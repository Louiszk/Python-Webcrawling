import requests
from bs4 import BeautifulSoup, NavigableString
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
    a_tags = soup.find('div', attrs={'class':'c-deck__inner'}).find_all('a', attrs={'class':'readon'})
    detail_urls = [a.get('href') for a in a_tags if not isinstance(a, NavigableString)]
            
    return detail_urls

def parse_course(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = soup.find('article')
    
    titel = content.find('h1', class_='header__title').get_text(strip=True)
    
    inhalte = content.find('h2', string='Inhalte').find_next_sibling('p').get_text(strip=True)
    
    leitung = content.find('h2', string='Leitung').find_next_sibling('p').get_text(strip=True)
    
    teilnahmekreis = content.find('h2', string='Teilnahmekreis').find_next_sibling('p').get_text(strip=True)
    
    themenbereich = content.find('h2', string='Themenbereich').find_next_sibling('p').get_text(strip=True)
    
    anbieterin = content.find('div', class_='c-contact__header').find('h3', class_='h2 title').get_text(strip=True)
    
    termine_section = content.find('aside').find('h2', string='Termine').find_next_sibling('p')
    termine = termine_section.find('time').get_text(strip=True) + " " + termine_section.find('span').get_text(strip=True)
    
    status = ", ".join([span.get_text(strip=True) for span in termine_section.find_all('span', role='status')])
    
    return (themenbereich, titel, inhalte.strip(), teilnahmekreis, termine, status,leitung, anbieterin)



if __name__ == "__main__":
    rows = []
    detail_urls = []
    sites = True
    page = 0
    while sites:
        page_url = f"https://fortbildung.uni-leipzig.de/fortbildungsdatenbank-angebote.html?page={page}" 
        sites = parse_courses(crawl_url(page_url))
        detail_urls.extend(sites)
        page += 1
        time.sleep(1)
    
    for i, url in enumerate(detail_urls):
        print(i+1, "/", len(detail_urls))
        if url:
            course = parse_course(crawl_url("/".join(("https://fortbildung.uni-leipzig.de", url))))
            print(course)
            rows.append(course)
            time.sleep(1)
    
    df = pd.DataFrame(rows, columns=['Kategorie', 'Kursname', 'Inhalte', 'Teilnahmekreis', 'Termine', 'Status', 'Leitung', 'Anbieterin'])
    df.to_csv('crawling_courses/unileipzig.csv', sep=';', encoding='utf-8')
