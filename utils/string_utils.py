import re

def remove_special_chars(req_str):
    return re.sub(r'[^\w\s]', '', req_str)

def remove_multi_space_chars(req_str):
    return re.sub(r'\s+', ' ', req_str).strip()
