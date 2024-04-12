from enrich_places_api.cache_interface import ICache
import json
import hashlib
from math import radians, cos, sin, asin, sqrt
from datetime import datetime


class JsonFileCache(ICache):
    def __init__(self, file_path: str, file_path_cache_requests: str = ""):
        self._file_path = file_path
        self._file_path_cache_requests = file_path_cache_requests
        self._cache = list[dict]()
        self._cache_set = dict()
        self._cache_requests = set()

    def is_request_in_cache(self, latitude: float, longitude: float) -> bool:
        return self._is_request_in_cache(latitude, longitude, False)

    def get_cache(self, latitude: float, longitude: float) -> list[dict]:
        self._is_request_in_cache(latitude, longitude, True)
        relevant_places = list[dict]()
        for place in self._cache:
            if self._get_distance(latitude, longitude, float(place['geometry']['location']['lat']),
                                  float(place['geometry']['location']['lng'])) < 1:
                relevant_places.append(place)

        # print(f"{len(relevant_places)} relevant items retrieved from cache.")
        return relevant_places

    def write_to_cache(self, results: list[dict]):
        added = 0
        for result in results:
            result['cachedAt'] = datetime.today().strftime("%d-%m-%y %H:%M:%S")
            if result['reference'] not in self._cache_set:
                self._cache.append(result)
                self._cache_set[result['reference']] = len(self._cache) - 1
                added = added + 1
            else:
                cache_index = self._cache_set[result['reference']]
                self._cache[cache_index] = result

        for item in self._cache:
            item['cachedAt'] = datetime.today().strftime("%d-%m-%y %H:%M:%S")

        cache_obj = {'cache_data': self._cache}
        json_object = json.dumps(cache_obj, indent=4)
        print(f"write to cache: total items={len(self._cache)}, added={added}, ignored={len(results)-added}")
        with open(self._file_path, "w") as outfile:
            outfile.write(json_object)

    def load_cache(self):
        with open(self._file_path, "r") as file:
            json_obj = json.load(file)
            if 'cache_data' in json_obj:
                self._cache = json_obj['cache_data']
                self._cache_set = dict()
                index = 0
                for item in self._cache:
                    self._cache_set[item['reference']] = index
                    index = index + 1

            if 'cache_requests' in json_obj:
                self._cache_requests = set(json_obj['cache_requests'])

            print(f"cache loaded: {len(self._cache)}")

        self._load_cache_requests()

    def _get_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])

        diff_lng = lng2 - lng1
        diff_lat = lat2 - lat1
        a = sin(diff_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(diff_lng / 2) ** 2
        c = 2 * asin(sqrt(a))
        return c * 6372

    def _write_cache_requests(self):
        if len(self._file_path_cache_requests) == 0:
            return

        cache_obj = {'cache_requests': list(self._cache_requests)}
        json_object = json.dumps(cache_obj, indent=4)
        # print(f"write to cache requests: total items={len(self._cache_requests)}")
        with open(self._file_path_cache_requests, "w") as outfile:
            outfile.write(json_object)

    def _load_cache_requests(self):
        if len(self._file_path_cache_requests) == 0:
            return

        with open(self._file_path_cache_requests, "r") as file:
            json_obj = json.load(file)
            if 'cache_requests' in json_obj:
                self._cache_requests = set(json_obj['cache_requests'])

            print(f"cache requests loaded: {len(self._cache_requests)}")

    def _create_request_hash(self, latitude: float, longitude: float):
        h = hashlib.new('sha1', usedforsecurity=False)
        h.update(f"{latitude}_{longitude}".encode())
        return h.hexdigest()

    def _is_request_in_cache(self, latitude: float, longitude: float, add_if_not: bool) -> bool:
        request_hash = self._create_request_hash(latitude, longitude)
        if request_hash not in self._cache_requests:
            if add_if_not:
                self._cache_requests.add(request_hash)
                self._write_cache_requests()
            return False

        return True
