import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import re
import string
from konlpy.tag import Komoran
engine = Komoran()

# Load stopwords from file
with open('stopwords.txt', 'r', encoding='utf-8') as stopwords_file:
    stopwords = set(stopwords_file.read().splitlines())

# Input multiple keywords separated by commas
keywords = input('검색어를 입력하세요 (쉼표로 구분): ').split(',')
startdate = input('시작 날짜(2023.08.01 형태): ')
enddate = input('시작 날짜(2023.08.01 형태): ')

# word count에서 제외
exclude_keywords = set(word.strip() for keyword in keywords for word in keyword.split())
print('exclude_keywords: ', exclude_keywords)


pageNum = 1
lastpage = 300

news_data = []
unique_urls = set()

# 정규화
def preprocess(text):
    text = text.strip()
    text = re.compile('<.*?>').sub('', text)
    text = re.compile('[%s]' % re.escape(string.punctuation)).sub(' ', text)
    text = re.sub('\s+', ' ', text)
    text = re.sub(r'\[[0-9]*\]', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', str(text).strip())
    text = re.sub(r'\d', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', '')  # Add this line to replace '\n' with ''


    text = engine.nouns(text)

    # stopwords, exclude_keywords, 한 글자 제외
    text = [word for word in text if word not in stopwords and word not in exclude_keywords and len(word) > 1]
    print(text[:5])

    return text

for keyword in keywords:
    for i in range(1, lastpage * 10, 10):
        print(f"{pageNum} 페이지 - 키워드: {keyword} ------------------------------")
        try:
            if startdate and enddate:
                url=f"https://search.naver.com/search.naver?where=news&sm=tab_pge&query={keyword}&sort=0&photo=0&field=0&pd=3&ds={startdate}&de={enddate}&cluster_rank=16&mynews=0&office_type=0&office_section_code=0&news_office_checked=&office_category=0&service_area=0&nso=so&start={i}"
            else:
                url=f"https://search.naver.com/search.naver?where=news&sm=tab_jum&query={keyword}&start={i}"

            print(f'url: {url}')
            response=requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses

        except requests.exceptions.RequestException as e:
            print(f"Error making request for keyword {keyword}, page {pageNum}: {e}")
            # Handle 403 Forbidden error
            if response.status_code == 403:
                time.sleep(10)  # Wait for 10 seconds
                continue


        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.select("div.info_group")
        cnt = 0

        for article in articles:
            links = article.select("a.info")
            if len(links) > 1:
                url = links[1].attrs['href']

                if url not in unique_urls:
                    try:
                        time.sleep(0.2)
                        response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'})
                        response.raise_for_status()
                        html = response.text
                        soup = BeautifulSoup(html, 'html.parser')
                        content = soup.select_one('#dic_area')

                        # Check if content is not None before accessing its text
                        if content:
                            description=preprocess(content.text)

                            date_element = soup.select_one('.media_end_head_info_datestamp_time')
                            date_string = date_element['data-date-time']
                            news_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime('%Y%m%d')


                            news_data.append({'URL': url, 'Description': description, 'Date': news_date})
                            unique_urls.add(url)

                            print(f"{cnt}번 뉴스 주소 : {url}\n{description}\n{news_date}\n")
                            cnt += 1
                        else:
                            print(f"Content is None for URL: {url}")
                            continue

                        time.sleep(0.2)
                    except requests.exceptions.RequestException as e:
                        print(f"Error fetching content from {url}: {e}")
                        continue
        pageNum = pageNum + 1

csv_filename=startdate[:4]+'_to_'+enddate[:4]+'_'
csv_filename = csv_filename + '_'.join(keywords) + '_news_data.csv'
with open(csv_filename, mode='w', encoding='utf-8-sig', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['URL', 'Description', 'Date'])
    writer.writeheader()
    writer.writerows(news_data)