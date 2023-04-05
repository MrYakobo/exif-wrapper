FROM docker.io/python:3.11.2-bullseye

RUN apt-get update && apt-get install -y nodejs npm ffmpeg exiftool
RUN npm i -g yarn

COPY ./google-photos-exif /app

WORKDIR /app
RUN yarn install