import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from playwright.async_api import async_playwright
import configparser
import hashlib
import logging

import re

import time
from datetime import datetime

import requests
from playwright.sync_api import sync_playwright
from utils import data_utils
import json

from logging.handlers import TimedRotatingFileHandler

# 현재 파일의 경로를 기준으로 상위 디렉토리를 sys.path에 추가하여,
# 해당 디렉토리에 있는 모듈들을 import할 수 있도록 설정합니다.


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
# Custom logger class to redirect all print statements to the logging system.
class PrintLogger:
    def write(self, message):
        if message.strip():  # Ignore empty (whitespace-only) messages.
            logging.info(message)  # Redirect to the logging system.

    def flush(self):
        # The flush method is needed for compatibility with sys.stdout,
        # but it's not used here as logs don't require explicit flushing.
        pass


# sys.stdout과 sys.stderr를 리다이렉션
sys.stdout = PrintLogger()
sys.stderr = PrintLogger()

# 테스트 로그
logger.info("This is a log message")


# Convert a URL into a hashed filename to ensure it is safe for file systems and unique.
def convert_url_to_safe_file_name(url, extension=".jpg"):
    # Hash the URL using MD5 to create a unique, safe file name.
    hashed_name = hashlib.md5(url.encode("utf-8")).hexdigest()
    return f"{hashed_name}{extension}"


def split_translation(data):
    # 연속된 줄바꿈을 하나로 정리
    cleaned_data = re.sub(r'\n+', '\n', data).strip()

    # "(Google 번역)"과 "(원본)"을 기준으로 나눔
    parts = re.split(r'\((Google 번역|원본)\)', cleaned_data)

    # 결과 배열 생성
    result = []
    for i in range(1, len(parts), 2):  # 홀수 인덱스 = (Google 번역), (원본)
        label = parts[i]  # 라벨: Google 번역 또는 원본
        text = parts[i + 1].strip()  # 라벨에 해당하는 텍스트
        result.append(f"({label}) {text}")

    return result


