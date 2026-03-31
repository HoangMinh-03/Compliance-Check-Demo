import re
import inspect
from datetime import datetime
from typing import Tuple, Union, Any, List, Dict, Callable

class HelperRegistry:
    def __init__(self):
        self.helpers: Dict[str, Callable] = {}
        self.pure_helpers: List[str] = []
        self.metadata: Dict[str, str] = {}

    def register(self, is_pure: bool = False, description: str = ""):
        def decorator(func: Callable):
            name = func.__name__
            self.helpers[name] = func
            self.metadata[name] = description
            if is_pure:
                self.pure_helpers.append(name)
            return func
        return decorator

    def get_helper(self, name: str) -> Callable:
        return self.helpers.get(name)

    def is_pure(self, name: str) -> bool:
        return name in self.pure_helpers

    def get_llm_metadata(self) -> str:
        lines = []
        for name, func in self.helpers.items():
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            
            # Ẩn tham số 'value' đầu tiên cho các hàm validation thông thường
            if not self.is_pure(name) and len(params) > 0:
                # Tạo signature hiển thị không bao gồm tham số đầu tiên (value)
                display_params = params[1:]
                display_sig = "(" + ", ".join(str(p) for p in display_params) + ")"
            else:
                display_sig = str(sig)
                
            desc = self.metadata.get(name, "")
            lines.append(f"- {name}{display_sig}: {desc}")
        return "\n".join(lines)

registry = HelperRegistry()

def _parse_value(val: Any) -> float:
    if val is None:
        raise ValueError("Giá trị là None")
    s_val = str(val).strip()
    if s_val.endswith('%'):
        return float(s_val.replace('%', '').strip()) / 100.0
    if '%' in s_val:
        return float(s_val.replace('%', '').strip()) / 100.0
    return float(s_val)

@registry.register(description="Kiểm tra trường dữ liệu không được để trống.")
def check_not_empty(value: str) -> Tuple[bool, str]:
    if value and str(value).strip():
        return True, ""
    return False, "Trường dữ liệu không được để trống"

@registry.register(description="Kiểm tra giá trị phải là số (hỗ trợ cả định dạng %)")
def check_numeric(value: str) -> Tuple[bool, str]:
    try:
        _parse_value(value)
        return True, ""
    except (ValueError, TypeError):
        return False, f"'{value}' không phải là số"

@registry.register(description="Kiểm tra số nằm trong khoảng (min_val, max_val).")
def check_range(value: str, min_val: Any, max_val: Any) -> Tuple[bool, str]:
    try:
        val = _parse_value(value)
        f_min = _parse_value(min_val)
        f_max = _parse_value(max_val)
        if f_min <= val <= f_max:
            return True, ""
        return False, f"Giá trị {value} nằm ngoài khoảng {min_val} đến {max_val}"
    except (ValueError, TypeError):
        return False, f"Không thể thực hiện so sánh khoảng cho giá trị '{value}'"

@registry.register(description="Kiểm tra định dạng ngày (mặc định %d-%m-%Y).")
def check_date_format(value: str, date_format: str = "%d-%m-%Y") -> Tuple[bool, str]:
    try:
        clean_format = str(date_format).replace('format=', '').strip('"\'')
        datetime.strptime(str(value), clean_format)
        return True, ""
    except (ValueError, TypeError):
        return False, f"'{value}' không đúng định dạng {date_format}"

@registry.register(description="Kiểm tra chỉ chứa chữ cái tiếng Việt và khoảng trắng.")
def check_alphabetical(value: str) -> Tuple[bool, str]:
    vietnamese_pattern = r"^[a-zA-Z\sÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂÂÊÔƠƯưăâêôơưẠ-ỹ]+$"
    if re.match(vietnamese_pattern, str(value), re.UNICODE):
        return True, ""
    return False, f"'{value}' chứa ký tự không phải chữ cái"

@registry.register(description="Kiểm tra độ dài chuỗi nằm trong khoảng (min_len, max_len).")
def check_length(value: str, min_len: int, max_len: int) -> Tuple[bool, str]:
    length = len(str(value))
    if int(min_len) <= length <= int(max_len):
        return True, ""
    return False, f"Độ dài {length} nằm ngoài khoảng {min_len} đến {max_len}"

