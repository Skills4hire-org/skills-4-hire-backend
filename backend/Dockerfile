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

# copy into app
COPY . /app

# copy the build file into app
COPY build.sh /app

# give permission
RUN chmod +x build.sh

# expose port
EXPOSE 8000

# entry point
CMD ["sh", "build.sh"]


