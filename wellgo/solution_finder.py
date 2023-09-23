import requests
from bs4 import BeautifulSoup
import openai
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
SIGN_IN_URL = os.getenv("SIGN_IN_URL")

QUIZ_URL = os.getenv("QUIZ_URL")
POST_ANSWER_URL = os.getenv("POST_ANSWER_URL")
API_KEY = os.getenv("API_KEY")


def submit_quiz(session, selected_answer: str, response: requests.Response):
    """Given a selected_answer submit to the session the answer, obtaining the authenticity_token from the response"""
    soup = BeautifulSoup(response.text, "html.parser")
    # Prepare the data for the POST request
    authenticity_token = soup.find("input", {"name": "authenticity_token"})
    authenticity_token = authenticity_token["value"]

    print(authenticity_token)

    quiz_data = {
        "authenticity_token": authenticity_token,
        "quiz_answer[answer_given]": selected_answer,
    }

    response = session.post(POST_ANSWER_URL, data=quiz_data)
    # print(response.status_code)


def obtain_question(response):
    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.prettify())
    # Find the element with the id "Question"
    question_element = soup.find(id="Question")

    # Extract the text from the "Question" element
    question = question_element.get_text(strip=True)
    print(question)
    if question == "No quiz today.":
        print("No quiz today")
        return None, None
    # TODO get answers from the response
    answers = ["A", "B", "C", "D"]
    return question, answers


def get_prompt(question, answers):
    """Return the prompt for the question and answers"""
    return """
    # Available answers 
    {answers}
    
    # Question to answer
    {question}
    
    # Respond with the letter from the multiple choice answer that solves the question
    
    """


def determine_answer(qu, answers):
    """Use ChatGPT to solve qu and return answer from answers"""
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct", prompt=get_prompt(qu, answers), temperature=1.0
    )
    return response


def sign_in():
    """Using requests to sign in to the website given by url"""
    session = requests.Session()
    response = session.get(SIGN_IN_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the authenticity token from the HTML response
    authenticity_token = soup.find("input", {"name": "authenticity_token"}).get("value")
    # # print(authenticity_token)
    login_data = {
        "authenticity_token": authenticity_token,
        "user[email]": EMAIL,
        "user[password]": PASSWORD,
        "user[agree_policy]": "1",
    }

    response = session.post(SIGN_IN_URL, data=login_data)
    response = session.get(QUIZ_URL)
    qu, anwers = obtain_question(response)
    # selected_answer = determine_answer(qu, anwers)

    # submit_quiz(session, selected_answer, response)

    # print(response.text)
    # soup = BeautifulSoup(response.content, "html.parser")
    # print(soup.prettify())
    # Check if the login was successful (by examining the response content or status code)
    # if "Welcome" in response.text:
    #     print("Login Successful")
    # else:
    #     print("Login Failed")


if __name__ == "__main__":
    sign_in()
