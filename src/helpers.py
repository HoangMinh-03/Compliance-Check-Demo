import re
from datetime import datetime

def check_not_empty(value):
    if value and value.strip():
        return True, ""
    return False, "Trường dữ liệu không được để trống"

def check_numeric(value):
    try:
        float(value)
        return True, ""
    except (ValueError, TypeError):
        return False, f"'{value}' không phải là số"

def check_range(value, min_val, max_val):
    is_num, msg = check_numeric(value)
    if not is_num:
        return False, msg
    val = float(value)
    if min_val <= val <= max_val:
        return True, ""
    return False, f"Giá trị {val} nằm ngoài khoảng {min_val} đến {max_val}"

def check_date_format(value, date_format="%d-%m-%Y"):
    try:
        datetime.strptime(value, date_format)
        return True, ""
    except (ValueError, TypeError):
        return False, f"'{value}' không đúng định dạng {date_format}"

def check_alphabetical(value):
    # Vietnamese characters support
    # Added common Vietnamese accented characters
    if re.match(r"^[a-zA-Z\sÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂÂÊÔƠƯưăâêôơư]+$", value):
        return True, ""
    return False, f"'{value}' chứa ký tự không phải chữ cái"
