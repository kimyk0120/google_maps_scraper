Google Maps Scraper  
=======================
This is a Google Maps scraper projet. 
It uses Playwright library to web scraping and data extraction from Google Maps.

This scraper will extract the following information list from the Google Maps:

- name: Store name (e.g., "Store Name")
- review_count: Total number of reviews (e.g., 756)
- review_average: Average review rating (e.g., 4.2)
- infos: Store service information (e.g., ["Dine-in", "Takeout", "Delivery Service"])
- opens_at: Store opening time (e.g., "Opens at 12:00 PM")
- address: Store address (e.g., "25 The West Mall, Etobicoke, ON M9C 1B8 Canada")
- website: Store website (e.g., "sample.com")
- phone: Store phone number (e.g., "+1 416-641-7327")
- place_type: Place type (e.g., "Restaurant")
- reviews: List of detailed review information
- review_name: Reviewer name (e.g., "reviewer name")
- review_info: Number of reviews and photos (e.g., "19 reviews · 12 photos")
- review_content: Review content (e.g., "So good~~")
- review_rate: Review rating (e.g., 5)
- review_image_urls: List of review image URLs (e.g., ["https://sample.com/p/-k-no", "https://sample.com/p/-k-no2"])
- review_at: Review posted time (e.g., "1 week ago")

```json
[
    {
        "name": "Store Name",   
        "review_count": 756,   
        "review_average": 4.2,
        "infos": [
            "매장 내 식사",
            "테이크아웃",
            "배달 서비스"
        ],
        "opens_at": "오후 12:00에 영업 시작",
        "address": "25 The West Mall, Etobicoke, ON M9C 1B8 캐나다",
        "website": "sample.com",
        "phone": "+1 416-641-7327",
        "place_type": "음식점",
        "reviews": [
            {
                "review_name": "reviewer name",
                "review_info": "리뷰 19개 · 사진 12장",
                "review_content": "So good~~",
                "review_rate": 5,
                "review_image_urls": [
                    "https://sample.com/p/-k-no",
                    "https://sample.com/p/-k-no2",
                ],
                "review_at": "1주 전"
            },
        ...
```

## Prerequisite
- python >= 3.10 
- chromium

## Features
- Data Scraping: Scrap data from Google Maps to extract information such as business names, addresses, websites, contact information, and reviews. The data structure is output as a json file, and the json structure is as above.
- You can adjust the number of lists, set proxy settings, or change the xpath by setting config.ini.

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/kimyk0120/google_maps_scraper
   ```
2. Move to the project directory:
   
3. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
   ```
## How to Use:

To use this script, follow these steps:

### Set up Configuration
You need to configure the necessary settings in the {project}/config/config.ini file.
- You must write the path to the chromium executable in "chromium_path".  
  - ```chromium_path = C:\Users\kimyk\Downloads\chrome-win\chrome-win\chrome.exe```
- Set "timout_sec" appropriately to prevent infinite loading.
- Set the maximum number of businesses to scrape with the "store_limit_cnt" setting.
- Set the maximum number of reviews to scrape with the "review_limit_cnt" setting.
- If you need proxy settings, put them in "proxy_server"

### Run the script with Python:
  ```bash 
    python main.py "search term" 
  ```
If you need to change the output path, do as follows.
   ```bash
     python main.py "search term" --output "ouput path"
  ```