@registry.register(description="Kiểm tra giá trị khớp với biểu thức chính quy (Regex).")
def check_regex(value: str, pattern: str) -> Tuple[bool, str]:
    if re.match(str(pattern), str(value)):
        return True, ""
    return False, f"Giá trị '{value}' không khớp với định dạng yêu cầu"

@registry.register(description="Kiểm tra định dạng Email.")
def check_email(value: str) -> Tuple[bool, str]:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if re.match(pattern, str(value)):
        return True, ""
    return False, f"'{value}' không phải là Email hợp lệ"

@registry.register(description="Kiểm tra số thẻ Visa (bắt đầu bằng 4, dài 13 hoặc 16 số).")
def check_visa(value: str) -> Tuple[bool, str]:
    # Loại bỏ khoảng trắng hoặc dấu gạch ngang
    clean_val = re.sub(r"[\s-]", "", str(value))
    pattern = r"^4[0-9]{12}(?:[0-9]{3})?$"
    if re.match(pattern, clean_val):
        return True, ""
    return False, f"'{value}' không phải là số thẻ Visa hợp lệ"

@registry.register(description="Kiểm tra số thẻ Mastercard.")
def check_mastercard(value: str) -> Tuple[bool, str]:
    clean_val = re.sub(r"[\s-]", "", str(value))
    # Mastercard: 51-55 hoặc 2221-2720, dài 16 số
    pattern = r"^(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}$"
    if re.match(pattern, clean_val):
        return True, ""
    return False, f"'{value}' không phải là số thẻ Mastercard hợp lệ"

@registry.register(description="Kiểm tra mã SWIFT/BIC (8 hoặc 11 ký tự).")
def check_swift_bic(value: str) -> Tuple[bool, str]:
    pattern = r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$"
    if re.match(pattern, str(value).upper()):
        return True, ""
    return False, f"'{value}' không phải là mã SWIFT/BIC hợp lệ"

@registry.register(description="Kiểm tra định dạng tiền tệ (VD: $1,000.00 hoặc 1.000 VND).")
def check_currency_format(value: str) -> Tuple[bool, str]:
    # Hỗ trợ nhiều định dạng: $1,000.00, 1.000.000 VND, 500,000đ
    pattern = r"^([\$€£¥]?\s*\d{1,3}([,.]\d{3})*([,.]\d+)?\s*([vV][nN][dD]|đ|[\$€£¥])?)$"
    if re.match(pattern, str(value).strip()):
        return True, ""
    return False, f"'{value}' không đúng định dạng tiền tệ"

@registry.register(is_pure=True, description="Thực hiện kiểm tra nếu điều kiện đúng. check_if(condition, helper_result)")
def check_if(condition: Any, helper_result: Any) -> Tuple[bool, str]:
    """
    Nếu condition là True, trả về kết quả của helper_result.
    Nếu condition là False, trả về (True, '').
    """
    # Nếu condition là một tuple (bool, str), lấy phần tử đầu tiên
    cond = condition[0] if isinstance(condition, tuple) and len(condition) == 2 else condition
    
    if cond:
        if isinstance(helper_result, tuple) and len(helper_result) == 2:
            return helper_result
        return True, ""
    return True, ""

@registry.register(is_pure=True, description="Lấy năm hiện tại.")
def get_current_year() -> int:
    return datetime.now().year

@registry.register(is_pure=True, description="Lấy ngày hiện tại (định dạng %d-%m-%Y).")
def get_current_date() -> str:
    return datetime.now().strftime("%d-%m-%Y")

@registry.register(is_pure=True, description="Trích xuất năm từ chuỗi ngày tháng.")
def extract_year(date_string: str, date_format: str = "%d-%m-%Y") -> int:
    try:
        clean_format = str(date_format).replace('format=', '').strip('"\'')
        dt = datetime.strptime(str(date_string), clean_format)
        return dt.year
    except (ValueError, TypeError):
        return 0

@registry.register(is_pure=True, description="Tính tuổi dựa trên năm sinh hoặc chuỗi ngày tháng.")
def calculate_age(birth_year: Union[int, str]) -> int:
    try:
        b_year = str(birth_year)
        if '-' in b_year or '/' in b_year:
            for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"]:
                try:
                    return datetime.now().year - datetime.strptime(b_year, fmt).year
                except:
                    continue
        return get_current_year() - int(float(b_year))
    except (ValueError, TypeError):
        return -1

