class ICache:
    def is_request_in_cache(self, latitude: float, longitude: float) -> bool:
        pass

    def get_cache(self, latitude: float, longitude: float) -> list[dict]:
        pass

    def write_to_cache(self, results: list[dict]):
        pass

    def load_cache(self):
        pass
