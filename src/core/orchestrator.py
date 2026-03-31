import re
import logging
import ast
import inspect
from typing import Dict, List, Tuple, Any, Optional
from src.core.helpers import registry

logger = logging.getLogger(__name__)

def split_args(args_str: str) -> List[str]:
    args = []
    current_arg = []
    paren_depth = 0
    for char in args_str:
        if char == ',' and paren_depth == 0:
            args.append("".join(current_arg).strip())
            current_arg = []
        else:
            if char == '(': paren_depth += 1
            elif char == ')': paren_depth -= 1
            current_arg.append(char)
    if current_arg: args.append("".join(current_arg).strip())
    return args

def resolve_arg(arg: Any, data_dict: Dict[str, str]) -> Any:
    if isinstance(arg, dict):
        if arg.get("type") == "expression" or "value" in arg:
            arg = arg.get("value")
        else:
            return arg
            
    if not isinstance(arg, str): return arg
    arg_stripped = arg.strip()
    
    match = re.match(r"^(\w+)\((.*)\)$", arg_stripped)
    if match:
        func_name = match.group(1)
        inner_args_str = match.group(2)
        helper_func = registry.get_helper(func_name)
        if helper_func:
            inner_args = [resolve_arg(a, data_dict) for a in split_args(inner_args_str)]
            result = helper_func(*inner_args)
            if isinstance(result, tuple) and len(result) == 2: return result[0] 
            return result
            
    if arg_stripped in data_dict: return data_dict[arg_stripped]
    
    if arg_stripped == "current_date":
        from datetime import datetime
        return datetime.now().strftime("%d-%m-%Y")
        
    try: return ast.literal_eval(arg_stripped)
    except: pass
    
    return arg_stripped

def parse_rule_string(rule_str: str) -> Optional[Dict[str, Any]]:
    rule_str = rule_str.strip()
    match = re.match(r"^(\w+)(\((.*)\))?$", rule_str)
    if not match: return None
    func_name = match.group(1)
    args_str = match.group(3) or ""
    args = []
    if args_str:
        for p in split_args(args_str):
            try: args.append(ast.literal_eval(p))
            except: args.append(p)
    return {"function": func_name, "args": args}

def run_compliance_check(data_dict: Dict[str, str], rule_map: Any) -> Tuple[bool, List[str]]:
    all_pass = True
    results = []

    if isinstance(rule_map, dict) and "execution_plan" in rule_map:
        rule_map = rule_map["execution_plan"]

    normalized_rules: Dict[str, List[Any]] = {}
    if isinstance(rule_map, list):
        for item in rule_map:
            field = item.get("field")
            rules = item.get("rules", [])
            if field: normalized_rules[field] = rules
    elif isinstance(rule_map, dict):
        normalized_rules = rule_map
    else:
        return False, ["ERROR: Định dạng Execution Plan không hợp lệ."]

    for field, rules in normalized_rules.items():
        actual_field = field
        if field not in data_dict:
            found = False
            for f in data_dict.keys():
                if f.lower() == field.lower():
                    actual_field = f
                    found = True
                    break
            if not found:
                results.append(f"MISSING_FIELD: '{field}'")
                all_pass = False
                continue
                
        value = data_dict[actual_field]
        for rule_item in rules:
            rule_obj = rule_item
            if isinstance(rule_item, str):
                parsed = parse_rule_string(rule_item)
                if parsed: rule_obj = parsed
                else:
                    results.append(f"PARSE_ERROR: '{rule_item}'")
                    all_pass = False
                    continue
            
            func_name = rule_obj.get("function") or rule_obj.get("helper")
            args = rule_obj.get("args", [])
            helper_func = registry.get_helper(func_name)
            
            if not helper_func:
                results.append(f"UNKNOWN_HELPER: '{func_name}'")
                all_pass = False
                continue
                
            try:
                resolved_args = [resolve_arg(a, data_dict) for a in args]
                
                # THÔNG MINH: Kiểm tra chữ ký hàm để quyết định có chèn 'value' hay không
                sig = inspect.signature(helper_func)
                params = list(sig.parameters.values())
                
                # Nếu LLM cung cấp ít đối số hơn tổng số tham số mà hàm có thể nhận,
                # ta tự động chèn 'value' vào đầu (áp dụng cho cả validation và logic check).
                if len(resolved_args) < len(params):
                    resolved_args.insert(0, value)
                
                # Thực thi hàm với danh sách đối số đã chuẩn hóa
                is_valid, error_msg = helper_func(*resolved_args)
                    
                if not is_valid:
                    results.append(f"INVALID: '{field}' failed '{func_name}'. {error_msg}")
                    all_pass = False
            except Exception as e:
                logger.exception(f"Error {func_name} on {field}")
                results.append(f"EXECUTION_ERROR: {func_name} on '{field}': {e}")
                all_pass = False
                
    return all_pass, results
