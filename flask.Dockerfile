# pull official base image
FROM python:3.9.18-slim-bullseye

# set work directory
WORKDIR /usr/src/flask

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/flask/requirements.txt
RUN pip install -r requirements.txt