@registry.register(is_pure=True, description="So sánh bằng giữa hai giá trị (hỗ trợ %).")
def check_logic_equal(val1: Any, val2: Any) -> Tuple[bool, str]:
    try:
        v1 = _parse_value(val1)
        v2 = _parse_value(val2)
        if abs(v1 - v2) < 1e-9:
            return True, ""
        return False, f"Giá trị '{val1}' không khớp với '{val2}'"
    except (ValueError, TypeError):
        return False, f"Không thể so sánh bằng giữa '{val1}' và '{val2}'"

@registry.register(is_pure=True, description="Kiểm tra giá trị 1 lớn hơn giá trị 2.")
def check_logic_greater(val1: Any, val2: Any) -> Tuple[bool, str]:
    try:
        v1 = _parse_value(val1)
        v2 = _parse_value(val2)
        if v1 > v2:
            return True, ""
        return False, f"Giá trị '{val1}' không lớn hơn '{val2}'"
    except (ValueError, TypeError):
        return False, f"Không thể so sánh lớn hơn giữa '{val1}' và '{val2}'"
    
@registry.register(is_pure=True, description="Kiểm tra giá trị 1 nhỏ hơn giá trị 2.")
def check_logic_smaller(val1: Any, val2: Any) -> Tuple[bool, str]:
    try:
        v1 = _parse_value(val1)
        v2 = _parse_value(val2)
        if v1 < v2:
            return True, ""
        return False, f"Giá trị '{val1}' không nhỏ hơn '{val2}'"
    except (ValueError, TypeError):
        return False, f"Không thể so sánh nhỏ hơn giữa '{val1}' và '{val2}'"

@registry.register(description="Kiểm tra ngày 1 phải TRƯỚC ngày 2.")
def check_date_before(date1: str, date2: str, date_format: str = "%d-%m-%Y") -> Tuple[bool, str]:
    try:
        clean_format = str(date_format).replace('format=', '').strip('"\'')
        d1 = datetime.strptime(str(date1), clean_format)
        d2 = datetime.strptime(str(date2), clean_format)
        if d1 < d2:
            return True, ""
        return False, f"Ngày '{date1}' không trước ngày '{date2}'"
    except (ValueError, TypeError):
        return False, f"Lỗi định dạng ngày khi so sánh '{date1}' và '{date2}'"

@registry.register(description="Kiểm tra ngày 1 phải SAU ngày 2.")
def check_date_after(date1: str, date2: str, date_format: str = "%d-%m-%Y") -> Tuple[bool, str]:
    try:
        clean_format = str(date_format).replace('format=', '').strip('"\'')
        d1 = datetime.strptime(str(date1), clean_format)
        d2 = datetime.strptime(str(date2), clean_format)
        if d1 > d2:
            return True, ""
        return False, f"Ngày '{date1}' không sau ngày '{date2}'"
    except (ValueError, TypeError):
        return False, f"Lỗi định dạng ngày khi so sánh '{date1}' và '{date2}'"

@registry.register(description="Kiểm tra CCCD Việt Nam (12 số, đúng mã tỉnh).")
def check_cccd_vn(value: str) -> Tuple[bool, str]:
    # 12 chữ số
    val = str(value).strip()
    if not re.match(r"^\d{12}$", val):
        return False, "CCCD phải bao gồm chính xác 12 chữ số"
    
    # Mã tỉnh thành (3 số đầu): 001 -> 096
    # Danh sách mã tỉnh thực tế (có thể có một số số không dùng nhưng nằm trong dải 001-096)
    valid_provinces = {
        "001", "002", "004", "006", "008", "010", "011", "012", "014", "015", "017", "019", "020", "022", "024", "025", "026", "027", "030", "031", "033", "034", "035", "036", "037", "038", "040", "042", "044", "045", "046", "048", "049", "051", "052", "054", "056", "058", "060", "062", "064", "066", "067", "068", "070", "072", "074", "075", "077", "079", "080", "082", "083", "084", "086", "087", "089", "091", "092", "093", "094", "095", "096"
    }
    
    province_code = val[:3]
    if province_code not in valid_provinces:
        return False, f"Mã tỉnh '{province_code}' không hợp lệ trên CCCD"
        
    return True, ""
