FROM python:3.8-slim
WORKDIR /fakesCreator

RUN apt update
RUN apt install default-jre libreoffice-java-common -y
RUN apt install unoconv -y
RUN apt-get update
RUN apt-get install poppler-utils
RUN apt-get install tesseract-ocr-pol -y

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

 CMD ["python3", "main.py", "--document", "training_document_0.jpg", "--type", "HospitalInformationSheet", "-n", "1", "--distort_type", "scan"]
#CMD ["python3", "main.py", "--document", "training_document_0.jpg", "--type", "HospitalInformationSheet", "-n", "1", "--distort_type", "scan", "--only_distort"]