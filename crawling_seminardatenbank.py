import requests
from bs4 import BeautifulSoup
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

def parse_table(html_content):
 
    soup = BeautifulSoup(html_content, 'html.parser')

    detail_urls = []

    trs = soup.find_all('tr')

    for tr in trs:
        a_tags = tr.find_all('a')
        for a_tag in a_tags:
            if a_tag and a_tag['href'] and 'detailseite' in a_tag['href']:
                detail_urls.append(a_tag['href'])
            
    
    return detail_urls


def parse_course(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    details = soup.find('div', class_='seminar-detail')
    
    try:
        title = details.find('h2').get_text(strip=True)
    except AttributeError:
        title = None
        
    try:
        datum_tage = details.find('td', id='td_2616_3').get_text(strip=True).replace('\n', '').strip()
    except AttributeError:
        datum_tage = None
    
    datum = datum_tage.split("/")[0].strip()

    try:
        beginn = details.find('td', id='td_2616_5').get_text(strip=True)
    except AttributeError:
        beginn = None
    
    try:
        ende = details.find('td', id='td_2616_7').get_text(strip=True)
    except AttributeError:
        ende = None

    begin_split = beginn.replace("Uhr", "").split(":")
    end_split = ende.replace("Uhr", "").split(":")
    duration = (int(end_split[0]) - int(begin_split[0]))*60 + (int(end_split[1]) - int(begin_split[1]))
    
    try:
        gebuehr = details.find('td', id='td_2616_15').get_text(strip=True)
    except AttributeError:
        gebuehr = None
    
    try:
        ansprechpartner = details.find('td', id='td_2616_17').get_text(strip=True)
        dozent = details.find('td', id='td_2616_13').get_text(strip=True)
    except AttributeError:
        ansprechpartner = None
        dozent = None
    
    try:
        veranstaltungsort = details.find('td', id='td_2616_19').get_text(separator=', ', strip=True)
        ort, adresse = veranstaltungsort.split(",", 1)
    except AttributeError:
        veranstaltungsort = None
    
    course_tuple = (
        title,
        datum,
        duration,
        gebuehr,
        ansprechpartner,
        dozent,
        ort,
        adresse
    )
    
    return course_tuple
     


if __name__ == "__main__":
    rows = []
    detail_urls = parse_table(crawl_url("https://www.s-vwa.de/seminare/seminardatenbank/"))
    for i, url in enumerate(detail_urls):
        print(i+1, "/", len(detail_urls))
        url = "".join(("https://www.s-vwa.de", url))
        course = parse_course(crawl_url(url))
        rows.append(course)
        time.sleep(2)
        

    
    
    df = pd.DataFrame(rows, columns=['Kursname', 'Datum', 'Dauer', 'Gebühr', 'Ansprechpartner', 'Dozent', 'Ort', 'Adresse'])
    df.to_csv('crawling_courses/seminardatenbank.csv', sep=';', encoding='utf-8')



