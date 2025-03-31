# from playwright.async_api import async_playwright
import configparser
import logging
import os
import time
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright

from utils import data_utils, string_utils
from logging.handlers import TimedRotatingFileHandler
import sys

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 콘솔 출력 핸들러 (IDE 콘솔에 기록)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
# console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

# 파일 출력 핸들러 (로그 파일에 기록)
file_handler = TimedRotatingFileHandler(
    filename='./log/log.log',
    when='midnight',
    interval=1,
    backupCount=10
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

# 로거에 핸들러 추가
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# print를 로그로 리다이렉션
class PrintLogger:
    def write(self, message):
        if message.strip():  # 공백 메시지 제외
            logging.info(message)

    def flush(self):
        pass  # 표준 출력에서는 필요. 여기서는 로그만 기록하므로 비워둠.


# sys.stdout과 sys.stderr를 리다이렉션
sys.stdout = PrintLogger()
sys.stderr = PrintLogger()

# 테스트 로그
logger.info("This is a log message")

# config
config = configparser.ConfigParser()
# 'utf-8' 인코딩으로 파일 읽기
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, '../config/config.ini')
config.read(config_path, encoding='utf-8')

# read section
path_props = config['PATH']
keyword_props = config['KEYWORD']
xpath_props = config['XPATH']
conf_props = config['CONFIG']
proxy_props = config['PROXY']

chromium_path = path_props['chromium_path']


# scrape 시작
def main(search_keyword: str, headlsee=True) -> list:
    with sync_playwright() as p:

        # launch 옵션 설정
        launch_options = {
            "headless": headlsee,
            "args": ["--start-maximized"]
        }

        # chromium_path가 있는 경우에만 launch_options에 추가
        if chromium_path:
            launch_options["executable_path"] = chromium_path

        # proxy 설정 추가
        if proxy_props['proxy_server']:  # proxy_server가 비어 있지 않다면
            launch_options["proxy"] = {"server": proxy_props['proxy_server']}

        # 브라우저 열기
        browser = p.chromium.launch(**launch_options)

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

        timeout = int(conf_props['timout_sec'])  # 초 단위로 설정
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
                print("@@@@ 리스트 로딩 타입아웃 초기화")

                # 이전 리스트 크기 업데이트
                previous_list_size = list_size

            # if found last text break
            if page.locator(f"//span[normalize-space(text())='{last_item_text}']").count() > 0:
                if page.is_visible(f"//span[normalize-space(text())='{last_item_text}']"):
                    print("@@@@ last item found. break.")
                    break

            # 타임아웃 확인 - 무한 로딩인 경우가 많음
            elapsed_time = time.time() - start_time  # 경과 시간 계산
            if elapsed_time > timeout:
                print("@@@@ 리스트 로딩 타임아웃 경과")
                break

            # store limit cnt 넘었을때 break
            if len(total_listings) >= int(conf_props['store_limit_cnt']):
                print("@@@@ store limit 달성")
                total_listings = total_listings[:int(conf_props['store_limit_cnt'])]
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
                    print("store name : ", name)
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
            # get review list
            # review_results = []
            # if review_count:
            #     try:
            #         # page.reload()
            #         page.locator(xpath_props['review_btn_xpath']).click()
            #         page.wait_for_selector(xpath_props['data_review_part_xpath'])
            #
            #         # 초기화
            #         total_review_listings = []
            #         previous_list_size = 0
            #         timeout = int(conf_props['timout_sec'])  # 초 단위로 설정
            #         start_time = time.time()
            #
            #         print("리뷰 스크롤 시작...")
            #         # scroll to bottom for visible all reviews
            #         while True:
            #             page.mouse.wheel(0, 5000)
            #             page.wait_for_timeout(1500)
            #
            #             current_list_size = page.locator(xpath_props['data_review_part_xpath']).count()
            #             print(f"스크롤 중: 불러온 리뷰 수: {current_list_size}/{review_count}")
            #
            #             if current_list_size:
            #                 new_review_list = page.locator(xpath_props['data_review_part_xpath']).all()[
            #                                   previous_list_size:current_list_size]
            #
            #                 # 누적 리스트에 추가
            #                 total_review_listings.extend(new_review_list)
            #
            #             # 새로운 리뷰를 불러온 경우 타임아웃 초기화
            #             if current_list_size > previous_list_size:
            #                 start_time = time.time()
            #                 previous_list_size = current_list_size
            #                 print("새로운 리뷰 발견 - 타임아웃 초기화")
            #
            #             # 모든 리뷰를 불러왔거나, 리뷰 제한 수에 도달하면 종료
            #             if current_list_size >= review_count or current_list_size >= int(
            #                     conf_props['review_limit_cnt']):
            #                 print("모든 리뷰 or review limit 도달하여 로드 완료")
            #                 total_review_listings = total_review_listings[:int(
            #                     conf_props['review_limit_cnt'])]
            #                 break
            #
            #             # 타임아웃 처리 (지정된 시간 동안 새로운 리뷰가 없으면 종료)
            #             if time.time() - start_time > timeout:
            #                 print(f"리뷰 로드가 {timeout}초 이내 완료되지 않음 - 타임아웃 발생")
            #                 break
            #     except Exception as e:
            #         print("리뷰 데이터 가져오는 중 오류 발생")
            #         print(e)
            #
            #     for review_raw in total_review_listings:
            #         review_name = review_raw.locator(".jJc9Ad .GHT2ce.NsCY4 div.d4r55").inner_text().strip()
            #         print("review_name: ", review_name)
            #
            #         # 리뷰어 정보 없을 수 있음
            #         if review_raw.locator(".jJc9Ad .GHT2ce.NsCY4 div.RfnDt").count() > 0:
            #             review_info = review_raw.locator(".jJc9Ad .GHT2ce.NsCY4 div.RfnDt").inner_text().strip()
            #         else:
            #             review_info = None
            #
            #         # 리뷰 내용이 없을 수 있음
            #         if review_raw.locator(".jJc9Ad .GHT2ce .MyEned span.wiI7pd").count() > 0:
            #             review_content = review_raw.locator(
            #                 ".jJc9Ad .GHT2ce .MyEned span.wiI7pd").inner_text().strip().replace('\n', ' ')
            #         else:
            #             review_content = None
            #
            #         # 리뷰 별
            #         review_rate = review_raw.locator(".jJc9Ad .GHT2ce .kvMYJc span").count()
            #
            #         # 리뷰 작성후 지난 시간
            #         review_at = review_raw.locator(".jJc9Ad .GHT2ce .rsqaWe").inner_text().strip()
            #
            #         review_image_urls = []
            #         if review_raw.locator(".jJc9Ad .GHT2ce .KtCyie").count() > 0:
            #             url_img_buttons = review_raw.locator(".jJc9Ad .GHT2ce .KtCyie button").all()
            #             if url_img_buttons:
            #                 for url_img in url_img_buttons:
            #                     style_attribute = url_img.get_attribute("style")
            #                     url_match = re.search(r'url\("?(.*?)"?\)', style_attribute)
            #                     if url_match:
            #                         review_image_urls.append(url_match.group(1))
            #
            #         review_results.append({
            #             "review_name": review_name,
            #             "review_info": review_info,
            #             "review_content": review_content,
            #             "review_rate": review_rate,
            #             "review_image_urls": review_image_urls,
            #             'review_at': review_at
            #         })

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
                # 'reviews': review_results,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            data_results.append(parse_result)
            print("parse_result: ", parse_result)

        print("end processing data")

        context.close()
        browser.close()
        return data_utils.remove_duplicate_list(data_results)


