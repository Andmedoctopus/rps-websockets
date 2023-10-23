FROM python:3.11-slim

ARG APP_USER=game\
    APP_GROUP=game\
    CODE_FOLDER=/code


RUN apt update && \
    apt upgrade -y && \
    apt install -y curl


WORKDIR $CODE_FOLDER

RUN groupadd $APP_GROUP && \
    useradd -s /bin/bash -g $APP_GROUP $APP_USER -m && \
    chown -R $APP_USER:$APP_GROUP $CODE_FOLDER


USER $APP_USER
ENV PATH=${PATH}:/home/$APP_USER/.local/bin \
    PYTHONPATH=${CODE_FOLDER}

RUN pip install -U pip && pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && poetry install

COPY index.html .

COPY ./rps rps/
COPY ./tests tests/


COPY entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

CMD ["uvicorn", "rps.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--reload-dir", "rps"]
