import time
import redis
import requests
from bs4 import BeautifulSoup
import colored
from colored import stylize
import time
import sys
import json
import os



def bingSearch(url):
    headers = {
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
    except:
        print(stylize("Unexpected error:", colored.fg("red")))
        print(stylize(sys.exc_info()[0], colored.fg("red")))
        return False

    if (response.status_code == 200):
        time.sleep(1.3)
        return response
    return response.status_code


def formatLink(link):
    if ('?' in link):
        link = link.split('?')[0]
    if ('&' in link):
        link = link.split('&')[0]
    return link


def keywordSearch(keywords, domains, end=500):
    """
    Searches based on specific keywords and specific domains.
    Returns a list of links from search results matching the keywords and domains
    """
    links = []
    for k in keywords:
        for domain in domains:
            print("\n")
            print(f"Searching {k}...")

            query = f"{k}%20site%3A{domain}"
            position = 0
            current_page = 0

            # Begin traversing pagination
            while (position < end):
                current_page = current_page + 1
                print(f"Current page: {current_page}. Position: {position}")
                url = f"https://www.bing.com/search?q={query}&first={position}"
                position = position + 11
                if ((position % 10) == 0):
                    print(stylize("Giving Bing a breath...", colored.fg("yellow")))
                    time.sleep(5)

                # Request page from pagination
                response = bingSearch(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                if (not soup):
                    break

                # Extract all links
                hrefs = soup.find_all("a", href=True)

                # Begin traversing links
                links = []  # links collects
                for h in hrefs:
                    if hasattr(h, 'href'):
                        if (f"https://{domain}/" in h['href']):
                            link = formatLink(h['href'])
                            links.append(link)
        return links



def infiniteSearch(keyword, domain):
    query = f"{keyword}%20site%3A{domain}"
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    position = r.get('bing_position') if r.get('bing_position') else 0
    links = []
    end = 100000000
    current_page = 0 if position == 0 else int(position / 11)

    # Begin traversing pagination
    while (position < end):
        current_page = current_page + 1
        print(f"Current page: {current_page}. Position: {position}")
        url = f"https://www.bing.com/search?q={query}&first={position}"
        position = position + 11
        if ((position % 10) == 0):
            print(stylize("Giving Bing a breath...", colored.fg("yellow")))
            time.sleep(5)

        # Cache the position
        r.put('bing_position', position)

        # Request page from pagination
        response = bingSearch(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        if (not soup):
            break

        # Extract all links
        hrefs = soup.find_all("a", href=True)

        # Begin traversing links
        links = []  # links collects
        for h in hrefs:
            if hasattr(h, 'href'):
                if (f"https://{domain}/" in h['href']):
                    link = formatLink(h['href'])
                    links.append(link)
    return links
    