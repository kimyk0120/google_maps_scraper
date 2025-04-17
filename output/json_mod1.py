# json 파일의 객체들을 한 json 파일로 모은다.

import glob
import json
import re


def remove_extra_text(price_str):
    return price_str.replace("(세금 및 수수료 포함)", "").strip()


def convert_to_krw(amount_str, exchange_rate=1000):
    # 금액 정보에서 숫자 추출 (CA$를 제거)
    match = re.search(r"CA\$(\d+)", amount_str)
    if match:
        cad_amount = int(match.group(1))  # CAD 금액
    else:
        raise ValueError("유효한 금액 정보가 포함되어 있지 않습니다.")

    # CAD를 KRW로 변환
    krw_amount = cad_amount * exchange_rate

    # 변환된 정보를 포함한 새로운 문자열 반환
    return krw_amount


def process_and_sort_prices(json_data_list):
    def convert_to_krw(price_txt, exchange_rate=1000):
        import re
        match = re.search(r"CA\$(\d+)", price_txt)
        if match:
            cad_amount = int(match.group(1))
            return cad_amount * exchange_rate
        raise ValueError(f"Invalid price format: {price_txt}")


json_ori = 'output_total.json'
with open(json_ori, 'r', encoding='utf-8') as f:
    json_data_list = json.load(f)

    # price를 객체로 만들고 오름차순 정렬

    for json_data in json_data_list:
        print(f'json data : {json_data["name"]}')

        price_infos = json_data['price_infos']
        processed_data = []
        for price_info in price_infos:

            site_name = price_info[0]
            price_txt = price_info[-1]

            try:
                price_krw = convert_to_krw(price_txt)
                price_obj = {'site_name': site_name, 'price_krw': price_krw, 'ori_ca_price': remove_extra_text(price_txt)}
                processed_data.append(price_obj)
            except ValueError as e:
                print(f"Error converting price: {e}")

        # 가격을 기준으로 오름차순 정렬
        processed_data_sorted = sorted(processed_data, key=lambda x: x['price_krw'])

        json_data['price_infos'] = processed_data_sorted

    # json 파일로 쓰기
    with open('./output_total_250417.json', 'w', encoding='utf-8') as f:
        json.dump(json_data_list, f, ensure_ascii=False, indent=4)

print("fin")
