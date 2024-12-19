# from playwright.async_api import async_playwright
import configparser
import time

from playwright.sync_api import sync_playwright
from utils import data_utils, string_utils
import json

config = configparser.ConfigParser()
# 'utf-8' 인코딩으로 파일 읽기
config.read('../config/config.ini', encoding='utf-8')

# read section
path_props = config['PATH']
keyword_props = config['KEYWORD']
xpath_props = config['XPATH']
etc_props = config['ETC']

chromium_path = path_props['chromium_path']


# scrape 시작
def main(search_keyword: str) -> list:
    with sync_playwright() as p:
        # 브라우저(Chromium) 열기
        browser = p.chromium.launch(headless=False, executable_path=chromium_path, args=["--start-maximized"])
        # browser = p.chromium.launch(headless=False, executable_path=chromium_path)
        # create a new incognito browser context.
        context = browser.new_context(no_viewport=True)
        # create a new page in a pristine context.
        page = context.new_page()

        # 웹 페이지 열기
        # page.goto('https://www.google.com/maps/@32.9817464,70.1930781,3.67z?', timeout=60000)
        page.goto('https://www.google.com/maps/', timeout=60000)
        page.wait_for_timeout(1000)

        page.locator('//input[@id="searchboxinput"]').fill(search_keyword.strip())
        page.keyboard.press("Enter")

        page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')

        page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

        # last keyword
        last_item_text = keyword_props['last_item_text']

        timeout = int(etc_props['timout_sec'])  # 초 단위로 설정
        start_time = time.time()  # 현재 시간을 기록

        total_listings = []
        previous_list_size = 0
        while True:
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(1500)
            # page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')

            list_size = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()

            # 새로운 항목이 있을 경우만 처리
            if list_size > previous_list_size:
                new_listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[
                               previous_list_size:list_size]
                new_listings = [listing.locator("xpath=..") for listing in new_listings]

                # 누적 리스트에 추가
                total_listings.extend(new_listings)
                print(f"새로운 항목 발견: {list_size - previous_list_size}개 추가")
                print(f"Total Found: {len(total_listings)}")  # 누적된 리스트 개수 출력

                # 타임아웃 초기화
                start_time = time.time()

                # 이전 리스트 크기 업데이트
                previous_list_size = list_size

            # if found last text break
            if page.locator(f"//span[normalize-space(text())='{last_item_text}']").count() > 0:
                if page.is_visible(f"//span[normalize-space(text())='{last_item_text}']"):
                    break

            # 타임아웃 확인 - 무한 로딩인 경우가 많음
            elapsed_time = time.time() - start_time  # 경과 시간 계산
            if elapsed_time > timeout:
                print("리스트 로딩 타임아웃 경과")
                break
        # .end while

        # list loop
        data_results = []
        for listing in total_listings:

            listing.click()
            page.wait_for_timeout(2000)

            try:
                page.wait_for_selector(xpath_props['name_xpath'], timeout=60000, state='attached')
                print("store page loaded")
            except Exception as e:
                print(e)
                print("store page not loaded")
                continue

            page.wait_for_timeout(3000)

            # name
            try:
                if page.locator(xpath_props['name_xpath']).count() > 0:
                    name = page.locator(xpath_props['name_xpath']).inner_text()
                else:
                    continue  # name은 없으면 continue..
            except Exception as e:
                print(e)
                continue

            # review count
            try:
                if page.locator(xpath_props['reviews_count_xpath']).count() > 0:
                    temp = page.locator(xpath_props['reviews_count_xpath']).inner_text()
                    temp = temp.replace('(', '').replace(')', '').replace(',', '')
                    review_count = int(temp)
                else:
                    review_count = None
            except Exception as e:
                print(e)
                review_count = None

            # review_average
            try:
                if page.locator(xpath_props['reviews_average_xpath']).count() > 0:
                    temp = page.locator(xpath_props['reviews_average_xpath']).inner_text()
                    temp = temp.replace(' ', '').replace(',', '.')
                    review_average = float(temp)
                else:
                    review_average = None
            except Exception as e:
                print(e)
                review_average = None

            # infos
            infos = []
            try:
                if page.locator(xpath_props['infos_xpath']).count() > 0:
                    infos_els = page.locator(xpath_props['infos_xpath']).all()
                    for info in infos_els:
                        temp = info.inner_text()
                        cleaned_temp = string_utils.remove_special_chars(temp)
                        cleaned_temp = string_utils.remove_multi_space_chars(cleaned_temp)
                        infos.append(cleaned_temp)
            except Exception as e:
                print(e)

            # opens_at
            try:
                if page.locator(xpath_props['opens_at_xpath']).count() > 0:
                    opens = page.locator(xpath_props['opens_at_xpath']).inner_text()
                    opens = opens.split('⋅')

                    if len(opens) != 1:
                        opens = opens[1]

                    else:
                        opens = page.locator(xpath_props['opens_at_xpath']).inner_text()
                        # print(opens)
                    opens = opens.replace("\u202f", "")
                    opens_at = opens.strip()
                else:
                    opens_at = ""

                if page.locator(xpath_props['opens_at_xpath2']).count() > 0:

                    try:
                        opens = page.locator(xpath_props['opens_at_xpath2']).inner_text()
                        opens = opens.split('⋅')
                        opens = opens[1]
                        opens = opens.replace("\u202f", "")
                        opens_at = opens.strip()
                    except Exception as e:
                        opens_at = None
            except Exception as e:
                print(e)
                opens_at = None

            # address
            try:
                address = data_utils.extract_data(xpath_props['address_xpath'], page)
            except Exception as e:
                print(e)
                address = None

            # website
            try:
                website = data_utils.extract_data(xpath_props['website_xpath'], page)
            except Exception as e:
                print(e)
                website = None

            # phone_number
            try:
                phone = data_utils.extract_data(xpath_props['phone_number_xpath'], page)
            except Exception as e:
                print(e)
                phone = None

            # place_type
            try:
                place_type = data_utils.extract_data(xpath_props['place_type_xpath'], page)
            except Exception as e:
                print(e)
                place_type = None

            # TODO review info
            if review_count is not None:
                # page.reload()
                page.locator(xpath_props['review_btn_xpath']).click()

                page.wait_for_selector(xpath_props['data_review_part_xpath'])

                total_review_listings = []
                previous_list_size = 0
                while True:
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(1500)

                    list_size = page.locator(xpath_props['data_review_part_xpath']).count()

                    #
                    # # 새로운 항목이 있을 경우만 처리
                    # if list_size > previous_list_size:
                    #     new_listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[
                    #                    previous_list_size:list_size]
                    #     new_listings = [listing.locator("xpath=..") for listing in new_listings]
                    #
                    #     # 누적 리스트에 추가
                    #     total_listings.extend(new_listings)
                    #     print(f"새로운 항목 발견: {list_size - previous_list_size}개 추가")
                    #     print(f"Total Found: {len(total_listings)}")  # 누적된 리스트 개수 출력
                    #
                    #     # 타임아웃 초기화
                    #     start_time = time.time()
                    #
                    #     # 이전 리스트 크기 업데이트
                    #     previous_list_size = list_size
                    #
                    # # if found last text break
                    # if page.locator(f"//span[normalize-space(text())='{last_item_text}']").count() > 0:
                    #     if page.is_visible(f"//span[normalize-space(text())='{last_item_text}']"):
                    #         break
                    #
                    # # 타임아웃 확인 - 무한 로딩인 경우가 많음
                    # elapsed_time = time.time() - start_time  # 경과 시간 계산
                    # if elapsed_time > timeout:
                    #     print("리스트 로딩 타임아웃 경과")
                    #     break


                    if len(total_review_listings) >= review_count:
                        break






            parse_result = {
                'name': name,
                'review_count': review_count,
                'review_average': review_average,
                'infos': infos,
                'opens_at': opens_at,
                'address': address,
                'website': website,
                'phone': phone,
                'place_type': place_type,
            }

            data_results.append(parse_result)
            print("parse_result: ", parse_result)

        print("end processing data")

        context.close()
        browser.close()
        return data_utils.remove_duplicate_list(data_results)


if __name__ == "__main__":
    search_keywords: list[str] = ["대야미역", "호계동 헬스", "Turkish Restaurants in Toronto Canada"]

    data_results = main(search_keywords[0])
    json_data = json.dumps(data_results, ensure_ascii=False, indent=4)  #

    print("end process")
