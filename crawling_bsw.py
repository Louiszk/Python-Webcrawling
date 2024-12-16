import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def handle_cookie_consent(driver):
    try:
        cookie_button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Speichern')]")
        if cookie_button:
            cookie_button.click()
            time.sleep(1) 
            print(f"Cookie consent handled")
    except Exception as e:
        print(f"Cookie consent not found or already handled")

def parse_courses():
    detail_urls = []
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    #driver.maximize_window()

    for i in range(5):
        try:
            print("Crawling with Selenium...")

            
            url = f"https://www.bsw-sachsen.de/unternehmen/weiterbildung/qualifizierung-fuer-gewerbliche-fachkraefte-kopie-1/#/de/classes/page/{i+1}/order_by/class_startdate/ASC?dp_id=4"
            driver.get(url)
            
            time.sleep(2)  
            if i==0:
                handle_cookie_consent(driver)
            iframe = driver.find_element(By.XPATH, ".//iframe")
            driver.switch_to.frame(iframe)
            elements = driver.find_elements(By.XPATH, "//table[@class='table list-table']//a")
            
            hrefs = [element.get_attribute('href') for element in elements if 'classes/view' in element.get_attribute('href')]
            
            print(hrefs)
            detail_urls.extend(hrefs)
          
        except Exception as e:
            print(f"An error occurred while crawling the URL: {url}\nError: {e}")
            
    driver.quit()
    return detail_urls

def parse_courses_details(detail_urls):
    course_details = []
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    for url in detail_urls:
        try:
            print(f"Parsing details from: {url}")
            driver.get(url)

            main_table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='container-fluid']"))
            )

            # Extract details from table
            category = main_table.find_element(By.XPATH, ".//td[contains(text(),'Kategorie')]/following-sibling::td").text
            title = main_table.find_element(By.XPATH, ".//td[contains(text(),'Kurs')]/following-sibling::td").text
            timeframe = main_table.find_element(By.XPATH, ".//td[contains(text(),'Zeitraum')]/following-sibling::td").text
            course_format = main_table.find_element(By.XPATH, ".//td[contains(text(),'Kursformat')]/following-sibling::td").text
            course_type = main_table.find_element(By.XPATH, ".//td[contains(text(),'Veranstaltungsart')]/following-sibling::td").text
            price = main_table.find_element(By.XPATH, ".//td[contains(text(),'Preis')]/following-sibling::td").text
            
            time_point = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table[@class='table dates-table']//td[2]"))
            ).text.replace(" Uhr", "")
            begin, end = time_point.split(" - ")
            begin_split = begin.split(":")
            end_split = end.split(":")
            duration = (int(end_split[0]) - int(begin_split[0]))*60 + (int(end_split[1]) - int(begin_split[1]))
            
            location_contact = driver.find_element(By.XPATH, "//div[@class='box tinted']").text.split('\n')
            location = f"{location_contact[1]}, {location_contact[2]}"
            address = f"{location_contact[3]}, {location_contact[4]}"
            contact = ' '.join(location_contact[5:])

            
            course_details.append((category, title, timeframe, time_point, duration, course_format, course_type, price, location, address, contact))

        except Exception as e:
            print(f"An error occurred while parsing the URL: {url}\nError: {e}")

    driver.quit()
    print(course_details)
    return course_details

if __name__ == "__main__":
    detail_urls = parse_courses()
    rows = parse_courses_details(detail_urls)
        
    df = pd.DataFrame(rows, columns=['Kategorie', 'Kursname', 'Termine', 'Uhrzeit', 'Dauer', 'Format', 'Typ', 'Preis', 'Ort', 'Adresse', 'Kontakt'])
    df.to_csv('crawling_courses/bsw.csv', sep=';', encoding='utf-8')



