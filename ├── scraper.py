import requests
from bs4 import BeautifulSoup

def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    page = requests.get(url, headers=headers)

    soup = BeautifulSoup(page.content, "html.parser")

    price = soup.find("span", {"class":"a-price-whole"})

    title = soup.find("span", {"id":"productTitle"})

    if price and title:

        p = float(price.text.replace(",", ""))

        t = title.text.strip()

        return t, p

    return None, None