if __name__ == "__main__":

    # search_keywords: list[str] = ["대야미역 헬스", "호계동 헬스", "Turkish Restaurants in Toronto Canada", "コインランドリ",
    #                               "北海道 コインランドリー"]

    # 읽어올 엑셀 파일 경로
    src_file_path = "cw_kr.xlsx"
    # 엑셀 파일 불러오기
    df = pd.read_excel(src_file_path)

    # 데이터 확인
    print(df.head())

    keyword_list = df.iloc[:, 5].tolist()

    # print(keyword_list)

    # CSV 파일 초기화
    output_file = f"../output/output.csv"

    # 첫 번째 시도 시 헤더를 포함해야 함
    is_first_iteration = True

    # n번째 인덱스를 제외한 나머지 리스트
    # keyword_list = keyword_list[1:]

    for skw in keyword_list:
        start_time = time.time()
        formatted_time = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')

        print(
            f" ############### keyword: {skw}, index: {keyword_list.index(skw)}, start_time: {formatted_time} ###############")

        data_results = main(skw, False)

        excel_data = []

        for result in data_results:
            name, address, scraped_at = result['name'], result['address'], result['scraped_at']
            excel_data.append({"scraped_at": scraped_at, "Keyword": skw, "Name": name, "Address": address})

        df = pd.DataFrame(excel_data)

        # 데이터를 CSV 파일로 저장
        df.to_csv(output_file, index=False, encoding="utf-8-sig", mode='a', header=is_first_iteration)

        # 헤더는 첫 번째 반복에서만 쓰고 이후에는 제외
        is_first_iteration = False

        end_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        elapsed_time = time.time() - start_time

        print(
            f"############### end keyword : {skw}, index: {keyword_list.index(skw)}, end_time: {end_time}, elapsed_time: {elapsed_time:.2f} sec  ###############")

    print("end process")
