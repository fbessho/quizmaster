import logging
import os
import subprocess

import openai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

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
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
    soup = BeautifulSoup(response.text, "html.parser")
    logger.info(soup.prettify())
    # Find the element with the id "Question"
    question_element = soup.find(id="Question")

    # Extract the text from the "Question" element
    question = question_element.get_text(strip=True)
    logger.info(question)
    if question == "No quiz today.":
        logger.info("No quiz today")
        return None, None
    # Find the table with id "quiz_question_table"
    table = soup.find("table", {"id": "quiz_question_table"})

    # Find all row elements within the table
    rows = table.find_all("tr")
    answers = []
    choices = ["A", "B", "C", "D"]
    # Iterate through the rows and logger.info their contents
    for i, row in enumerate(rows):
        # logger.info(row.prettify())
        div_element = row.find("div")
        if div_element:
            answers.append(choices[i] + ". " + div_element.get_text(strip=True))
    logger.info(answers)
    return question, answers


def get_prompt(question, answers):
    """Return the prompt for the question and answers"""
    return f"""
    {question} Give Response  as a single letter from options that answers this qu.
    # Options 
    {answers}
    """


def determine_answer(qu, answers):
    """Use ChatGPT to solve qu and return answer from answers"""
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct", prompt=get_prompt(qu, answers), temperature=1.0
    )
    logger.info(response)
    answer = response.choices[0].text
    answer = answer.strip("\n")[0]
    logger.info(answer)
    if answer not in ["A", "B", "C", "D"]:
        raise Exception("Wrong Choice! Investigate ChatGPT response...")
    return answer


def check_answer(session):
    """Check if the answer was correct by querying the website"""
    response = session.get(QUIZ_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    try:
        status = soup.find("h1", {"style": "color: #70c78b"}, text=True).get_text(
            strip=True
        )
    except Exception as e:
        logger.info(e)
        return False
    if status == "Correct!":
        return True
    return False


def sign_in():
    """Using requests to sign in to the website given by url"""
    session = requests.Session()
    response = session.get(SIGN_IN_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the authenticity token from the HTML response
    authenticity_token = soup.find("input", {"name": "authenticity_token"}).get("value")
    # # logger.info(authenticity_token)
    login_data = {
        "authenticity_token": authenticity_token,
        "user[email]": EMAIL,
        "user[password]": PASSWORD,
        "user[agree_policy]": "1",
    }

    response = session.post(SIGN_IN_URL, data=login_data)
    response = session.get(QUIZ_URL)
    qu, answers = obtain_question(response)
    prompt = get_prompt(qu, answers)
    logger.info(prompt)
    selected_answer = determine_answer(qu, answers)
    logger.info(f"Chosen Answer={selected_answer}")
    submit_quiz(session, selected_answer, response)
    if check_answer(session):
        logger.info("Answer Correct!")
        cmd = f'curl "http://{HOME_IP}:8991/message?token={TOKEN}" -F "title=[SU!] QUIZMASTER" -F "message"="Answer submitted sucessfully & is CORRECT." -F "priority=5"'
        subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    else:
        logger.info("Answer Wrong!")
        cmd = f'curl "http://{HOME_IP}:8991/message?token={TOKEN}" -F "title= [FA] QUIZMASTER" -F "message"="Submission is INCORRECT." -F "priority=5"'
        subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )


if __name__ == "__main__":
    sign_in()
