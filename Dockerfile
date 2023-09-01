FROM python:3.8-slim
WORKDIR /fakesCreator

RUN apt update
RUN apt install default-jre libreoffice-java-common -y
RUN apt install unoconv -y
RUN apt-get update
RUN apt-get install poppler-utils

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]