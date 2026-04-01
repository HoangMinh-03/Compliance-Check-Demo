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
    in_quote = None  # Theo dõi xem đang ở trong nháy đơn hay kép
    
    for char in args_str:
        # Xử lý dấu nháy
        if char in ["'", '"']:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
            current_arg.append(char)
        # Chỉ tách bằng dấu phẩy nếu không ở trong nháy VÀ không ở trong ngoặc lồng
        elif char == ',' and paren_depth == 0 and in_quote is None:
            args.append("".join(current_arg).strip())
            current_arg = []
        else:
            if char == '(': paren_depth += 1
            elif char == ')': paren_depth -= 1
            current_arg.append(char)
            
    if current_arg: 
        args.append("".join(current_arg).strip())
    return args

def resolve_arg(arg: Any, data_dict: Dict[str, str], mapping: Optional[Dict[str, str]] = None, current_value: Any = None) -> Any:
    if isinstance(arg, dict):
        if arg.get("type") == "expression" or "value" in arg:
            arg = arg.get("value")
        else:
            return arg
            
    if not isinstance(arg, str): return arg
    arg_stripped = arg.strip()
    
    # Handle recursive function calls in expressions (supports unicode)
    match = re.match(r"^([a-zA-Z0-9_À-ỹ]+)\((.*)\)$", arg_stripped)
    if match:
        func_name = match.group(1)
        inner_args_str = match.group(2)
        helper_func = registry.get_helper(func_name)
        if helper_func:
            inner_args = [resolve_arg(a, data_dict, mapping, current_value) for a in split_args(inner_args_str)]
            
            # THÔNG MINH: Chỉ chèn current_value nếu số lượng đối số cung cấp 
            # ít hơn số lượng tham số BẮT BUỘC (không có mặc định) của hàm.
            sig = inspect.signature(helper_func)
            required_params = [p for p in sig.parameters.values() if p.default is p.empty and p.kind != p.VAR_POSITIONAL and p.kind != p.VAR_KEYWORD]
            
            if len(inner_args) < len(required_params) and current_value is not None:
                inner_args.insert(0, current_value)
                
            result = helper_func(*inner_args)
            if isinstance(result, tuple) and len(result) == 2: return result[0] 
            return result
            
    # NEW: If arg is just a helper name (no parens), and we have current_value, try executing it
    if not "(" in arg_stripped and not ")" in arg_stripped:
        helper_func = registry.get_helper(arg_stripped)
        if helper_func and current_value is not None:
            result = helper_func(current_value)
            return result

    # NEW: Try resolving through mapping first (Rule Space -> Data Space)
    if mapping and arg_stripped in mapping and mapping[arg_stripped]:
        mapped_field = mapping[arg_stripped]
        if mapped_field in data_dict:
            return data_dict[mapped_field]

    # Try resolving directly from data_dict (Data Space)
    if arg_stripped in data_dict: 
        val = data_dict[arg_stripped]
        return val
    
    # Robust matching: Try stripping and case-insensitive
    target = arg_stripped.strip().lower()
    for f, v in data_dict.items():
        if f.strip().lower() == target:
            return v
    
    if arg_stripped == "current_date":
        from datetime import datetime
        return datetime.now().strftime("%d-%m-%Y")
        
    try: 
        val = ast.literal_eval(arg_stripped)
        return val
    except: pass
    
    return arg_stripped

def parse_rule_string(rule_str: str) -> Optional[Dict[str, Any]]:
    rule_str = rule_str.strip()
    # Support unicode in function names
    match = re.match(r"^([a-zA-Z0-9_À-ỹ]+)(\((.*)\))?$", rule_str)
    if not match: return None
    func_name = match.group(1)
    
    # Robust argument extraction: find the content of the outermost parentheses
    args_str = ""
    if "(" in rule_str:
        start = rule_str.find("(") + 1
        end = rule_str.rfind(")")
        args_str = rule_str[start:end]
        
    args = []
    if args_str:
        for p in split_args(args_str):
            p_stripped = p.strip()
            try: 
                # If it's a quoted string, use literal_eval
                if (p_stripped.startswith("'") and p_stripped.endswith("'")) or \
                   (p_stripped.startswith('"') and p_stripped.endswith('"')):
                    args.append(ast.literal_eval(p_stripped))
                else:
                    # Keep as string for resolve_arg to handle (field names, nested calls)
                    args.append(p_stripped)
            except: 
                args.append(p_stripped)
    return {"function": func_name, "args": args}

def run_compliance_check(data_dict: Dict[str, str], rule_map: Any, mapping: Optional[Dict[str, str]] = None) -> Tuple[bool, List[str]]:
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
        # Resolve actual field name using mapping
        # Ensure mapping_value is stripped of whitespace
        mapping_value = mapping.get(field, field) if mapping else field
        if isinstance(mapping_value, str): mapping_value = mapping_value.strip()
        
        # Check if mapping_value is a function call or expression
        if mapping_value and "(" in mapping_value and ")" in mapping_value:
            try:
                value = resolve_arg(mapping_value, data_dict, mapping)
            except Exception as e:
                results.append(f"CALCULATION_ERROR: Lỗi tính toán trường '{field}' từ biểu thức '{mapping_value}': {e}")
                all_pass = False
                continue
        else:
            actual_field = mapping_value if mapping_value else field
            
            # Robust matching: Direct check first
            if actual_field not in data_dict:
                # Try stripping and case-insensitive
                found = False
                target = actual_field.strip().lower()
                for f in data_dict.keys():
                    if f.strip().lower() == target:
                        actual_field = f
                        found = True
                        break
                
                if not found:
                    results.append(f"MISSING_FIELD: '{actual_field}' (mapped from '{field}')" if mapping and field in mapping else f"MISSING_FIELD: '{field}'")
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
                resolved_args = [resolve_arg(a, data_dict, mapping, current_value=value) for a in args]
                
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
