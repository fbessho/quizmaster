from strategy.retrieval_qa_with_source import WebSearchStrategy
from strategy.simple_prompt import SimplePromptStrategy
from strategy.chat_completion import ChatCompletionStrategy
from dotenv import load_dotenv
import os
import json


load_dotenv()
__cache_dir = os.environ["CACHE_LOCATION"]

def test_simple_prompt_strategy():
    strategy = SimplePromptStrategy()
    _test_strategy(strategy)

def test_chat_completion_strategy():
    strategy = ChatCompletionStrategy()
    _test_strategy(strategy)

def _test_strategy(strategy):
    cache_dir = __cache_dir
    # Go through .json files under `cache_dir`
    total_cnt = 0
    correct_cnt = 0
    error_cnt = 0
    for filename in os.listdir(cache_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(cache_dir, filename)
            with open(filepath, encoding='utf-8') as f:
                print(f"Reading file: {filepath}")
                data = json.load(f)
                question = data["question"]
                options = data["choices"]
                if "answer" not in data:
                    print('No answer found in data')
                    continue
                answer = data["answer"]
                total_cnt += 1
                try:
                    determined_answer = strategy.determine_answer(question, options)
                except Exception as e:
                    error_cnt += 1
                    print(f"Error: {e}")
                    continue
                if determined_answer == answer:
                    correct_cnt += 1
                print(f"Question: {question}")
                print(f"Correct Answer: {answer}")
                print(f"Determined Answer: {determined_answer}")
                print(f"Options: {options}")
                print("=========================================")

    print(f"Precision: {correct_cnt:2d}/{total_cnt:2d} = {correct_cnt/total_cnt:.2f} (error={error_cnt})")
