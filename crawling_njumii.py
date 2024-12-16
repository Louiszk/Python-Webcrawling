import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
from datetime import datetime
import re
def handle_cookie_consent(driver):
    try:
        cookie_button = driver.find_element(
            By.XPATH, "//a[contains(text(), 'zulassen')]")
        if cookie_button:
            cookie_button.click()
            time.sleep(1) 
            print(f"Cookie consent handled")
    except Exception as e:
        print(e)
        print(f"Cookie consent not found or already handled")

def scroll_down(driver, timeout=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(timeout)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def parse_courses():
    detail_urls = []
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    #driver.maximize_window()

    
    try:
        print("Crawling with Selenium...")

        
        url = "https://www.njumii.de/Kurssuche#firstcourse"
        driver.get(url)
        
        time.sleep(3)  
        
        handle_cookie_consent(driver)
        
        filters = ["Weiterbildung", "CAD", "Energie", "Digitalisierung", "Kauf", "Vertrieb", "Personal", "Datenschutz"]
        for filter in filters:
            filter_button = driver.find_element(By.XPATH, f"//label[contains(text(), '{filter}')]")
            filter_button.click()
            time.sleep(2)

        elements = driver.find_elements(By.XPATH, "//div[@id='kursliste']//a")
        
        hrefs = [element.get_attribute('href') for element in elements if element.get_attribute('href') and 'Kurse/' in element.get_attribute('href')]
        hrefs = list(set(hrefs))
        print(len(hrefs))
        detail_urls = hrefs
        
    except Exception as e:
        print(f"An error occurred while crawling the URL: {url}\nError: {e}")
            
    driver.quit()
    return detail_urls

def parse_main_content(html):
    
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        title = soup.find('h1', class_="nj-course-detail-title").get_text(strip=True)
    except AttributeError:
        title = 'Titel nicht gefunden'
    
    try:
        theme = soup.find('label', class_="nj-chk-theme").get_text(strip=True)
    except AttributeError:
        theme = 'Theme nicht gefunden'
    try:
        date_str = soup.find('p', attrs={"class": "nj-course-detail-subtitle", "style": "margin-top:15px;"}).get_text(strip=True)
        time_str = soup.find('p', attrs={"style": "margin-top:-10px;margin-bottom:20px;"}).get_text(strip=True)
        
        pattern = r"(\d{2}:\d{2}) bis (\d{2}:\d{2})"

        match = re.search(pattern, time_str)
        if match:
            start_time_str = match.group(1)
            end_time_str = match.group(2)
            start_time = datetime.strptime(start_time_str, "%H:%M")
            end_time = datetime.strptime(end_time_str.replace(' Uhr', ''), "%H:%M")
        
        duration = (end_time - start_time).total_seconds() / 60
    except Exception as e:
        date_str = 'Datum nicht gefunden'
        start_time = 'Startzeit nicht gefunden'
        end_time = 'Endzeit nicht gefunden'
        duration = 'Dauer nicht berechnet'

    duration_element = soup.find('p', class_='nj-course-detail-fact', string=lambda x: 'Dauer' in x)
    duration2 = None
    if duration_element:
        duration2 = duration_element.find_next_sibling('p').text.strip()

    zielgruppe_element = soup.find('p', class_='nj-course-detail-fact', string=lambda x: 'Zielgruppe' in x)
    zielgruppe= None
    if duration_element:
        zielgruppe = zielgruppe_element.find_next_sibling('p').text.strip()
    
    voraussetzung_element = soup.find('p', class_='nj-course-detail-fact', string=lambda x: 'Voraussetzung' in x)
    voraussetzung = None
    if duration_element:
        voraussetzung = voraussetzung_element.find_next_sibling('p').text.strip()
    
    map_div = soup.find('div', id='map')

    if map_div:
        location_element = map_div.find_previous('p')
        location = location_element.decode_contents().strip().replace('<br/>', ', ')
    else:
        location = None
    
    # Preis
    price_text = 'Preis nicht gefunden'
    try:
        price_text = soup.find('p', attrs={"class": "nj-course-detail-subtitle", "style": "margin-top:15px"}).get_text(strip=True)
    except AttributeError:
        price_text = 'Preis nicht gefunden'
    
    return (
        title,
        theme,
        zielgruppe, 
        voraussetzung,
        date_str,
        start_time if isinstance(start_time, str) else start_time.strftime("%H:%M"),
        end_time if isinstance(end_time, str) else end_time.strftime("%H:%M"),
        duration,
        duration2,
        location,
        price_text
    )

def get_courses_details(detail_urls):
    course_details = []
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    for i, url in enumerate(detail_urls):
        try:
            
            driver.get(url)
            print(i)

            time.sleep(1)
            main_table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='sc-content-block']/div[@class='row']"))
            )

            main_html = main_table.get_attribute('outerHTML')

            parsed_course = parse_main_content(main_html)
            
            
            course_details.append(parsed_course)

        except Exception as e:
            print(f"An error occurred while parsing the URL: {url}\nError: {e}")
        finally:
            time.sleep(2)

    driver.quit()
    return course_details

if __name__ == "__main__":
    detail_urls = parse_courses()
    rows = get_courses_details(detail_urls)
        
    df = pd.DataFrame(rows, columns=['Kursname', 'Theme', 'Zielgruppe', 'Voraussetzung', 'Termin','Start', 'Ende', 'Dauer', 'Dauer2', 'Ort', 'Preis'])
    df.to_csv('crawling_courses/njumii.csv', sep=';', encoding='utf-8', index=False)




