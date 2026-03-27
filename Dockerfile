# use python 3.13
FROM python:3.12-slim AS builder

# project directory
WORKDIR /app

# update apt
RUN apt-get update && apt-get install curl -y

# install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./pyproject.toml ./uv.lock ./build.sh  ./

RUN uv sync --frozen --no-cache --no-dev

Run chmod +x build.sh

COPY . .

EXPOSE 8000




