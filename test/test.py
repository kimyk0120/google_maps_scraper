import argparse
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import asyncio
import time

chromium_path = "C:\\Users\\kimyk\\Downloads\\chrome-win\\chrome-win\\chrome.exe"


# async def main():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False, executable_path=chromium_path)
#         page = await browser.new_page()
#         await page.goto("http://example.com")
#         await page.screenshot(path="example.png")
#         # await browser.close()
# asyncio.run(main())


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
        # search_keyword = "수리산역"
        search_keyword = "Turkish Restaurants in Toronto Canada"
        
        page.locator('//input[@id="searchboxinput"]').fill(search_keyword.strip())
        page.keyboard.press("Enter")

        page.wait_for_selector('//a[contains(@href, "https://www.google.com/maps/place")]')

        page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

        # last keyword
        last_item_text = '마지막 항목입니다.'

        timeout = 2 * 60  # 초 단위로 설정
        start_time = time.time()  # 현재 시간을 기록

        while True:
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(1500)

            # if found last text break
            text_cont = page.is_visible(f"//span[normalize-space(text())='{last_item_text}']")
            if text_cont:
                break

            # 리스트가 더 발견되면 timeout 초기화

            # 타임아웃 확인 - 무한 로딩인 경우가 많음
            elapsed_time = time.time() - start_time  # 경과 시간 계산
            if elapsed_time > timeout:
                print("리스트 로딩 타임아웃 경과")
                break


        # # 페이지 제목 출력
        # print("Page Title : ", page.title())

        # 브라우저 닫기
        # browser.close()

        print("end main")

        context.close()
        browser.close()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-s", "--search", type=str)
    # parser.add_argument("-t", "--total", type=int)
    # args = parser.parse_args()

    # if args.search:
    #     search_for = args.search
    # else:
    #     search_for = "turkish stores in toronto Canada"
    # if args.total:
    #     total = args.total
    # else:
    #     total = 1

    main()
