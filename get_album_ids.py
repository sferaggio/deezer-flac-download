from selenium import webdriver
from bs4 import BeautifulSoup
import re
import time

def get_album_ids(url):
    # Set up the Selenium driver (make sure to specify the correct path to your driver)
    driver = webdriver.Edge(r"msedgedriver.exe")
    driver.get(url)

    # Scroll to the bottom of the page to load all hrefs
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait to load page
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

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
