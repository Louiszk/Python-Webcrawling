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
            By.XPATH, "//button[contains(text(), 'Ablehnen')]")
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

        
        url = f"https://www.ihk.de/dresden/system/veranstaltungen-webinare-fortbildung/6041314?actionId=SEARCH"
        driver.get(url)
        
        time.sleep(3)  
        
        handle_cookie_consent(driver)
        scroll_down(driver)
        elements = driver.find_elements(By.XPATH, "//main//a")
        
        hrefs = [element.get_attribute('href') for element in elements if 'events.dresden' in element.get_attribute('href')]
        
        print(len(hrefs))
        detail_urls.extend(hrefs)
        
    except Exception as e:
        print(f"An error occurred while crawling the URL: {url}\nError: {e}")
            
    driver.quit()
    return detail_urls

def parse_main_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        # Titel
        title = soup.find_all('h1')[1].get_text(strip=True)
    except AttributeError:
        title = 'Titel nicht gefunden'
    
    try:
        
        datetime_text = soup.find('div', class_='lead').get_text(strip=True)
        date_str, time_str = datetime_text.split(', ')
        
        start_time_str, end_time_str = time_str.split(' - ')
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(end_time_str.replace(' Uhr', ''), "%H:%M")
        
        duration = (end_time - start_time).total_seconds() / 60
    except (AttributeError, ValueError, IndexError) as e:
        date_str = 'Datum nicht gefunden'
        start_time = 'Startzeit nicht gefunden'
        end_time = 'Endzeit nicht gefunden'
        duration = 'Dauer nicht berechnet'
    
    try:
        
        location_text = soup.find('p', string=re.compile('Veranstaltungsort:')).get_text(strip=True)
        location = location_text.replace('Veranstaltungsort:', '').strip()
    except AttributeError:
        try:
            location_strong = soup.find('strong', string=re.compile('Veranstaltungsort:')).parent.get_text(strip=True)
            location = location_strong.replace('Veranstaltungsort:', '').strip()
        except AttributeError:
            location = 'Standort nicht gefunden'
    
    price_text = 'Preis nicht gefunden'
    try:
        price_headings = soup.find_all('div', class_='section-heading')
        for heading in price_headings:
            if 'Preis' in heading.get_text():
                price_div = heading.find('div', class_='lead')
                if price_div:
                    price_text = price_div.get_text(strip=True)
                    break
    except AttributeError:
        price_text = 'Preis nicht gefunden'
    
    return (
        title,
        date_str,
        start_time if isinstance(start_time, str) else start_time.strftime("%H:%M"),
        end_time if isinstance(end_time, str) else end_time.strftime("%H:%M"),
        f"{duration} Minuten" if isinstance(duration, (int, float)) else duration,
        location,
        price_text
    )

def get_courses_details(detail_urls):
    course_details = []
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    for url in detail_urls:
        try:
            print(f"Parsing details from: {url}")
            driver.get(url)

            main_table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//main"))
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
        
    df = pd.DataFrame(rows, columns=['Kursname', 'Termin','Start', 'Ende', 'Dauer','Ort', 'Preis'])
    df.to_csv('crawling_courses/ihk.csv', sep=';', encoding='utf-8')




