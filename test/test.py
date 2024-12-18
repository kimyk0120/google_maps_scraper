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
with sync_playwright() as p:
    # 브라우저(Chromium) 열기
    browser = p.chromium.launch(headless=False, executable_path=chromium_path)  # headless=False는 브라우저가 눈에 보이도록 설정
    page = browser.new_page()

    # 웹 페이지 열기
    page.goto('https://www.google.com')

    # 페이지 제목 출력
    print(page.title())

    # 브라우저 닫기
    browser.close()


sync_playwright()