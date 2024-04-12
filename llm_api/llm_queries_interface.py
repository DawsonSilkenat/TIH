from llm_api.llm_models import LLMResponse


class ILLMQueries:
    def collect_user_data(self, conversation: list[dict[str, str]]) -> LLMResponse:
        pass

    def get_keywords(self, conversation: list[dict[str, str]]) -> list[str]:
        pass

    def filter_datasets(self, conversation: list[dict[str, str]], possible_datasets: list[str]) -> list[str]:
        pass
