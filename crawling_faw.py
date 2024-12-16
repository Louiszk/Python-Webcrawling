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

    a_tags = soup.find('div', attrs={'id':'box_courses'}).find_all('a')
    detail_urls = [a.get('href') for a in a_tags]
            
    return list(set(detail_urls))

def safe_get_text(element):
    return element.text.strip() if element else None

def parse_course(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = soup.find('main', attrs={'id': 'mainspace'})

    course_name = safe_get_text(content.find('h1', itemprop='name'))
    
    description = safe_get_text(content.find('div', itemprop='description'))
    
    target_group_section = content.find('div', class_='targetgroup')
    target_groups = ", ".join([safe_get_text(li) for li in target_group_section.find_all('li')]) if target_group_section else None
    
    requirements_section = content.find('div', class_='requirements')
    requirements = ", ".join([safe_get_text(li) for li in requirements_section.find_all('li')]) if requirements_section else None
    
    events = []
    event_list = content.find('div', class_='box_events')
    if event_list:
        for event_item in event_list.find_all('li', class_='events-item'):
            location = safe_get_text(event_item.find('div', class_='event-location'))
            location = location.replace("Anfahrtsskizze", "") if location else location
            dates = safe_get_text(event_item.find('div', class_='event-date'))
            contact = safe_get_text(event_item.find('div', class_='event-ap').find('span', itemprop='name'))
            times = safe_get_text(event_item.find('div', class_='event-times'))
            if location and contact and dates and times:
                events.append("\n".join((location, contact, dates, times)))
    
    row = (course_name, description, target_groups, requirements, events)
    return row

def extract_id(url):
    try:
        
        match = re.search(r'/kurs/(eca-\d+)/', url)
        if match:
            return match.group(1)
        else:
            raise ValueError("No ID found in the URL")
    except Exception as e:
        print(f"Error extracting ID: {e}")
        return None

if __name__ == "__main__":
    categories = ["weiterbildung",
                   "online-weiterbilden/online-umschulungen",
                     "online-weiterbilden/teilqualifizierungen",
                       "online-weiterbilden/vorbereitung-auf-die-externenpruefung",
                         "online-weiterbilden/grundkompetenzen-und-digitale-kompetenzen",
                         "online-weiterbilden/betriebliche-fachwirte-und-meister",
                           "sprache-integration", "vermittlung-beratung"]
    for category in categories[1:]:
        rows = []
        detail_urls = parse_courses(crawl_url(f"https://www.faw.de/{category}"))
        #detail_urls = ["/kurs/eca-92405/women-in-progress"]
        
        for i, url in enumerate(detail_urls):
            print(i+1, "/", len(detail_urls))
            if url:
                course_id = extract_id(url)
                course = parse_course(crawl_url("".join(("https://www.faw.de", url))))
                rows.append((category, course_id) +course)
                time.sleep(0.4)
            
        df = pd.DataFrame(columns=['Seite', 'KursID', 'Kursname', 'Beschreibung', 'Zielgruppe', 'Voraussetzungen'])


        row_dicts = []

        for row_tuple in rows:
            seite, kurs_id, kursname, beschreibung, zielgruppe, voraussetzungen, events = row_tuple
            
            row_data = {
                'Seite': seite,
                'KursID': kurs_id,
                'Kursname': kursname,
                'Beschreibung': beschreibung,
                'Zielgruppe': zielgruppe,
                'Voraussetzungen': voraussetzungen
            }
            
            
            for i, event in enumerate(events, start=1):
                row_data[f'Event{i}'] = event
            
            row_dicts.append(row_data)

        df = pd.concat([pd.DataFrame([row]) for row in row_dicts], ignore_index=True)

        df.to_csv(f'crawling_courses/faw_{category}.csv', sep=';', encoding='utf-8')



