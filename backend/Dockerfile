# use python 3.13
FROM python:alpine3.23 AS builder

# project directory
WORKDIR /app

# copy django to project directory
COPY . .

# upgrade pip
RUN pip install --upgrade pip
# update apt
#RUN apt-get update && apt-get install curl -y


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# copy required dependencies into the docker app
COPY requirements.txt /app

# install required dependecies
RUN pip install -r requirements.txt

# copy into app
COPY . /app

# copy the build file into app
COPY build.sh /app

# give permission
RUN chmod +x build.sh

# expose port
EXPOSE 8000

# entry point
CMD ["python3", "manage.py", "migrate"]




