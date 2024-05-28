import multiprocessing
multiprocessing.set_start_method('spawn', True)
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pymongo
import time
from datetime import date

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
}

async def get_page_content(url):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            elif response.status == 403:
                print('Access forbidden. Status code: 403')
            else:
                print(f'Failed to retrieve the page. Status code: {response.status}')
            return None

def print_job_info(job_info):
    for title, company, salary, location, link in job_info:
        print(f'Title: {title}')
        print(f'Company: {company}')
        print(f'Salary: {salary}')
        print(f'Location: {location}')
        print(f'Link: {link}')
        print('-' * 40)

def extract_job_information(job, url):
    (element, attribute) = selector_map[url]['title']
    title_tag = job.find(element, attribute)

    (element, attribute) = selector_map[url]['company']
    company_tag = job.find(element, attribute)

    (element, attribute) = selector_map[url]['salary']
    salary_tag = job.find(element, attribute)

    (element, attribute) = selector_map[url]['location']
    location_tag = job.find(element, attribute)

    (element, attribute) = selector_map[url]['link']
    link_tag = job.find(element, attribute)

    title = title_tag.get_text(strip=True) if title_tag else 'No title'
    company = company_tag.get_text(strip=True) if company_tag else 'Brak firmy'
    salary = salary_tag.get_text(strip=True) if salary_tag else 'Brak pensji'
    location = location_tag.get_text(strip=True) if location_tag else 'Brak lokalizacji'
    if url == 'rocketjobs':
        link = f"https://rocketjobs.pl{link_tag['href']}" if link_tag else 'No link'
    else:
        link = link_tag.get('href') if link_tag else 'No link'

    if title == 'No title' or link == 'No link':
        return None
    return (title, company, salary, location, link)

def parse_and_extract_job_information(args):
    url, page_content = args
    job_info_list = []
    if page_content:
        soup = BeautifulSoup(page_content, 'html.parser')
        (element, attribute) = selector_map[url]['job_offers']
        job_offers = soup.find_all(element, attribute)
        for job in job_offers:
            praca = extract_job_information(job, url)
            if praca is not None:
                job_info_list.append(praca)
    return job_info_list

selector_map = {
    'jooble': {
        'job_offers': ('div', {'data-test-name': '_jobCard'}),
        'title': ('h2', {'class': 'sXM9Eq'}),
        'company': ('p', {'class': 'z6WlhX'}),
        'salary': ('p', {'class': 'W3cvaC'}),
        'location': ('div', {'class': 'caption NTRJBV'}),
        'link': ('a', {'class': 'tUC4Fj'}),
    },
    'rocketjobs': {
        'job_offers': ('div', {'data-index': True}),
        'title': ('h2', {'class': 'css-g9dzcj'}),
        'company': ('div', {'class': 'css-jx23jo'}),
        'salary': ('div', {'class': 'css-lz8wxo'}),
        'location': ('div', {'class': 'css-1wao8p8'}),
        'link': ('a', {'class': 'offer-list-offer_link'}),
    },
    'pracuj': {
        'job_offers': ('div', {'class': 'tiles_b1j1pbod core_po9665q'}),
        'title': ('a', {'class': 'tiles_o1tnn5os core_n194fgoq'}),
        'company': ('h3', {'class': 'tiles_c1rl4c7t size-caption core_t1rst47b'}),
        'salary': ('span', {'class': 'tiles_s192qrcb'}),
        'location': ('h4', {'class': 'tiles_r1h1nge7 size-caption core_t1rst47b'}),
        'link': ('a', {'class': 'tiles_c8yvgfl core_n194fgoq'}),
    }
}

async def fetch_all_content(urls):
    tasks = [get_page_content(url) for url in urls]
    return await asyncio.gather(*tasks)

def save_to_mongodb(job_info, collection):
    for title, company, salary, location, link in job_info:
        job_data = {
            "title": title,
            "company": company,
            "salary": salary,
            "location": location,
            "link": link
        }
        collection.insert_one(job_data)

async def main(keyword, location, date):
    client = pymongo.MongoClient("mongodb://mongodb:27017/")
    db = client["projekt"]
    collection = db[f'search:{keyword}, {location}, {date}']
    

    names = ['jooble', 'rocketjobs', 'pracuj']
    urls = [
        f'https://pl.jooble.org/SearchResult?rgns={location}&ukw={keyword}',
        f'https://rocketjobs.pl/{location}?keyword={keyword}',
        f'https://pracuj.pl/praca/{keyword};kw/{location};wp'
    ]

    start_time = time.time()
    page_contents = await fetch_all_content(urls)
    paired_args = list(zip(names, page_contents))
    
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        job_info_results = pool.map(parse_and_extract_job_information, paired_args)

    for job_info in job_info_results:
        print_job_info(job_info)
        save_to_mongodb(job_info, collection)
    
    end_time = time.time()
    print(f"Time: {end_time - start_time:.2f} seconds")

def check_for_signals():
    client = pymongo.MongoClient("mongodb://mongodb:27017/")
    db = client["projekt"]
    signals_collection = db["scraping_signals"]
    
    while True:
        signal = signals_collection.find_one_and_update(
            {"status": "pending"},
            {"$set": {"status": "processing"}}
        )
        if signal:
            keyword = signal["keyword"]
            location = signal["location"]
            date = signal["date"]
            if f'search:{keyword}, {location}, {date}' in db.list_collection_names():
                db[f'search:{keyword}, {location}, {date}'].delete_many({})
            asyncio.run(main(keyword, location, date))
            signals_collection.update_one({"_id": signal["_id"]}, {"$set": {"status": "completed"}})
        time.sleep(2)

if __name__ == "__main__":
    check_for_signals()
