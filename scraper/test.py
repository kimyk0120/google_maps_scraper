import argparse

from numpy.f2py.crackfortran import previous_context
# from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import asyncio
import time
import configparser

config = configparser.ConfigParser()
# 'utf-8' 인코딩으로 파일 읽기
with open('../config/config.ini', encoding='utf-8') as config_file:
    config.read_file(config_file)

# read section
path_props = config['PATH']
keyword_props = config['KEYWORD']
xpath_props = config['XPATH']

chromium_path = path_props['chromium_path']

# scrape 시작
def main():
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
        
        # FIXME 
        search_keyword = "호계동 헬스"
        # search_keyword = "Turkish Restaurants in Toronto Canada"
        
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
                new_listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[previous_list_size:list_size]
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
            text_cont = page.is_visible(f"//span[normalize-space(text())='{last_item_text}']")
            if text_cont:
                break

            # 타임아웃 확인 - 무한 로딩인 경우가 많음
            elapsed_time = time.time() - start_time  # 경과 시간 계산
            if elapsed_time > timeout:
                print("리스트 로딩 타임아웃 경과")
                break
        # .end while

        # list loop
        for listing in total_listings:
            listing.click()
            page.wait_for_timeout(300)

            page.wait_for_selector('//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]')

            name_xpath = '//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]'
            address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
            website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
            phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
            reviews_count_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]'
            reviews_average_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]'

            info1 = '//div[@class="LTs0Rc"][1]'  # store
            info2 = '//div[@class="LTs0Rc"][2]'  # pickup
            info3 = '//div[@class="LTs0Rc"][3]'  # delivery
            opens_at_xpath = '//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]'  # time
            opens_at_xpath2 = '//div[@class="MkV9"]//span[@class="ZDu9vd"]//span[2]'
            place_type_xpath = '//div[@class="LBgpqf"]//button[@class="DkEaL "]'  # type of place
            intro_xpath = '//div[@class="WeS02d fontBodyMedium"]//div[@class="PYvSYb "]'  # ?





        print("end main")

        context.close()
        browser.close()


if __name__ == "__main__":

    main()
