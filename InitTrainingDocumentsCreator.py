from docx import Document
from random import randint


INPUT_FILE = "Data/hospitalInformationSheet.xml"
OUTPUT_DIRECTORY = "Data/GeneratedFiles"


def create_pesel() -> int:
    return randint(int(1e10), int(1e11 - 1))


def create_name() -> str:
    return 'Adam Mickiewicz'


def create_xml(information_sheet):
    with open('hospitalInformationSheet.xml', 'w') as f:
        f.write(information_sheet._element.xml)


def print_docx(information_sheet):
    i = 0
    for paragraph in information_sheet.paragraphs:
        print(f'{i}: {paragraph.text}')
        i += 1


def create_date():
    return '2222-12-31'


def produce_new_file():
    # information_sheet = Document(INPUT_FILE)
    new_pesel = create_pesel()
    new_name = create_name()
    new_date = create_date()
    with open(INPUT_FILE, 'r') as source:
        contents = source.read()
    contents.replace('pesel_', new_pesel)
    contents.replace('name_', new_name)
    contents.replace('date_', new_date)
    # i = 0
    # paragraph = information_sheet.paragraphs[3]
    # # information_sheet.paragraphs[3].text = f"Telefon  0-12/666-55-44	Pacjent: {new_name}    PESEL: {new_pesel}"
    # paragraph.runs[0].text = f"Telefon  0-12/666-55-44	Pacjent: {new_name}    PESEL: {new_pesel}"
    # information_sheet.save('edited.docx')
