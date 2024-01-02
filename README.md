# quizmaster
Use chatGPT API to solve multiple choice questions in Japanese using bs4 for webscraping.

Submit the answer and check to see if correct. 

Use gotify to provide user alerting.

## Build
```
docker build -t quizmaster:latest .
```

## Prep
Create `wellgo/.env` based on `wellgo/.env.sample`

## Run
In PowerShell
```
docker run --rm -it  \
    -v ${PWD}/cache:/root/cache \
    -v ${PWD}/logs:/var/log/wellgo \
    -v ${PWD}/wellgo/.env:/app/wellgo/.env
    quizmaster:latest
```