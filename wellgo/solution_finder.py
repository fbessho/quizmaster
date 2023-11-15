import datetime
import logging
import os
import subprocess
import json
from logging.handlers import RotatingFileHandler

import openai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from strategy.retrieval_qa_with_source import WebSearchStrategy
from strategy import BaseStrategy
from strategy.simple_prompt import SimplePromptStrategy

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
SIGN_IN_URL = os.getenv("SIGN_IN_URL")

QUIZ_URL = os.getenv("QUIZ_URL")
POST_ANSWER_URL = os.getenv("POST_ANSWER_URL")
openai.api_key = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv("TOKEN")
HOME_IP = os.getenv("HOME_IP")

log_file = os.getenv("LOG_LOCATION")

handler = RotatingFileHandler(
    log_file,
    maxBytes=1024 * 1024,
    backupCount=5,
)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %Z",
)
handler.setFormatter(formatter)

# Create a StreamHandler to log messages to the terminal
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S %Z"
    )
)
# Get the root logger and add the stream handler
logger = logging.getLogger()
logger.addHandler(stream_handler)
logger.addHandler(handler)

should_roll_over = os.path.isfile(log_file)
if should_roll_over:  # log already exists, roll over!
    handler.doRollover()

logger.setLevel(logging.INFO)


def submit_quiz(session, selected_answer: str, response: requests.Response):
    """Given a selected_answer submit to the session the answer, obtaining the authenticity_token from the response"""
    soup = BeautifulSoup(response.text, "html.parser")
    # Prepare the data for the POST request
    authenticity_token = soup.find("input", {"name": "authenticity_token"})
    authenticity_token = authenticity_token["value"]

    logger.info(authenticity_token)

    quiz_data = {
        "authenticity_token": authenticity_token,
        "quiz_answer[answer_given]": selected_answer,
    }

    response = session.post(POST_ANSWER_URL, data=quiz_data)
    logger.info(response.status_code)


def obtain_question(response):
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        logger.debug(soup.prettify())
        # Find the element with the id "Question"
        question_element = soup.find(id="Question")

        # Extract the text from the "Question" element
        question = question_element.get_text(strip=True)
        logger.info(question)
        if question == "No quiz today.":
            return None, None
        # Find the table with id "quiz_question_table"
        table = soup.find("table", {"id": "quiz_question_table"})

        # Find all row elements within the table
        rows = table.find_all("tr")
        answers = []
        choices = ["A", "B", "C", "D"]
        # Iterate through the rows and logger.info their contents
        for i, row in enumerate(rows):
            div_element = row.find("div")
            if div_element:
                answers.append(choices[i] + ". " + div_element.get_text(strip=True))
        logger.info(answers)
    except Exception as e:
        logger.info("Error in obtaining question and answers, getting from cache instead")
        data = json.load(open(f"wellgo/cache/{datetime.date.today()}.json", 'r', encoding='utf-8'))
        question = data['question']
        answers = data['answers']
    return question, answers


def get_prompt(question, answers, snippets):
    """Return the prompt for the question and answers"""
    return f"""
    Give response as a single letter from options that answers this question. User given Google Search Results to determine the answer.
    # Question
    {question}
    # Options 
    {answers}
    # Google Search Results
    {snippets}
    """

def get_google_prompt(question):
    return f"""
    Give a Japanese search query in Japanese to answer the following question.

    # Question
    {question}
    """

def get_search_result(question):
    params = {
        'key': os.getenv('GOOGLE_API_KEY'),
        'cx': os.getenv('GOOGLE_CX'),
        'q': question,
    }
    r = requests.get('https://customsearch.googleapis.com/customsearch/v1', params=params)
    actual_url = r.url
    # logger.info(f'URL called: {actual_url}')    
    # logger.info(r.json())
    snippets = [x['snippet'] for x in r.json()['items']]
    return '\n\n'.join(snippets)


def check_answer(session):
    """Check if the answer was correct by querying the website"""
    response = session.get(QUIZ_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    try:
        status = soup.find("h1", {"style": "color: #70c78b"}, string=True).get_text(
            strip=True
        )
    except Exception as e:
        logger.exception(e)
        return False
    if status == "Correct!":
        return True
    return False


def notify(header, message):
    logger.info(f"Sending notification {header} {message}")
    # cmd = f'curl "http://{HOME_IP}:8991/message?token={TOKEN}" -F "title=[{header}] QUIZMASTER" -F "message"="{message}" -F "priority=5"'
    # subprocess.run(
    #     cmd,
    #     shell=True,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True,
    #     check=True,
    # )


def run(strategy: BaseStrategy, dry_run=False):
    """Using requests to sign in to the website given by url"""
    logger.info(f'Running quiz extraction for date {datetime.date.today()}')
    # Sign in
    session = requests.Session()
    response = session.get(SIGN_IN_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    authenticity_token = soup.find("input", {"name": "authenticity_token"}).get("value")
    login_data = {
        "authenticity_token": authenticity_token,
        "user[email]": EMAIL,
        "user[password]": PASSWORD,
        "user[agree_policy]": "1",
    }

    response = session.post(SIGN_IN_URL, data=login_data)

    # Get todays question and answer
    response = session.get(QUIZ_URL)
    qu, answers = obtain_question(response)
    if qu is None and answers is None:
        logger.info("No quiz today")
        notify("SU", "No quiz today")
        return
    
    # Save the question and answers to a JSON file
    data = {"date": f"{datetime.date.today()}", "question": qu, "answers": answers}
    json.dump(data, open(f"wellgo/cache/{datetime.date.today()}.json", 'w', encoding='utf-8'), ensure_ascii=False)

    # Determine the answer
    selected_answer = strategy.determine_answer(qu, answers)
    logger.info(f"Chosen Answer={selected_answer}")

    # Submit the answer
    if dry_run:
        logger.info("Dry Run, not submitting answer")
    else:
        submit_quiz(session, selected_answer, response)
        if check_answer(session):
            logger.info("Answer Correct!")
            notify("SU", "Answer submitted sucessfully & is CORRECT.")
        else:
            logger.info("Answer Wrong!")
            notify("**FA**", "Submission is INCORRECT.")


if __name__ == "__main__":
    try:
        strategy = WebSearchStrategy()
        # strategy = SimplePromptStrategy()
        run(
            strategy=strategy,
            dry_run=False
        )
    except Exception as e:
        logger.exception(str(e))
        notify("EXC", str(e))
