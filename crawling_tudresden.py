import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import re
import pandas as pd
import time

def crawl_url(url):

    try:
        response = requests.get(url)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while crawling the URL: {url}\nError: {e}")
    return None

def parse_courses(url):
    try:
        print("Crawling with Selenium...")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
  
        driver.get(url)
        
        time.sleep(2)  
        
  
        touch_feedback_div = driver.find_element(By.XPATH, "//input[@value= 'Suchen']")
        driver.execute_script("arguments[0].click();", touch_feedback_div)
        
        time.sleep(1)

        segments = driver.find_elements(
            By.XPATH, "//div[@class='documentContent']//a")
        detail_urls = [segment.get_attribute('href') for segment in segments]
        
        driver.quit()
        
        return detail_urls
        
    except Exception as e:
        print(f"An error occurred while crawling the URL: {url}\nError: {e}")
        return None

def parse_course(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        content = soup.find('div', class_='documentContent').find('table')
        data = {}

        rows = content.find_all("tr")
        for row in rows:
            key_td = row.find("td", class_="bold_gray")
            value_td = row.find_all("td")[1] if row.find_all("td") else None
            
            if not key_td or not value_td:
                continue
            
            key = key_td.text.strip()
            value = value_td
            
            if key == "Veranstaltungsform":
                data['veranstaltungsform'] = value.get_text(separator=' ', strip=True).split('Bemerkung:')[0].strip()
            
            if key == "Thema":
                data['thema'] = value.text.strip()
            
            if key == "Termine":
                data['termine'] = value.get_text(separator=' ', strip=True)
                
            if key == "Veranstaltungsort":
                data['ort'] = value.text.strip()
            
            if key == "Kosten":
                prices = re.findall(r'\d+,\d{2} Euro', value.get_text(separator=' ', strip=True))
                data['prices'] = ', '.join(prices)
            
            if key == "Anbieter":
                data['veranstalter'] = value.get_text(separator=' ', strip=True)
            
            if key == "Ansprechpartner":
                data['ansprechpartner'] = value.get_text(separator=' ', strip=True)
        
        return (
            data.get('veranstaltungsform', 'N/A'), 
            data.get('thema', 'N/A'), 
            data.get('termine', 'N/A'),
            data.get('ort', 'N/A'), 
            data.get('prices', 'N/A'), 
            data.get('veranstalter', 'N/A'), 
            data.get('ansprechpartner', 'N/A')
        )
    
    except Exception as e:
        print(f"Error parsing course data: {e}")
        return None


if __name__ == "__main__":
    rows = []
    detail_urls = parse_courses("https://wbk.tu-dresden.de/generalize/index.php?g_nid=010200&next=11")
    
    for i, url in enumerate(detail_urls[1:]):
        print(i+1, "/", len(detail_urls))
        if url:
            course = parse_course(crawl_url(url))
            if course:
                rows.append(course)
            time.sleep(1)
        

    
    
    df = pd.DataFrame(rows, columns=['Kategorie', 'Kursname', 'Termine', 'Ort', 'Gebühren', 'Veranstalter', 'Ansprechpartner'])
    df.to_csv('crawling_courses/tudresden.csv', sep=';', encoding='utf-8')



