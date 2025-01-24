FROM postgres:17.2

RUN apt update && apt upgrade -y

RUN echo "CREATE DATABASE strapi;" > /docker-entrypoint-initdb.d/init-strapi.sql