from app.lab.scrape.scraper import Scraper
import time
import redis
import colored
from colored import stylize
import time
import sys
import json
import os


def keywordSearch(keywords, domains, end=500):
    """
    Searches based on specific keywords and specific domains.
    Returns a list of links from search results matching the keywords and domains
    """
    links = []
    scrape = Scraper()
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
                response = scrape.search(url)
                soup = scrape.parseHTML(response)
                if (not soup):
                    break

                # Extract all links
                hrefs = soup.find_all("a", href=True)

                # Begin traversing links
                links = []  # links collects
                for h in hrefs:
                    if hasattr(h, 'href'):
                        if (f"https://{domain}/" in h['href']):
                            link = scrape.stripParams(h['href'])
                            links.append(link)
        return links



def infiniteSearch(keyword, domain):
    scrape = Scraper()
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
        response = scrape.search(url)
        soup = scrape.parseHTML(response)
        if (not soup):
            break

        # Extract all links
        hrefs = soup.find_all("a", href=True)

        # Begin traversing links
        links = []  # links collects
        for h in hrefs:
            if hasattr(h, 'href'):
                if (f"https://{domain}/" in h['href']):
                    link = scrape.stripParams(h['href'])
                    links.append(link)
    return links
    