FROM python:3.11-slim

ARG APP_USER=game\
    APP_GROUP=game\
    CODE_FOLDER=/code

RUN apt-get update && \
    apt-get upgrade -y

WORKDIR $CODE_FOLDER

RUN groupadd $APP_GROUP && \
    useradd -s /bin/bash -g $APP_GROUP $APP_USER -d $CODE_FOLDER && \
    chown -R $APP_USER:$APP_GROUP $CODE_FOLDER

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY . .

USER $APP_USER

EXPOSE 8000
CMD uvicorn main:app --reload --host 0.0.0.0 --port 8000
