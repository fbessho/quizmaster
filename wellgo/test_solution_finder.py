import pytest
from solution_finder import obtain_question, submit_quiz, check_answer, notify
from unittest.mock import Mock
import subprocess
from unittest.mock import patch
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
SIGN_IN_URL = os.getenv("SIGN_IN_URL")

QUIZ_URL = os.getenv("QUIZ_URL")
POST_ANSWER_URL = os.getenv("POST_ANSWER_URL")
TOKEN = os.getenv("TOKEN")
HOME_IP = os.getenv("HOME_IP")


# def test_obtain_question():
#     # Create a mock response object
#     response = Mock()
#     response.text = '<html><body><div id="Question">What is the capital of France?</div></body></html>'

#     # Call the function with the mock response
#     question, answers = obtain_question(response)

#     # Check that the question was extracted correctly
#     assert question == "What is the capital of France?"

#     # Check that the answers list is correct
#     assert answers == ["A", "B", "C", "D"]


def test_submit_quiz():
    # Create a mock session object
    session = Mock()

    # Create a mock response object
    response = Mock()
    response.text = '<html><body><input name="authenticity_token" value="1234567890abcdef"></body></html>'

    # Call the function with a selected answer and the mock response
    submit_quiz(session, "A", response)

    # Check that the session.post method was called with the correct data
    expected_data = {
        "authenticity_token": "1234567890abcdef",
        "quiz_answer[answer_given]": "A",
    }
    session.post.assert_called_once_with(
        "https://wellgo.jp/en/quiz_answers", data=expected_data
    )


# def test_check_answer():
#     # Create a mock session object
#     session = Mock()

#     # Create a mock response object with a correct answer
#     response = Mock()
#     response.text = '<html><body><h1 class="mb-1 h1-noti" style="color: #70c78b">Correct!</h1></body></html>'

#     # Call the function with the mock session and response
#     result = check_answer(session, response)

#     # Check that the result is True
#     assert result == True


@patch("subprocess.run")
def test_notify(mock_run):
    # Call the function with test arguments
    header = "Test Header"
    message = "Test Message"
    notify(header, message)
    # Check that subprocess.run was called with the expected command
    expected_cmd = f'curl "http://{HOME_IP}:8991/message?token={TOKEN}" -F "title=[{header}] QUIZMASTER" -F "message"="{message}" -F "priority=5"'
    mock_run.assert_called_once_with(
        expected_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
