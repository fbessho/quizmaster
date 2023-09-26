import os

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
    print(response.status_code)


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
    # Find the table with id "quiz_question_table"
    table = soup.find("table", {"id": "quiz_question_table"})

    # Find all row elements within the table
    rows = table.find_all("tr")
    answers = []
    choices = ["A", "B", "C", "D"]
    # Iterate through the rows and print their contents
    for i, row in enumerate(rows):
        # print(row.prettify())
        div_element = row.find("div")
        if div_element:
            answers.append(choices[i] + ". " + div_element.get_text(strip=True))
    print(answers)
    return question, answers


def get_prompt(question, answers):
    """Return the prompt for the question and answers"""
    return f"""
    # Available answers 
    {answers}
    
    # Question to answer
    {question}
    
    Respond with the letter from the multiple choice answer that solves the question. Give your response as a captilized letter in english only of length=1.  
    """


def determine_answer(qu, answers):
    """Use ChatGPT to solve qu and return answer from answers"""
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct", prompt=get_prompt(qu, answers), temperature=1.0
    )
    print(response)
    answer = response.choices[0].text
    answer = answer.strip("\n")[0]
    print(answer)
    if answer not in ["A", "B", "C", "D"]:
        raise Exception("Wrong Choice! Investigate ChatGPT response...")
    return answer


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
    qu, answers = obtain_question(response)
    prompt = get_prompt(qu, answers)
    print(prompt)
    selected_answer = determine_answer(qu, answers)
    print(f"Chosen Answer={selected_answer}")
    submit_quiz(session, selected_answer, response)
    print("Answer submitted!")


if __name__ == "__main__":
    sign_in()
