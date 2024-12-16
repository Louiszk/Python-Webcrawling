import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

def crawl_url(url):

    try:
        response = requests.get(url)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while crawling the URL: {url}\nError: {e}")
    return None

def parse_date(html_content):
 
    soup = BeautifulSoup(html_content, 'html.parser')

    table = soup.find_all('td')
    tuples = []
    for i, td in enumerate(table):
        tuple_pos = i//2
        if i%2==0:
            time = td.text.split("\r\n")
            date = time[1].strip()
            interval = time[2].strip().split(" - ")
            begin_split = interval[0].split(":")
            end_split = interval[1].split(":")
            duration = (int(end_split[0]) - int(begin_split[0]))*60 + (int(end_split[1]) - int(begin_split[1]))
            tuples.append((date, interval[0], interval[1], duration))
        else:
            link = td.find('a')
            event = link.text
            href = link['href']
            location = td.find('i').text if td.find('i') else None
            tuples[tuple_pos] += (event, location, href)
            
    return tuples

def extract_price(text):
    # Regex to capture a number (including decimal numbers) followed by 'Euro', '€', or preceded by '€'
    pattern = r'(\d+[\.,]?\d*)\s*Euro|(\d+[\.,]?\d*)\s*€|€\s*(\d+[\.,]?\d*)'
    match = re.search(pattern, text)
    
    if match:
        
        price = next((x for x in match.groups() if x), None)
        if price:
            
            price = float(price.replace(',', '.'))
            return price
    return None

def parse_event(content):
    soup = BeautifulSoup(content, 'html.parser')

    all_text = soup.find_all('p')
    categories, price = None, None
    #print(all_text)
    for i, p in enumerate(all_text):
        if p.find('strong') and p.find('strong').text == "Kategorien":
            categories = all_text[i+1].text.replace("\n", "").replace("\r", "")
        if ' Euro ' in p.text or '€' in p.text:
            price = extract_price(p.text)
    return (categories, price)

if __name__ == "__main__":
    print("Running")
    number_dates = 31
    full_tuples = []
    for j in range(2):
        for i in range(number_dates):
            print(i)
            url_to_crawl = f'https://www.frauenzentrum-bautzen.de/fzbtz/veranstaltungen/2024-0{j+5}-{i+1:02}/'
            html_content = crawl_url(url_to_crawl)
            if html_content:
                tuples = parse_date(html_content)
                print(tuples)
                for t in tuples:
                    event_url = t[6]
                    content = crawl_url(event_url)
                    new_tuple = parse_event(content)
                    full_tuples.append(t + new_tuple)
    df = pd.DataFrame(full_tuples, columns=['Datum', 'Beginn', 'Ende', 'Dauer', 'Veranstaltung', 'Ort', 'URL', 'Kategorie', 'Preis'])
    df.to_csv('Veranstaltungen_Mai.csv', sep=';')

