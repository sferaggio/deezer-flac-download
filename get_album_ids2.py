from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time

from selenium.webdriver.edge.service import Service


def get_album_info(playlist_id):
    # Step1: Try get all info from API first
    album_info = get_album_info_from_playlist(playlist_id)
    # Step2: Check through each id to make sure there is data
    for album_id, (artist_name, album_title, track_title) in album_info.copy().items():
        test = get_album_info_raw(album_id)
        if test.get("error"):
            print(f"BAD ALBUM: {album_id}")
            print(f"    artist_name: {artist_name}")
            print(f"    album_title: {album_title}")
            print(f"    track_title: {track_title}")
            del album_info[album_id]
            searched_album_info = search_album_info(track_title, artist_name)
            if searched_album_info:
                new_album_id = searched_album_info["album"]["id"]
                new_album_title = searched_album_info["album"]["title"]
                new_artist_name = searched_album_info["artist"]["name"]
                print(f'    REPLACED: {album_id} -> {new_album_id}')
                print(f'                         -> artist name: {new_artist_name}')
                print(f'                         -> album title: {new_album_title}')
                album_info[new_album_id] = (new_artist_name, new_album_title)
    return album_info

def search_album_info(track_title, artist_name=None, try_=0):
    url = "https://api.deezer.com/search?q="
    if artist_name:
        url = url + f'artist:"{artist_name}" '
    if track_title:
        url = url + f'track:"{track_title}"'
    print(f'    SEARCHING: {url}')
    with httpx.Client() as client:
        response = client.get(url)
        # We assume that the first entry is acceptable, as the closest match
        # if no match, try a more general search before moving on
        try:
            return response.json()["data"][0]
        except IndexError:
            try_ += 1
            if try_ < 3:
                return search_album_info(track_title, try_=try_)

def get_album_info_raw(album_id):
    url = f"https://api.deezer.com/album/{album_id}"
    with httpx.Client() as client:
        response = client.get(url)
        return response.json()

def get_album_info_from_playlist(playlist_id):
    url = f"https://api.deezer.com/playlist/{playlist_id}"
    with httpx.Client() as client:
        response = client.get(url)
        # NOTE: This has the added benefit of collapsing duplicate albums if the playlist contains more than 1 song from that album
        return {t["album"]["id"]: (t["artist"]["name"], t["album"]["title"], t["title"]) for t in response.json()['tracks']['data']}


def get_album_ids(url):
    # Set up the Selenium driver (make sure to specify the correct path to your driver)
    service = Service(r"msedgedriver.exe")
    options = webdriver.EdgeOptions()
    driver = webdriver.Edge(service=service, options=options)
    driver.get(url)

    # Wait for the accept button to be clickable, and then click it
    wait = WebDriverWait(driver, 10)
    accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div/div/div[2]/div[1]/button')))
    accept_button.click()

    # Give the page 30 seconds to load before scraping
    time.sleep(30)

    # Now that the page is fully scrolled, grab the HTML and use BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Find all hrefs that contain 'album/(\d+)'
    album_links = soup.find_all('a', href=re.compile(r'album/(\d+)'))
    
    # Extract the album IDs from the hrefs
    album_ids = [re.search(r'album/(\d+)', a['href']).group(1) for a in album_links]

    return album_ids

# Example usage:
url = 'https://www.deezer.com/en/playlist/12814501181'  # Replace with your URL
print(get_album_ids(url))
