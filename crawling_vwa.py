import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def crawl_url(url):

    try:
        response = requests.get(url)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while crawling the URL: {url}\nError: {e}")
    return None

def parse_urls(html_content):
    
    soup = BeautifulSoup(html_content, features='xml')
    
    loc_elements = soup.find_all('loc')
    hrefs = [loc.text for loc in loc_elements]
    
    return hrefs

def handle_cookie_consent(driver):
    try:
        cookie_button = driver.find_element(
            By.XPATH, "//button[text()='Speichern und zustimmen']")
        if cookie_button:
            cookie_button.click()
            time.sleep(1) 
            print(f"Cookie consent handled")
    except Exception as e:
        print(f"Cookie consent not found or already handled")

def parse_courses_selenium(urls):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    rows = []
    print(len(urls))
    
    for url in urls:
        try:
            print("Crawling with Selenium...")
            driver.get(url)
            
            time.sleep(1)  
            handle_cookie_consent(driver)
            
            aside = driver.find_element(By.XPATH, "//aside")
            details = {}
            
            try:
                details['Seminar'] = driver.find_element(By.XPATH, "//h1").text
            except Exception as e:
                print(f"Error extracting Seminar title: {e}")
                details['Seminar'] = None
            
            try:
                termine_header = aside.find_element(By.XPATH, ".//h3[contains(text(), 'Termine')]")
                termine_value = termine_header.find_element(By.XPATH, "following-sibling::p").text
                details['Termine'] = termine_value
            except Exception as e:
                print(f"Error extracting Termine: {e}")
                details['Termine'] = None

            try:
                ort_header = aside.find_element(By.XPATH, ".//h3[contains(text(), 'Ort')]")
                ort_value = ort_header.find_element(By.XPATH, "following-sibling::p").text
                details['Ort'] = ort_value
            except Exception as e:
                print(f"Error extracting Ort: {e}")
                details['Ort'] = None

            try:
                kosten_header = aside.find_element(By.XPATH, ".//h3[contains(text(), 'Kosten')]")
                kosten_value = kosten_header.find_element(By.XPATH, "following-sibling::p").text
                details['Kosten'] = kosten_value
            except Exception as e:
                print(f"Error extracting Kosten: {e}")
                details['Kosten'] = None

            try:
                format_header = aside.find_element(By.XPATH, ".//h3[contains(text(), 'Format')]")
                format_value = format_header.find_element(By.XPATH, "following-sibling::p").text
                details['Format'] = format_value
            except Exception as e:
                print(f"Error extracting Format: {e}")
                details['Format'] = None

            try:
                kontakt_header = aside.find_element(By.XPATH, ".//h3[contains(text(), 'Kontakt')]")
                kontakt_value = kontakt_header.find_element(By.XPATH, "following-sibling::div//p").text
                details['Kontakt'] = kontakt_value.replace("\n", " ")
            except Exception as e:
                print(f"Error extracting Kontakt: {e}")
                details['Kontakt'] = None

            try:
                hinweis_header = aside.find_element(By.XPATH, ".//h3[contains(text(), 'Hinweis')]")
                hinweis_value = hinweis_header.find_element(By.XPATH, "following-sibling::div").text
                details['Hinweis'] = hinweis_value
            except Exception as e:
                print(f"Error extracting Hinweis: {e}")
                details['Hinweis'] = None

            rows.append(list(details.values()))
            
        except Exception as e:
            print(f"An error occurred while crawling the URL: {url}\nError: {e}")
    
    print(rows)
    driver.quit()
    return rows


if __name__ == "__main__":
    detail_urls = []
    detail_urls = parse_urls(crawl_url("https://www.vwa-leipzig.de/sitemap-64.xml"))
    rows = parse_courses_selenium(detail_urls)

    df = pd.DataFrame(rows, columns=['Kursname', 'Termine', 'Ort', 'Kosten', 'Format', 'Kontakt', 'Hinweis'])
    df.to_csv('crawling_courses/vwa.csv', sep=';', encoding='utf-8')



