# FROM ubuntu:22.04
FROM python:3.11

COPY ./wellgo/requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

WORKDIR /app/wellgo
COPY wellgo/ /app/wellgo

CMD ["python", "solution_finder.py"]
