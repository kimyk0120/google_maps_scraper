def extract_data(xpath, page):
    if page.locator(xpath).count() > 0:
        data = page.locator(xpath).inner_text()
    else:
        data = None
    return data


def remove_duplicate_list(req_list, tg_key="name"):
    seen_names = set()
    filtered_results = []
    for item in req_list:
        if item[tg_key] not in seen_names:
            seen_names.add(item[tg_key])
            filtered_results.append(item)
    return filtered_results
