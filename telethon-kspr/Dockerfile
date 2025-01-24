FROM python:3.12.8

WORKDIR /root/app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN apt update && apt upgrade -y

COPY app .
RUN rm requirements.txt

CMD python3 main.py