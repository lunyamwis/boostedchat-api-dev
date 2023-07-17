FROM python:3.11-slim

RUN python -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

COPY . .
