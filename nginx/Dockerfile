FROM nginx:1.26.2

RUN apt update && apt upgrade -y

RUN rm -rf /usr/share/nginx/html/*
COPY html /usr/share/nginx/html

RUN rm -rf /etc/nginx/*
COPY conf /etc/nginx

COPY certifications /etc/nginx/certifications

CMD envsubst '$MAIN_FILE_CONF' < /etc/nginx/nginx-template.conf > /etc/nginx/nginx.conf && nginx -g 'daemon off;'