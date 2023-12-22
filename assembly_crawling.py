from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup as Soup
import pandas as pd

law_name = []
content_list = []
opinion_list = []
opposite_list = []

df = pd.DataFrame(columns=['law_name', 'content', 'opinions'])

filename = './국회입법예고_복지법_19.csv'

url = 'https://pal.assembly.go.kr/napal/search/lgsltpaSearch/list.do'
driver = webdriver.Chrome()
driver.get(url)
driver.maximize_window()  # 브라우저 창 최대화
driver.implicitly_wait(10)

#원하는 검색어 설정
search_input = driver.find_element(By.ID, "search_txt_billName")
search_query = "복지법"
search_input.send_keys(search_query)

#원하는 대 선택
dropdown = driver.find_element(By.ID, "search_sel_fromAge")
select = Select(dropdown)
select.select_by_value("19")

dropdown = driver.find_element(By.ID, "search_sel_toAge")
select = Select(dropdown)
select.select_by_value("19")

driver.find_element(By.ID, "btn_search").click()

#전체 페이지 확인
html = driver.page_source
soup = Soup(html, 'html.parser')
page_spans = soup.find_all("span", text=lambda text: text and " 페이지" in text)
number = page_spans[0].text.split('/')[-1].strip()
number = number.split(' ')[0].strip(')')
page_num = int(number, 10)

href_list = []

#법률안명 수집
for page in range(1, page_num+1):
    print("process: ", page, "/", page_num)

    a_list = soup.find_all('a', {'class': 'board_subject'})
    href_list += [a.get('href') for a in a_list]

    page += 1
    if page == page_num + 1:
        break
    if page % 10 == 1:
        next_list_link = driver.find_element(By.CSS_SELECTOR, 'a[title="다음 목록"]')
    else:
        next_list_link = driver.find_element(By.XPATH, f'//span[text()="{page}"]')
    next_list_link.click()

print(len(href_list))

for href in href_list:
    url = 'https://pal.assembly.go.kr' + href
    driver.get(url)
    driver.implicitly_wait(100)
    html = driver.page_source
    soup = Soup(html, 'html.parser')

    #법률안 명
    h3_list = soup.find_all('h3')[1]
    law_name.append(h3_list.text)

    #제안 이유 및 주요내용
    desc_div = soup.find('div', class_='desc')
    text = desc_div.get_text(separator=' ', strip=True)
    content_list.append(text)

    #의견목록
    element = driver.find_element(By.XPATH, '//*[@id="cnts-tab-list"]/li[2]/a').click()
    driver.implicitly_wait(10)

    # 페이지 확인
    html = driver.page_source
    soup = Soup(html, 'html.parser')
    spans = soup.find_all("span", text=lambda text: text and " 페이지" in text)
    pageNum = spans[0].text.split('/')[-1].strip()
    pageNum = int(pageNum.split(' ')[0].strip(')'))

    a_list = soup.find_all('a', {'class': 'board_subject'})

    if pageNum >= 2:
        for page in range(1, pageNum + 1):
            page += 1
            if page == page_num + 1:
                break
            if page % 10 == 1:
                next_list_link = driver.find_element(By.CSS_SELECTOR, 'a[title="다음 목록"]')
                next_list_link.click()
            else:
                js_script = f'fnSearch({page})'
                driver.execute_script(js_script)

            html = driver.page_source
            soup = Soup(html, 'html.parser')
            a_list += soup.find_all('a', {'class': 'board_subject'})

    if not a_list:
        opinion_list.append("의견 없음")
    else:
        text_list = []
        for a in a_list:
            text_list.append(a.get_text(strip=True))
        opinion_list.append(text_list)


df['law_name'] = law_name
df['content'] = content_list
df['opinions'] = opinion_list

df.to_csv(filename, index=False)

print(df.head())