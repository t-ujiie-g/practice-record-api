FROM python:3.11

WORKDIR /app
COPY /api/practice_record_api/requirements.txt ./
COPY /api/wait-for-it.sh ./
COPY .env ./

RUN apt-get update
RUN apt-get install -y netcat-openbsd
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache
