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

def get_type_urls(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    panel_bodies = soup.find_all('div', attrs={'class':'panel-body'})
    links_list = []
    for panel_body in panel_bodies:
        h4_tags = panel_body.find_all('h4')
        for h4 in h4_tags:
            a_tag = h4.find('a')
            if a_tag:
                text = a_tag.get_text(strip=True)
                href = a_tag.get('href')
                if 'courselist' in href:
                    links_list.append((text, href))
    
    return links_list


def parse_courses(url):
    detail_urls = []
    offset = 0
    while True:
        html_content = crawl_url('&'.join((url, f'offset={offset}')))
        soup = BeautifulSoup(html_content, 'html.parser')

        listwrapper = soup.find('div', attrs={'class':'listgroup-wrapper'})
        if not listwrapper:
            print("no list found")
        a_tags = listwrapper.find_all('a') if listwrapper else None
        
        if a_tags:
            urls = [a.get('href') for a in a_tags]
            detail_urls.extend(urls)
            print("Increasing Offset")
            offset += 20
            time.sleep(0.4)
        else:
            break
            
    return list(set(detail_urls))

def get_all_p_until_next_h(tag):
    p_tags = []
    for sibling in tag.find_next_siblings():
        if sibling.name and sibling.name.startswith('h'):
            break
        if sibling.name == 'p':
            p_tags.append(sibling.get_text(strip=True))
    return ", ".join(p_tags)

def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', ' ', text).strip()

def parse_course(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = soup.find('div', attrs={'class': 'container content'})
    details = content.find('div', class_='col-sm-5')
    try:
        
        try:
            name = content.find('h1', class_='odav-pagetitle').get_text(strip=True)
        except AttributeError:
            name = None
        
        
        try:
            lessons = clean_text(get_all_p_until_next_h(details.find('h3', string='Unterricht')))
        except AttributeError:
            lessons = None
        
        try:
            price = clean_text(details.find('h3', string='Gebühren').find_next('p').get_text(strip=True).replace("Kurs:", ""))
        except AttributeError:
            price = None
        
        try:
            location = get_all_p_until_next_h(details.find('h3', string='Lehrgangsort'))
        except AttributeError:
            location = None
        
        try:
            contact = clean_text(content.find('div', class_='teaser-text').get_text(separator=' ', strip=True))
        except AttributeError:
            contact = None

        row = (name, lessons, price, location, contact)
        
        return row
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return (None, None, None, None, None)
    


if __name__ == "__main__":
    type_urls = get_type_urls(crawl_url("https://www.hwk-leipzig.de/artikel/kurse-und-seminare-der-handwerkskammer-zu-leipzig-3,952,635.html"))
    rows = []
    print(len(type_urls))
    for type_url in type_urls:
        detail_urls = parse_courses("".join(("https://www.hwk-leipzig.de", type_url[1])))
        
        for i, url in enumerate(detail_urls):
            print(i+1, "/", len(detail_urls))
            if url:            
                course = parse_course(crawl_url("".join(("https://www.hwk-leipzig.de", url))))
                rows.append((type_url[0],) + course)
                time.sleep(0.4)
            
    df = pd.DataFrame(rows, columns=['Typ', 'Kursname', 'Unterricht', 'Preis', 'Ort', 'Ansprechpartner'])
    df.to_csv(f'crawling_courses/hwk.csv', sep=';', encoding='utf-8')



