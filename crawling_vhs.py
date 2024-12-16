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

def parse_subcategories(html_content):
 
    soup = BeautifulSoup(html_content, 'html.parser')

    categories = soup.find_all('a', attrs={"class": "category-childs-item"})
    categories = [(c.text.split("\n")[2].strip(), c['href']) for c in categories]
    return categories

def parse_all_courses(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    courses = soup.find_all('a', attrs={"class": "card-list-item bg-white"})
    courses = [c['href'] for c in courses]
    return courses

def parse_course(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    name = soup.find('h1').text.strip()
    try:
        price = soup.find('div', attrs={"class": "course-priceNumber"}).text.strip()
    except Exception as e:
        price = None
    dates = soup.find_all('div', attrs={"class":"d-flex align-items-center"})
    try:
        termine = soup.find('small', attrs={"class": "badge badge-primary-10 text-primary ml-2"}).text.strip()
    except Exception as e:
        termine = None
    start = dates[0].text.replace(" ", "").split("\n")[6]
    end = dates[1].text.replace(" ", "").split("\n")[6]
    begin_split = start.replace("Uhr", "").split(":")
    end_split = end.replace("Uhr", "").split(":")
    duration = (int(end_split[0]) - int(begin_split[0]))*60 + (int(end_split[1]) - int(begin_split[1]))
    try:
        loc = soup.find('div', attrs={"id":"course_branchID"}).text.split(": ")[1].strip()
    except Exception as e:
        loc = None
    #print(name, price, start, end, termine, loc)
    return (name, price, termine, start, end, duration, loc)


if __name__ == "__main__":
    rows = []
    all_categories = [("Gesundheit und Ernährung", "https://www.vhs-lkl.de/p/475-CAT-KAT1"), ("Sprachen", "https://www.vhs-lkl.de/p/475-CAT-KAT403")]
    for category in all_categories:
        subcategories = parse_subcategories(crawl_url(category[1]))

        for sc in subcategories:
            courses = parse_all_courses(crawl_url("".join(("https://www.vhs-lkl.de", sc[1]))))

            for i, course in enumerate(courses):
                print("Parsing Course ", i)
                infos = parse_course(crawl_url("".join(("https://www.vhs-lkl.de", course))))
                tuple = (category[0], sc[0]) + infos
                rows.append(tuple)
    
    df = pd.DataFrame(rows, columns=['Kategorie', 'Unterkategorie', 'Kursname', 'Gebühr', 'Termine', 'Start', 'Ende', 'Dauer', 'Geschäftsstelle'])
    df.to_csv('Courses_Health_Diet_Languages.csv', sep=';', encoding='utf-8')



