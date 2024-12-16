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

def parse_courses(html_content):
    
    soup = BeautifulSoup(html_content, 'html.parser')

    a_tags = soup.find('div', attrs={'id':'content-outer'}).find_all('a')
    detail_urls = [a.get('href') for a in a_tags]
            
    return detail_urls

def parse_course(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = soup.find('div', attrs={'id': 'content-outer'})

    try:
        category = content.find(string=re.compile(r"^Veranstaltungsgruppe:\s*")).next.strip()
    except AttributeError:
        category = None

    try:
        title = content.find('h2').get_text(separator=' ').split('\n')[-1].strip()
    except AttributeError:
        title = None

    try:
        datum = content.find(string=re.compile(r"^Termin:\s*")).next.strip()
    except AttributeError:
        datum = None

    try:
        gebuehr1 = content.find(string=re.compile(r"^Zweckverbandsmitglieder:\s*")).next.strip()
    except AttributeError:
        gebuehr1 = None

    try:
        gebuehr2 = content.find(string=re.compile(r"^Nichtmitglieder:\s*")).next.strip()
    except AttributeError:
        gebuehr2 = None

    try:
        ansprechpartner = content.find(string=re.compile(r"^Ansprechpartner:\s*")).next.strip()
    except AttributeError:
        ansprechpartner = None

    try:
        ort = content.find(string="Ort:").next.strip()
    except AttributeError:
        ort = None

    course_tuple = (
        category,
        title,
        datum,
        gebuehr1,
        gebuehr2,
        ansprechpartner,
        ort
    )
    
    return course_tuple
        


if __name__ == "__main__":
    rows = []
    detail_urls = []
    sites = parse_courses(crawl_url("https://www.skvs-sachsen.de/jahresprogramm"))
    for site in sites:
        if site:
            detail_urls.extend(parse_courses(crawl_url(site)))
            time.sleep(0.4)
    
    for i, url in enumerate(detail_urls):
        print(i+1, "/", len(detail_urls))
        if url:
            course = parse_course(crawl_url(url))
            rows.append(course)
            time.sleep(0.4)
        

    
    
    df = pd.DataFrame(rows, columns=['Kategorie', 'Kursname', 'Datum', 'Gebühr Mitglieder', 'Gebühr', 'Ansprechpartner', 'Ort'])
    df.to_csv('crawling_courses/skvs.csv', sep=';', encoding='utf-8')



