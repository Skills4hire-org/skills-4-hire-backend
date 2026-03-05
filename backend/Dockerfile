# use python 3.13
FROM python:alpine3.23 AS builder

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

COPY ./backend .

EXPOSE 8000

# entry point
CMD ["uv", "run", "sh", "build.sh"]


