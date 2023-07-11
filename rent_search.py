import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from deep_translator import GoogleTranslator

PATTERN = r'[^.?!]*(?:including|excluding|excl\.|period|deposit)[^.?!]*[.?!]'
WEB_CONFIG = {
    "pararius": {
        "query_link": "{url}/apartments/{place}/0-{max_price}",
        "selector": "li h2 a",
    },
    "funda": {
        "query_link": "{url}/en/huur/1-dag/{place}/0-{max_price}",
        "selector": "ol li div.search-result__header-title-col a",
    }
}


class RentSearch:

    def __init__(self, vendor, url, place_list, max_price):
        self.config = WEB_CONFIG[vendor]
        self.url = url
        self.places = [item.lower() for item in place_list]
        self.max_price = max_price
        self.house_data = pd.DataFrame(columns=['Place', 'Title', 'Location', 'Price', 'Adunit', 'Offeredsince',
                                                'Available', 'Duration', 'Energy', 'Service', 'Otherinfo', 'Link'])

    def query_renting_list(self):
        if "pararius" in self.url:
            return self.query_renting_list_pararius()
        elif "funda" in self.url:
            return self.query_renting_list_funda()

    def query_renting_list_funda(self):
        for place in self.places:
            query_url = self.config['query_link'].format(url=self.url,
                                                         place=place,
                                                         max_price=self.max_price)
            headers = {
                'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
                'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/111.0.0.0 Safari/537.36"
            }
            response = requests.get(url=query_url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            all_links = soup.select(selector=self.config["selector"])
            links = list(
                set([f"{self.url}{item.get('href')}" for item in all_links]))

            for index in range(0, len(links)):
                link = links[index]
                response = requests.get(link, headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")
                # parse rent data
                # title/location/price/ad_unit can be parsed based on name and class
                title = self.process(
                    soup, name="span", class_name="object-header__title")
                location = self.process(
                    soup, name="span", class_name="object-header__subtitle")
                price = self.process(soup, name="dd",
                                     class_name="fd-flex--bp-m")
                ad_unit = self.process(soup, name="ul",
                                       class_name="kenmerken-highlighted__list")
                # offered_since always today as it is configed in query url
                offered_since = datetime.today().strftime("%d-%m-%Y")
                # available/duration parsed from selector
                all_keys = soup.select(selector="dl.object-kenmerken-list dt")
                keys = [item.text.strip().replace("\n", "; ")
                        for item in all_keys]
                keys.remove("Deposit")
                values = [item.text.strip().replace("\n", "; ")
                          for item in soup.select(selector="dd span")]
                dict_data = dict(zip(keys, values))
                available = dict_data.get("Acceptance")
                duration = dict_data.get("Rental agreement")
                # energy/service/other_info based on name and class
                energy = self.process(
                    soup, name="span", class_name="energielabel")
                service = self.process(
                    soup, name="dd", class_name="listing-features__description--service_costs")
                description = self.process(
                    soup, name="div", class_name="object-description-body")
                description = description.replace("\n", ".").lower()
                # description need to be translated from nl to en for funda
                translator = GoogleTranslator(source="auto", target="en")
                translated = translator.translate(description)
                other_info = re.findall(PATTERN, translated)
                other_info = "; ".join(other_info).strip()
                # no need to check since_list, as query is today's data
                new_row = {
                    "Place": place.title(),
                    "Title": title,
                    "Location": location,
                    "Price": price,
                    "Adunit": ad_unit,
                    "Offeredsince": offered_since,
                    "Available": available,
                    "Duration": duration,
                    "Energy": energy,
                    "Service": service,
                    "Otherinfo": other_info,
                    "Link": link
                }
                self.house_data = pd.concat([self.house_data, pd.DataFrame(new_row, index=[index])],
                                            ignore_index=True)
        return self.house_data

    def query_renting_list_pararius(self):
        for place in self.places:
            # response = requests.get(f"{self.url}/apartments/{place}/0-{self.max_price}")
            query_url = self.config['query_link'].format(url=self.url,
                                                         place=place,
                                                         max_price=self.max_price)
            headers = {
                'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
                'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/111.0.0.0 Safari/537.36"
            }
            response = requests.get(url=query_url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            all_links = soup.select(selector=self.config['selector'])
            links = list(
                set([f"{self.url}{item.get('href')}" for item in all_links]))

            for index in range(0, len(links)):
                link = links[index]
                response = requests.get(link)
                soup = BeautifulSoup(response.text, "html.parser")
                # parse rent data
                title = self.process(
                    soup, name="h1", class_name="listing-detail-summary__title")
                title = title.replace("For rent:", "").strip()
                location = self.process(
                    soup, name="div", class_name="listing-detail-summary__location")
                price = self.process(soup, name="dd",
                                     class_name="listing-features__description--for_rent_price")
                # ['€995 per month', 'Includes: Service costs']
                ad_unit = self.process(soup, name="div",
                                       class_name="listing-detail-summary__illustrated-features")
                # ['45 m²', '2 rooms', 'Furnished']
                offered_since = self.process(
                    soup, name="dd", class_name="listing-features__description--offered_since")
                available = self.process(
                    soup, name="dd", class_name="listing-features__description--acceptance")
                duration = self.process(soup, name="dd", class_name="listing-features__description"
                                                                    "--contract_duration_min_max")
                energy = self.process(
                    soup, name="dd", class_name="listing-features__description--energy-label-c")
                service = self.process(
                    soup, name="dd", class_name="listing-features__description--service_costs")
                description = self.process(
                    soup, name="div", class_name="listing-detail-description__content")
                description = description.replace("\n", ".").lower()
                other_info = re.findall(PATTERN, description)
                other_info = "; ".join(other_info).strip()
                # check if the latest one
                if datetime.today().strftime("%d-%m-%Y") == offered_since:
                    new_row = {
                        "Place": place.title(),
                        "Title": title,
                        "Location": location,
                        "Price": price,
                        "Adunit": ad_unit,
                        "Offeredsince": offered_since,
                        "Available": available,
                        "Duration": duration,
                        "Energy": energy,
                        "Service": service,
                        "Otherinfo": other_info,
                        "Link": link
                    }
                    self.house_data = pd.concat([self.house_data, pd.DataFrame(new_row, index=[index])],
                                                ignore_index=True)
        return self.house_data

    @staticmethod
    def process(soup, name, class_name):
        result = soup.find(name=name, class_=class_name)
        if result:
            return result.text.strip().replace("\n", "; ")
        else:
            return ""
