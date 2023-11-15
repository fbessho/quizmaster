from typing import List


class BaseStrategy():
    def determine_answer(self, question: str, answers: List[str]) -> str:
        raise NotImplementedError
