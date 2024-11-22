FROM python:3.12-slim

ARG ENVIRONMENT="production"

ENV DEBIAN_FRONTEND=noninteractive \
  TZ=Europe/Moscow \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONPATH=/var/install/api/src \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_VERSION=1.8.4 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry'

# setting timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update \
    && apt-get install --no-install-recommends -y  \
        python3-distutils \
        python3-dev \
        python3-setuptools \
        curl \
        build-essential \
        libpq-dev \
        python3-apt \
    && apt-get clean

# Установка pip и poetry
RUN python -m ensurepip --upgrade \
    && python -m pip install --upgrade pip \
    && pip install "poetry==$POETRY_VERSION"

WORKDIR /var/install/api

# Копируем файлы зависимостей
COPY ./pyproject.toml ./poetry.lock /var/install/api/

# Project initialization:
RUN echo "$ENVIRONMENT" \
    && poetry --version \
    # Generating requirements.txt
    && poetry export --without-hashes -f requirements.txt -o /var/install/requirements.txt \
    && poetry install \
        $(if [ "$ENVIRONMENT" = 'production' ]; then echo '--no-dev'; fi) \
        --no-interaction --no-ansi \
        # Do not install the root package (the current project)
        --no-root \
    # Cleaning poetry installation's cache for production:
    && if [ "$ENVIRONMENT" = 'production' ]; then rm -rf "$POETRY_CACHE_DIR"; fi

# Setting up proper permissions:
RUN groupadd -r web \
    && useradd -d /var/install/api -r -g web web \
    && chown web:web -R /var/install/api

USER web


COPY ./src/ /var/install/api/src/

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
