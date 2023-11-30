from typing import List


class BaseStrategy():
    def determine_answer(self, question: str, choices: List[str]) -> str:
        raise NotImplementedError