# scrape 시작
def main(search_keyword: str, headlsee=True) -> list:
    with (sync_playwright() as p):

        # Configure browser launch options for the Playwright scraper
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
                print("Resetting timeout after discovering new listings.")

                # 이전 리스트 크기 업데이트
                previous_list_size = list_size

            # if found last text break
            if page.locator(f"//span[normalize-space(text())='{last_item_text}']").count() > 0:
                if page.is_visible(f"//span[normalize-space(text())='{last_item_text}']"):
                    print("last keyword found")
                    break

            # 타임아웃 확인 - 무한 로딩인 경우가 많음
            elapsed_time = time.time() - start_time  # 경과 시간 계산
            if elapsed_time > timeout:
                print("리스트 로딩 타임아웃 경과")
                break

            # store limit cnt 넘었을때 break
            if len(total_listings) >= int(conf_props['store_limit_cnt']):
                print("store limit 달성")
                total_listings = total_listings[:int(conf_props['store_limit_cnt'])]
                break

        # .end while


        # list loop
        # data_results = []
        # FIXME
        continu_num = 0
        total_listings = total_listings[continu_num:]
        for list_idx, listing in enumerate(total_listings):

            list_idx = list_idx + continu_num
            list_start_time = time.time()
            formatted_time = datetime.fromtimestamp(list_start_time).strftime('%Y-%m-%d %H:%M:%S')

            print(
                f" ############### list: {str(list_idx)}, start_time: {formatted_time} ###############")

            if listing.is_visible():
                listing.click()
                page.wait_for_timeout(2000)
            else:
                print("!! listing not visible")
                continue

            try:
                page.wait_for_selector(xpath_props['name_xpath'])
                print(f"@@@@ store page loaded : " + str(list_idx) + " / " + str(len(total_listings)+continu_num) + " @@@@")
            except Exception as e:
                print(e)
                print("!! store page not loaded")
                continue

            page.wait_for_timeout(3000)

            # name
            try:
                if page.locator(xpath_props['name_xpath']).count() > 0:
                    name = page.locator(xpath_props['name_xpath']).inner_text()
                    print("store name : " + str(name))
                else:
                    continue  # name은 없으면 continue..
            except Exception as e:
                print("!!", e)
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
                print("!!", e)
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
                print("!!", e)
                review_average = None

            # 좌표
            try:
                current_url = page.url
                # 정규식으로 좌표 추출
                match = re.search(r"3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", current_url)
                if match:
                    latitude = match.group(1)  # 위도
                    longitude = match.group(2)  # 경도
                    print(f"Latitude: {latitude}, Longitude: {longitude}")

            except Exception as e:
                print("!!", e)
                latitude = None
                longitude = None

            # address
            try:
                address = data_utils.extract_data(xpath_props['address_xpath'], page)
            except Exception as e:
                print("!!", e)
                address = None

            # website
            try:
                website = data_utils.extract_data(xpath_props['website_xpath'], page)
            except Exception as e:
                print("!!", e)
                website = None

            # phone_number
            try:
                phone = data_utils.extract_data(xpath_props['phone_number_xpath'], page)
            except Exception as e:
                print("!!", e)
                phone = None

            # 요금
            price_infos = []
            try:
                if page.locator('a.SlvSdc.co54Ed').count() > 0:
                    price_lows = page.locator('a.SlvSdc.co54Ed').all()
                    print('price low 리스트 수 : ' + str(len(price_lows)))

                    for price_low in price_lows:
                        price_info = price_low.inner_text()

                        price_info_list = price_info.split('\n')
                        price_info_list_cleaned = [re.sub(r'[\ue000-\uf8ff]', '', item).strip() for item in
                                                   price_info_list]

                        cleaned_list = [item for item in price_info_list_cleaned if item != ""]

                        price_infos.append(cleaned_list)

            except Exception as e:
                print("!!", e)

            # 뒤로가기
            # page.locator('button.iPpe6d[aria-label="뒤로"]').click()

            # 질문 응답
            qna_results = []
            try:
                if page.locator('//span[text()="질문 더보기"]').count() > 0:
                    page.locator('//span[text()="질문 더보기"]').click()  # headless 에서는 적용이 안된다...
                    page.wait_for_timeout(1000)

                    iframe = page.frame_locator('iframe.rvN3ke')
                    if iframe.locator('div[jscontroller="s2Fp0c"]').count() > 0:

                        # iframe 내부에서 작업 계속 진행
                        qna_list_div = iframe.locator('div[jscontroller="s2Fp0c"] > div').all()
                        print('qna 목록 수 : ' + str(len(qna_list_div)))

                        for qna_div in qna_list_div:
                            question = qna_div.locator('div.NXtIPd').nth(0).inner_text().strip()

                            # 뉴라인 분리 적용
                            qna_results_cleaned = split_translation(question)

                            answers_divs = qna_div.locator('div.V4O16c').all()
                            answers = []
                            for answer_div in answers_divs:
                                answer = answer_div.inner_text().strip()
                                answer_cleaned = split_translation(answer)
                                answers.append(answer_cleaned)

                            qna_results.append({'question': qna_results_cleaned, 'answers': answers})
                        print("qna 완")
                        page.wait_for_timeout(1000)
                    iframe.locator('button[data-tooltip-id="tt-i2"]').click()
            except Exception as e:
                print("!! qna err ", e)
                # iframe.locator('button[data-tooltip-id="tt-i2"]').click()

            # listing.click()
            # page.wait_for_timeout(500)
            # page.locator('button[data-tooltip-id="tt-i2"]').click()
            page.wait_for_timeout(1500)

            # get review list
            review_results = []
            review_err = False
            if review_count:
                try:
                    # page.reload()
                    page.wait_for_selector(xpath_props['review_btn_xpath_accom'])
                    page.wait_for_timeout(500)
                    page.locator(xpath_props['review_btn_xpath_accom']).click()
                    page.wait_for_timeout(2000)
                    page.wait_for_selector(xpath_props['data_review_part_xpath'])

                    # 초기화
                    total_review_listings = []
                    previous_list_size = 0
                    timeout = int(conf_props['timout_sec'])  # 초 단위로 설정
                    start_time = time.time()

                    print("리뷰 스크롤 시작...")
                    # scroll to bottom for visible all reviews
                    while True:
                        page.mouse.wheel(0, 5000)
                        page.wait_for_timeout(1500)

                        current_list_size = page.locator(xpath_props['data_review_part_xpath']).count()
                        print(f"스크롤 중: 불러온 리뷰 수: {current_list_size}/{review_count}")

                        if current_list_size:
                            new_review_list = page.locator(xpath_props['data_review_part_xpath']).all()[
                                              previous_list_size:current_list_size]

                            # 누적 리스트에 추가
                            total_review_listings.extend(new_review_list)

                        # 새로운 리뷰를 불러온 경우 타임아웃 초기화
                        if current_list_size > previous_list_size:
                            start_time = time.time()
                            previous_list_size = current_list_size
                            print("새로운 리뷰 발견 - 타임아웃 초기화")

                        # 모든 리뷰를 불러왔거나, 리뷰 제한 수에 도달하면 종료
                        if current_list_size >= review_count or current_list_size >= int(
                                conf_props['review_limit_cnt']):
                            print("모든 리뷰 or review limit 도달하여 로드 완료")
                            total_review_listings = total_review_listings[:int(
                                conf_props['review_limit_cnt'])]
                            break

                        # 타임아웃 처리 (지정된 시간 동안 새로운 리뷰가 없으면 종료)
                        if time.time() - start_time > timeout:
                            print(f"리뷰 로드가 {timeout}초 이내 완료되지 않음 - 타임아웃 발생")
                            break
                except Exception as e:
                    print("!! 리뷰 데이터 가져오는 중 오류 발생")
                    print(e)
                    review_err = True

                print('리뷰 데이터 파싱..')
                if not review_err:
                    for r_idx, review_raw in enumerate(total_review_listings):
                        review_name = review_raw.locator(".jJc9Ad .GHT2ce.NsCY4 div.d4r55").inner_text().strip()
                        # print("review_name: " + review_name)

                        # 리뷰어 정보 없을 수 있음
                        if review_raw.locator(".jJc9Ad .GHT2ce.NsCY4 div.RfnDt").count() > 0:
                            review_info = review_raw.locator(".jJc9Ad .GHT2ce.NsCY4 div.RfnDt").inner_text().strip()
                        else:
                            review_info = None

                        # 리뷰 내용이 없을 수 있음
                        if review_raw.locator(".jJc9Ad .GHT2ce .MyEned span.wiI7pd").count() > 0:
                            review_content = review_raw.locator(
                                ".jJc9Ad .GHT2ce .MyEned span.wiI7pd").inner_text().strip().replace('\n', ' ')
                        else:
                            review_content = None

                        # 리뷰 별
                        review_rate = review_raw.locator(".jJc9Ad .fzvQIb").inner_text().strip()

                        # 리뷰 작성후 지난 시간
                        review_at = review_raw.locator(".jJc9Ad .xRkPPb").text_content().strip()

                        review_image_urls = []
                        if review_raw.locator(".jJc9Ad .GHT2ce .KtCyie").count() > 0:
                            if review_raw.locator(".jJc9Ad .GHT2ce .KtCyie .Tap5If").count() > 0:
                                review_raw.locator(".jJc9Ad .GHT2ce .KtCyie .Tap5If").click()
                                page.wait_for_timeout(1000)
                            url_img_buttons = review_raw.locator(".jJc9Ad .GHT2ce .KtCyie button").all()
                            if url_img_buttons:
                                for url_img in url_img_buttons:
                                    style_attribute = url_img.get_attribute("style")
                                    url_match = re.search(r'url\("?(.*?)"?\)', style_attribute)
                                    if url_match:
                                        review_image_urls.append({"url": url_match.group(1)})

                        # images 파일로 다운로드
                        if len(review_image_urls) > 0:
                            print("downloading images...")
                            image_dir = os.path.join('../output/images', name)
                            os.makedirs(image_dir, exist_ok=True)
                            for i, image_url in enumerate(review_image_urls):
                                try:
                                    image_url = image_url['url']
                                    if image_url.startswith('//'):
                                        image_url = 'https:' + image_url

                                    # 이미지 파일 이름 정리
                                    image_name = convert_url_to_safe_file_name(image_url)

                                    image_folder_path = os.path.join(image_dir, str(r_idx))
                                    if not os.path.exists(image_folder_path):
                                        os.makedirs(image_folder_path)
                                    image_path = os.path.join(image_dir, str(r_idx), image_name)

                                    # 파일이 이미 존재하는지 확인
                                    if not os.path.exists(image_path):
                                        print(f"Downloading image: {image_name}")

                                        # 이미지 다운로드
                                        response = requests.get(image_url, stream=True)
                                        response.raise_for_status()  # 요청이 성공하지 않으면 에러 발생

                                        # 이미지 파일로 저장
                                        with open(image_path, 'wb') as file:
                                            for chunk in response.iter_content(1024):  # 파일을 잘게 나눠서 저장
                                                file.write(chunk)

                                        print(f"Image saved: {image_path}")

                                    else:
                                        print(f"Image already exists: {image_path}")

                                    review_image_urls[i]['path'] = os.path.join(name, str(r_idx), image_name)

                                except Exception as e:
                                    print(f"!! Failed to download {image_url}: {e}")

                        review_results.append({
                            "review_idx": r_idx,
                            "review_name": review_name,
                            "review_info": review_info,
                            "review_content": review_content,
                            "review_rate": review_rate,
                            "review_image_urls": review_image_urls,
                            'review_at': review_at
                        })

            # 정보
            print('정보 데이터 파싱..')
            infos = []
            try:
                if page.locator('//button[@role="tab"][4]').count() > 0:
                    page.locator('//button[@role="tab"][4]').click()
                    page.wait_for_timeout(1500)
                    page.wait_for_selector('div.QoXOEc.fontBodySmall')

                    role_divs = page.locator('div.QoXOEc.fontBodySmall  div[role="img"]').all()
                    for role_div in role_divs:
                        role = role_div.inner_text().strip()
                        # print(f"role: {role}")
                        infos.append(role)

                    # 특수문자와 줄바꿈 제거
                    cleaned_infos = [
                        re.sub(r"^[^\w\s]+|\n", "", info) for info in infos
                    ]

                    infos = cleaned_infos

            except Exception as e:
                print("!!", e)

            parse_result = {
                'name': name,
                # 'idx': str(list_idx),
                'infos': infos,
                'price_infos': price_infos,
                'qna_results': qna_results,
                'review_count': review_count,
                'review_average': review_average,
                'latitude': latitude,
                'longitude': longitude,
                'address': address,
                'website': website,
                'phone': phone,
                'reviews': review_results,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'search_keyword': search_keyword,
            }

            end_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            elapsed_time = time.time() - list_start_time

            print(
                f"############### end {name}, end_time: {end_time}, elapsed_time: {elapsed_time:.2f} sec  ###############")

            # data_results.append(parse_result)
            # print("parse_result: ", parse_result)
            json_data = json.dumps(parse_result, ensure_ascii=False, indent=4)
            output_dir = '../output/json/'
            os.makedirs(output_dir, exist_ok=True)
            try:
                with open(f'{output_dir}/output_{name}.json', 'w', encoding='utf-8') as f:
                    f.write(json_data)

            except Exception as e:
                print(f"!! Error writing to file : {e}")


        print("Finished processing and scraping data.")

        context.close()
        browser.close()
        # return data_utils.remove_duplicate_list(data_results)


if __name__ == "__main__":

    search_keywords: list[str] = ["양곤 호텔", "호계동 헬스", "Turkish Restaurants in Toronto Canada", "コインランドリ",
                                  "コインランドリー", "ရန်ကုန် Hotel", "မန္တလေး Hotel", "နေပြည်တော် Hotel"]



    search_keyword = search_keywords[5]

    start_time = time.time()
    formatted_time = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')

    print(
        f" ############### keyword: {search_keyword}, start_time: {formatted_time} ###############")

    # data_results = main(search_keyword, False)  # 질문 답변 파트에서 headless 적용이 안됨 iframe 때문일듯
    main(search_keyword, False)
    # json_data = json.dumps(data_results, ensure_ascii=False, indent=4)
    # Save the scraped result data as a JSON file in the output directory.
    # try:
    #     with open(f'../output/output_{search_keyword}.json', 'w', encoding='utf-8') as f:
    #         f.write(json_data)
    #
    # except Exception as e:
    #     print(f"!! Error writing to file : {e}")

    end_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    elapsed_time = time.time() - start_time

    print(
        f"############### end keyword : {search_keyword}, end_time: {end_time}, elapsed_time: {elapsed_time:.2f} sec  ###############")


    print("end process")
