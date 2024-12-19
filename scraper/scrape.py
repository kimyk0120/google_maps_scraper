# from playwright.async_api import async_playwright
import configparser
import time

from playwright.sync_api import sync_playwright

import utils.string_utils

config = configparser.ConfigParser()
# 'utf-8' 인코딩으로 파일 읽기
config.read('../config/config.ini', encoding='utf-8')

# read section
path_props = config['PATH']
keyword_props = config['KEYWORD']
xpath_props = config['XPATH']

chromium_path = path_props['chromium_path']


# scrape 시작
def main(search_keyword: str) -> list:
    with sync_playwright() as p:
        # 브라우저(Chromium) 열기
        # browser = p.chromium.launch(headless=False, executable_path=chromium_path, args=["--start-maximized"])
        browser = p.chromium.launch(headless=False, executable_path=chromium_path)
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

        timeout = 60  # 초 단위로 설정
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
            page.wait_for_timeout(300)

            page.wait_for_selector(xpath_props['name_xpath'])

            # name
            if page.locator(xpath_props['name_xpath']).count() > 0:
                name = page.locator(xpath_props['name_xpath']).inner_text()
            else:
                continue  # name은 없으면 continue..

            # review count
            if page.locator(xpath_props['reviews_count_xpath']).count() > 0:
                temp = page.locator(xpath_props['reviews_count_xpath']).inner_text()
                temp = temp.replace('(', '').replace(')', '').replace(',', '')
                review_count = int(temp)
            else:
                review_count = None

            # review_average
            if page.locator(xpath_props['reviews_average_xpath']).count() > 0:
                temp = page.locator(xpath_props['reviews_average_xpath']).inner_text()
                temp = temp.replace(' ', '').replace(',', '.')
                review_average = float(temp)
            else:
                review_average = None

            # infos
            infos = []
            if page.locator(xpath_props['infos']).count() > 0:
                infos_els = page.locator(xpath_props['infos']).all()
                for info in infos_els:
                    temp = info.inner_text()
                    cleaned_temp = utils.string_utils.remove_special_chars(temp)
                    cleaned_temp = utils.string_utils.remove_multi_space_chars(cleaned_temp)
                    infos.append(cleaned_temp)





        print("end main")

        context.close()
        browser.close()
        return data_results


if __name__ == "__main__":
    search_keywords: list[str] = ["호계동 헬스", "Turkish Restaurants in Toronto Canada"]

    data_results = main(search_keywords[1])

