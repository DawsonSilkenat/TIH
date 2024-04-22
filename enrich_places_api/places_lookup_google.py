import googlemaps
import time

from enrich_places_api.cache_interface import ICache
from enrich_places_api.places_lookup_interface import IPlacesLookup
from difflib import SequenceMatcher


class GooglePlacesLookup(IPlacesLookup):
    def __init__(self, api_key, cache: ICache):
        self._cache = cache
        self._cache.load_cache()
        if api_key and not api_key.isspace():
            self._client = googlemaps.Client(key=api_key)
        else:
            self._client = None

    def find_place(self, place: str, block: str, street_name: str, latitude: float, longitude: float) -> dict | None:
        already_searched = self._cache.is_request_in_cache(latitude, longitude)
        results = self._cache.get_cache(latitude, longitude)
        if results is not None and len(results) > 0:
            #print(f"data collected from cache: {results}")
            found_place = self._filter_place(place, block, street_name, results)
            if found_place is not None:
                return found_place

        if already_searched:
            #TODO check cache age and invalidate, if to old query google again (code below)
            return None

        # API Key not set therefore only the data cache is used
        if self._client is None:
            return None

        print("Data not found in caching retrieving data from google...")
        results = self._collect_data(place, latitude, longitude)
        return self._filter_place(place, block, street_name, results)

    def _filter_place(self, place: str, block: str, street_name: str, results: list[dict]) -> dict | None:
        for result in results:
            google_address_parts = result['formatted_address'].split(' ', 1)

            if self._block_filter(block, google_address_parts[0]):
                continue

            if self._name_filter(place, result['name']):
                continue

            # Street names are too different since google uses a lots of abbreviations
            # For example Google abbreviates 'east coast parkway' with 'ecp'
            if self._street_filter(street_name, google_address_parts[1].split(',')[0]):
                continue

            #print(f"match found: {result}")
            return result

        return None

    def _name_filter(self, tih_name: str, google_name: str) -> bool:
        google_name = google_name.strip().lower()
        tih_name = tih_name.strip().lower()

        # contains check for cases such as the following:
        # google name=the landing point
        # tih name=the landing point, the fullerton bay hotel singapore
        if google_name != tih_name and google_name not in tih_name and tih_name not in google_name:
            # print(f"Names do not match: google name={google_name}, tih name={tih_name}")
            similarity_name = SequenceMatcher(None, google_name, tih_name).ratio()
            # print(f"Name similarity ratio: {similarity_name}")

            # 0.5 magic ratio I don't if is a good choice or not.
            if similarity_name < 0.5:
                return True

        return False

    def _street_filter(self, tih_street_name: str, google_street_name: str) -> bool:
        # google abbreviate 'road' with 'rd' and 'street' with 'st'. TIH normally doesn't abbreviate these words
        # while TIH uses 'street' and 'road' normally I do the replacement too just to be sure
        google_street_name = (google_street_name.strip().lower()
                              .replace(" st", " street").replace(" rd", " road"))
        tih_street_name = (tih_street_name.strip().lower()
                           .replace(" st", " street").replace(" rd", " road"))

        # google abbreviates a lot of with the first characters of each word
        tih_abbreviation = ""
        for word in tih_street_name.split(' '):
            if len(word) > 0:
                tih_abbreviation = tih_abbreviation + word[0]

        if google_street_name != tih_street_name and tih_abbreviation != google_street_name:
            similarity_street = SequenceMatcher(None, google_street_name, tih_street_name).ratio()

            # 0.8 magic ratio I don't if is a good choice or not.
            if similarity_street < 0.8:
                # print(f"street name do not match: google={google_street_name}, tih={tih_street_name}")
                # print(f"street similarity ratio: {similarity_street}")
                return True

        return False

    def _block_filter(self, tih_block: str, google_block: str) -> bool:
        google_block = google_block.strip()
        tih_block = tih_block.strip()

        #ignore filter if we don't have to block data
        if len(tih_block) == 0:
            return False

        if google_block != tih_block:
            #print(f"skipped blocks not equal: google block={google_block}, tih block={tih_block}")
            return True

        return False

    def _collect_data(self, place: str, latitude: float, longitude: float, next_page=None) -> list[dict]:
        places_result = self._client.places(query=place, location={'lat': latitude, 'lng': longitude}, radius=1000,
                                            page_token=next_page)
        results = places_result['results']
        self._cache.write_to_cache(results)
        if 'next_page_token' in places_result:
            # The token becomes valid after an unspecified delay. 2 seconds seem to work reliable
            # for more information see: https://developers.google.com/maps/documentation/places/web-service/search-text
            time.sleep(2)
            results.extend(self._collect_data(place, latitude, longitude, places_result['next_page_token']))

        return results
