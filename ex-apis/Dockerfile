FROM python:3.12.8

WORKDIR /root/app

RUN apt update && apt upgrade -y

COPY app /root/app
COPY requirements.txt /root/app

RUN pip install --upgrade pip && pip install -r requirements.txt && rm requirements.txt

CMD python3 main.py