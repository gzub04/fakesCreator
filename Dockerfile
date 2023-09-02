FROM python:3.8-slim
WORKDIR /fakesCreator

RUN apt update
RUN apt install default-jre libreoffice-java-common -y
RUN apt install unoconv -y
RUN apt install tesseract-ocr -y
RUN apt-get update
RUN apt-get install poppler-utils

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py", "--document", "training_document_0.jpg", "--type", "HospitalInformationSheet", "-n", "5", "--distort_type", "scan"]