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

def get_categories(html_content):

    soup = BeautifulSoup(html_content, 'html.parser')

    a_tags = soup.find('div', attrs={'class':'col-xs-12 col-lg-10 col-center'}).find_all('a')
    
    detail_urls = [(a.get('href'), a.text.strip()) for a in a_tags if a.text.strip() in ["Kinder- und Jugendhilfe", "EDV-Webinare /IT-Kompetenzen", "Kommunikation / Arbeitstechniken", "Projektmanagement", "Führung und Steuerung"]]
            
    return list(set(detail_urls))

def parse_courses(html_content):
    
    soup = BeautifulSoup(html_content, 'html.parser')

    a_tags = soup.find('div', class_="search-results text-left col-xs-12").find_all('a')
    detail_urls = [a.get('href') for a in a_tags]
            
    return list(set([url for url in detail_urls if url and "/seminar/" in url]))

def safe_get_text(element):
    return element.text.strip() if element else None

def parse_course(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = soup.find('div', attrs={'class': 'row border001'})

    try:
        
        titel = safe_get_text(content.find('div', class_='col-xs-12 col-md-offset-1 col-md-10 padt-1').h1)

        typ_div = content.find('div', class_='clearfix bg6 hidden-xs hidden-sm').find_next('div', class_='col-xs-8 small')
        typ = safe_get_text(typ_div)

        orte_div = content.find('div', class_='clearfix bg6 hidden-xs hidden-sm').find_next('div', class_='col-xs-4 small text-uppercase tkomplex', string='Orte')
        orte = safe_get_text(orte_div.find_next_sibling('div'))

        format_div = content.find('div', class_='clearfix bg6 hidden-xs hidden-sm').find_next('div', class_='col-xs-4 small text-uppercase tkomplex', string='Format')
        format = safe_get_text(format_div.find_next_sibling('div')) if format_div else None

        termine = content.find('a', attrs={'href': '#termine'})
        termine = termine['title'].strip() if termine else None

        preis_div = content.find('div', class_='clearfix bg6 hidden-xs hidden-sm').find_next('div', class_='col-xs-4 small text-uppercase tkomplex', string='Preis ab')
        preis = safe_get_text(preis_div.find_next_sibling('div')).split()[0].replace(',', '.') if preis_div else None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    return (titel, typ, orte, format, termine, preis)


if __name__ == "__main__":
    categories = get_categories(crawl_url("https://www.kbw.de/online-seminare"))
    
    rows = []
    for category in categories:
        detail_urls = parse_courses(crawl_url(f"https://www.kbw.de{category[0]}"))
        #detail_urls = ["/kurs/eca-92405/women-in-progress"]
        print(len(detail_urls))
        for i, url in enumerate(detail_urls):
            print(i+1, "/", len(detail_urls))
            if url:
                
                course = parse_course(crawl_url("".join(("https://www.kbw.de", url))))
                if course:
                    rows.append((category[1],) +course)
                    time.sleep(0.4)
            
    df = pd.DataFrame(rows, columns=['Kategorie', 'Titel', 'Typ', 'Orte', 'Format', 'Termine', 'Preis'])
    df.to_csv(f'crawling_courses/kbw.csv', sep=';', encoding='utf-8')



