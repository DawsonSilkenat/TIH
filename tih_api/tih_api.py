import requests
import datetime
import json
from enrich_places_api.places_lookup_google import IPlacesLookup
import time

class TIHAPI:
    def __init__(self, tih_api_key: str,  places: IPlacesLookup, dataset_cache_file_path: str, max_cache_age: int = 6000):
        self._tih_api_key = tih_api_key
        self._places = places
        self._datasets_cache = list[str]()
        self._datasets_cache_time = None
        self._max_cache_age = max_cache_age
        self._dataset_cache_file_path = dataset_cache_file_path
        self._hidden_gem_dataset_type_filter = ['food_beverages', 'bars_clubs', 'shops', 'attractions']
        self._read_dataset_cache()

    def multiple_datasets_by_keywords(self, datasets: list[str], keywords: list[str], limit: int,
                                      start_date: datetime, end_date: datetime, expected_result_count: int = 10)\
            -> list[dict[str, any]]:
        valid_responses = list[dict[str, any]]()

        offset = 0
        needs_hidden_gem_filter = any(item in datasets for item in self._hidden_gem_dataset_type_filter)
        while len(valid_responses) < expected_result_count:
            api_response = self._request_from_api(datasets, keywords, limit, offset, start_date, end_date)
            self._enrich_with_google_data(api_response)

            # if we don't need to apply the hidden gem filter the data just return the data.
            if not needs_hidden_gem_filter:
                for item in api_response:
                    if 'google_data' in item:
                        valid_responses.append(item)
            else:
                self._check_for_hidden_gems(api_response, valid_responses, expected_result_count)

            if len(api_response) < limit:
                return valid_responses

            offset = offset + limit

        return valid_responses

    def get_datasets(self) -> list[str]:
        if self._datasets_cache_time is None or (datetime.datetime.now() - self._datasets_cache_time).seconds > self._max_cache_age:
            self._datasets_cache = self._request_dataset_list()
            self._datasets_cache_time = datetime.datetime.now()
            print("dataset cache refreshed")
            print(self._datasets_cache)
            self._write_dataset_cache()

        return self._datasets_cache

    def _check_for_hidden_gems(self, api_response: list[dict[str, any]], valid_responses: list[dict[str, any]],
                               expected_result_count: int):
        for item in api_response:
            if self._is_matching_google_rating_filter(item):
                print(f"hidden gem :{item['name']}")
                valid_responses.append(item)
                if len(valid_responses) >= expected_result_count:
                    return valid_responses

    def _get_tih_address_data(self, item) -> (str, str):
        if len(item['address']['block'].strip()) == 0:
            street_parts = item['address']['streetName'].split(' ', 1)
            if street_parts[0].isnumeric():
                return street_parts[0],  street_parts[1]

        return item['address']['block'], item['address']['streetName']

    def _request_dataset_list(self) -> list[str]:
        """Use the TIH api to fetch the list of possible datasets

        Args:
            tih_api_key (str): The user's TIH api key, under which the queries will be conducted

        Returns:
            list[str]: the list of available datasets
        """
        start = time.time()
        url = "https://api.stb.gov.sg/content/common/v2/datasets"
        headers = {
            "X-API-Key": self._tih_api_key,
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        end = time.time()
        print(f"fetching datasets request took {end - start} seconds")
        if response.status_code == 200:
            return response.json().get("data")
        response.raise_for_status()

    def _is_matching_google_rating_filter(self, item, max_rating_count: int = 500, minimum_rating: float = 3.0):
        if 'google_data' not in item:
            return False

        google_place_result = item['google_data']
        rating_count = google_place_result['user_ratings_total']
        rating = google_place_result['rating']
        operational = google_place_result['business_status'] == 'OPERATIONAL'
        return (operational and rating_count < max_rating_count and rating >= minimum_rating) or rating_count <= 10

    def _enrich_with_google_data(self, api_response):
        start = time.time()
        for item in api_response:
            block, street = self._get_tih_address_data(item)
            google_data = self._enrich_data(item['name'], block, street, float(item['location']['latitude']),
                                            float(item['location']['longitude']))
            if google_data is not None:
                item['google_data'] = google_data

        end = time.time()
        print(f"Enriching with google data took {end - start} seconds")

    def _enrich_data(self, name: str, block: str, street_name: str, latitude: float, longitude: float):
        if float(latitude) == 0.0 and float(longitude) == 0.0:
            print(f"{name} has a invalid geo location in tih.")
            return None

        return self._places.find_place(name, block, street_name, latitude, longitude)

    def _request_from_api(self, datasets: list[str], keywords: list[str], limit: int, offset: int,
                          start_date: datetime, end_date: datetime, offset_days: int = 5) -> list[dict[str, any]]:
        start = time.time()
        url = "https://api.stb.gov.sg/content/common/v2/search"
        headers = {
            "X-API-Key": self._tih_api_key,
            "Content-Type": "application/json",
            "X-Content-Language": "en"
        }

        query = {
            "dataset": ", ".join(datasets),
            "distinct": "Yes",
            "limit": limit,
            "offset": offset,
            "keyword": ", ".join(keywords)
        }

        # If setting start and end date to datasets that do not provide these fields 0 items are returned.
        # Therefore, only apply for events
        if 'events' in datasets and start_date is not None and end_date is not None:
            query["startDate"] = (start_date-datetime.timedelta(days=offset_days)).strftime('%Y-%m-%d')
            query["endDate"] = (end_date+datetime.timedelta(days=offset_days)).strftime('%Y-%m-%d')

        response = requests.get(url, headers=headers, params=query)
        end = time.time()
        print(f"Fetching tih data took {end - start} seconds")
        if response.status_code == 200:
            return response.json()["data"]
        response.raise_for_status()

    def _write_dataset_cache(self):
        cache_obj = {'cache_data': self._datasets_cache, 'cachedAt': datetime.datetime.today().strftime("%d-%m-%y %H:%M:%S")}
        json_object = json.dumps(cache_obj, indent=4)
        with open(self._dataset_cache_file_path, "w") as outfile:
            outfile.write(json_object)

    def _read_dataset_cache(self):
        with open(self._dataset_cache_file_path, "r") as file:
            json_obj = json.load(file)
            if 'cache_data' in json_obj:
                self._datasets_cache = json_obj['cache_data']
                self._datasets_cache_time = datetime.datetime.strptime(json_obj['cachedAt'], '%d-%m-%y %H:%M:%S')
