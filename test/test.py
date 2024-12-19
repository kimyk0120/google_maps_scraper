import argparse

from numpy.f2py.crackfortran import previous_context
# from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import asyncio
import time

chromium_path = "C:\\Users\\kimyk\\Downloads\\chrome-win\\chrome-win\\chrome.exe"


def extract_data(xpath, data_list, page):
    if page.locator(xpath).count() > 0:
        data = page.locator(xpath).inner_text()
    else:
        data = ""
    data_list.append(data)


# Playwright 시작
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
        # search_keyword = "수리산역 음식점"
        search_keyword = "Turkish Restaurants in Toronto Canada"
        
        page.locator('//input[@id="searchboxinput"]').fill(search_keyword.strip())
        page.keyboard.press("Enter")

        page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')

        page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

        # last keyword
        last_item_text = '마지막 항목입니다.'

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





        print("end main")

        context.close()
        browser.close()


if __name__ == "__main__":

    main()
