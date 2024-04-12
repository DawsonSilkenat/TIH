import requests
import datetime
from enrich_places_api.places_lookup_google import IPlacesLookup


class TIHAPI:
    def __init__(self, tih_api_key: str,  places: IPlacesLookup, max_cache_age: int = 300):
        self._tih_api_key = tih_api_key
        self._places = places
        self._datasets_cache = list[str]()
        self._datasets_cache_time = None
        self._max_cache_age = max_cache_age

    def multiple_datasets_by_keywords(self, datasets: list[str], keywords: list[str], limit: int,
                                      start_date: datetime, end_date: datetime, expected_result_count: int = 25)\
            -> list[dict[str, any]]:
        valid_responses = list[dict[str, any]]()

        offset = 0
        while len(valid_responses) < expected_result_count:
            api_response = self._request_from_api(datasets, keywords, limit, offset, start_date, end_date)
            if 'events' in datasets:
                return api_response

            offset = offset + limit
            for item in api_response:
                block, street = self._get_tih_address_data(item)
                if self._is_matching_google_rating_filter(item['name'], block, street,
                                                          float(item['location']['latitude']),
                                                          float(item['location']['longitude'])):
                    print(f"hidden gem :{item['name']}")
                    valid_responses.append(item)
                    if len(valid_responses) >= expected_result_count:
                        return valid_responses

            if len(api_response) < limit:
                return valid_responses

        return valid_responses

    def get_datasets(self) -> list[str]:
        if self._datasets_cache_time is None or (datetime.datetime.now() - self._datasets_cache_time).seconds > self._max_cache_age:
            self._datasets_cache = self._request_dataset_list()
            self._datasets_cache_time = datetime.datetime.now()
            print("dataset cache refreshed")

        return self._datasets_cache

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

        url = "https://api.stb.gov.sg/content/common/v2/datasets"
        headers = {
            "X-API-Key": self._tih_api_key,
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json().get("data")
        response.raise_for_status()

    def _is_matching_google_rating_filter(self, name: str, block: str, street_name: str, latitude: float,
                                          longitude: float, max_rating_count: int = 500, minimum_rating: float = 3.0):
        # ignore restaurant that have not a valid location
        if float(latitude) == 0.0 and float(longitude) == 0.0:
            return False

        print(f"check google or cache for: {name} {block} {latitude} {longitude}")
        google_place_result = self._places.find_place(name, block, street_name, latitude, longitude)
        if google_place_result is not None:
            rating_count = google_place_result['user_ratings_total']
            rating = google_place_result['rating']
            operational = google_place_result['business_status'] == 'OPERATIONAL'
            return (operational and rating_count < max_rating_count and rating >= minimum_rating) or rating_count <= 0
        else:
            print(f"Resturant {name}, {block}, {street_name}, {latitude}, {longitude} couldn't be found")

        return False

    def _request_from_api(self, datasets: list[str], keywords: list[str], limit: int, offset: int,
                          start_date: datetime, end_date: datetime, offset_days: int = 5) -> list[dict[str, any]]:
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
            query["startDate"] = (start_date-datetime.timedelta(days=offset_days)).today().strftime('%Y-%m-%d')
            query["endDate"] = (end_date+datetime.timedelta(days=offset_days)).today().strftime('%Y-%m-%d')

        response = requests.get(url, headers=headers, params=query)

        if response.status_code == 200:
            return response.json()["data"]
        response.raise_for_status()
