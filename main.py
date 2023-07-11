from rent_search import RentSearch
from data_manager import DataManager
from notification import Notification
from datetime import timedelta

# config search places and max_price
places = [
    "helmond",
    "eindhoven",
    "veldhoven"
]
max_price = 1300

# only support below sites
urls = {
    "pararius": "https://www.pararius.com",
    "funda": "https://www.funda.nl",
}

if __name__ == "__main__":
    places = [item.lower() for item in places]
    for key, url in urls.items():
        rent_search = RentSearch(vendor=key,
                                 url=url,
                                 place_list=places,
                                 max_price=max_price,
                                 )
        rent_data = rent_search.query_renting_list()
        data_manager = DataManager(rent_data)
        history_data = data_manager.get_history_data()
        data_manager.update_new_history()
        notification = Notification(data_manager.new_df)
        notification.send_sms()
