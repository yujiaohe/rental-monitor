import os
import pandas as pd
import requests


RENT_HISTORY = os.getenv("RENT_HISTORY")
RENT_KEY = os.getenv("RENT_KEY")


class DataManager:

    def __init__(self, rent_search_df):
        self.new_df = rent_search_df
        self.history_data = {}

    def get_history_data(self):
        headers = {
            'Authorization': RENT_KEY
        }
        response = requests.get(url=RENT_HISTORY, headers=headers)
        # print("=================History data start===============")
        # print(response.text)
        # print("=================History data end=================")

        self.history_data = response.json()["rent"]
        return self.history_data

    def update_new_history(self):
        history_df = pd.DataFrame.from_dict(self.history_data)
        history_df.columns = [item.title()
                              for item in history_df.columns.to_list()]
        if history_df.shape[0] > 0:
            for index, row in self.new_df.iterrows():
                if row.Link in history_df.Link.values:
                    self.new_df.drop(index=index, inplace=True)
            print(f"{self.new_df.shape[0]} new house(s) are founded!")
            print(f"{self.new_df}")
        headers = {
            'Authorization': f"Basic {RENT_KEY}"
        }
        for _, row in self.new_df.iterrows():
            row_dict = {key.lower(): value.replace("\n", '; ')
                        for key, value in row.to_dict().items()}
            post_data = {
                "rent": row_dict
            }
            try:
                response = requests.post(
                    url=RENT_HISTORY, json=post_data, headers=headers)

                if response.status_code == 200:
                    print("New record post successfully!")
                    # print(f"response.text\n{response.text}")
                else:
                    print(f"Error: {response.status_code, response.text}")
            except requests.RequestException as e:
                print(f"Error: {e}")
