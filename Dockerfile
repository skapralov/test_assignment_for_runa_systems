FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PROJECT_PATH /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat \
    && rm -rf /var/lib/apt/lists/*

COPY . ${PROJECT_PATH}
WORKDIR ${PROJECT_PATH}

RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install --system

RUN chmod +x ./entrypoint.sh
ENTRYPOINT ./entrypoint.sh