FROM python:3.12-slim

ARG ENVIRONMENT="production"

WORKDIR /app

COPY requirements.txt .

# setting timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && apt-get clean\
    && pip install "poetry==$POETRY_VERSION"

WORKDIR /var/install/api
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

COPY ./app/ /var/install/api/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
