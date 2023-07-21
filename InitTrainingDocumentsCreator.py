from docx import Document
from random import randint, choice
import datetime


SOURCE_FILES = "Data/sources"
INPUT_DOCUMENT = f"{SOURCE_FILES}/hospitalInformationSheet.docx"
OUTPUT_DIRECTORY = "Data/generated_documents"


def create_pesel() -> str:
    return str(randint(int(1e10), int(1e11 - 1)))


def create_name(sex) -> str:
    if sex == 'M':
        file_first_names = open(f'{SOURCE_FILES}/male_firstnames.csv', 'r', encoding='utf-8')
        file_last_names = open(f'{SOURCE_FILES}/male_lastnames.csv', 'r', encoding='utf-8')
    else:
        file_first_names = open(f'{SOURCE_FILES}/female_firstnames.csv', 'r', encoding='utf-8')
        file_last_names = open(f'{SOURCE_FILES}/female_lastnames.csv', 'r', encoding='utf-8')
    first_names = file_first_names.readlines()
    last_names = file_last_names.readlines()
    file_first_names.close()
    return choice(first_names).rstrip('\n').capitalize() + ' ' + choice(last_names).rstrip('\n').capitalize()


def create_xml(information_sheet):
    with open('HospitalInformationSheet.xml', 'w') as f:
        f.write(information_sheet._element.xml)


def print_docx(information_sheet):
    i = 0
    for paragraph in information_sheet.paragraphs:
        print(f'{i}: {paragraph.text}')
        i += 1


def create_dates():
    """
    Returns list of length 5:
    [0] - birth date
    [1] - arrival at hospital date
    [2] - arrival at hospital hour
    [3] - discharge date
    [4] - discharge hour
    """

    today = datetime.date.today()

    # generate birthdate date from 23 to 60 years ago
    birthdate = datetime.date.today() - datetime.timedelta(days=(randint(23, 60) * 365))

    # Generate a random arrival date between 7 days and 20 years ago
    arrival_date = datetime.datetime.now() - datetime.timedelta(days=randint(7, 365 * 20))
    arrival_date = arrival_date.replace(hour=randint(0, 23), minute=randint(0, 59))

    # Generate random discharge date between 1 and 7 days after the arrival date
    discharge_date = arrival_date + datetime.timedelta(days=randint(1, 5))
    discharge_date = discharge_date.replace(hour=randint(10, 16), minute=choice([0, 30]))


    return [birthdate, arrival_date.strftime('%Y-%m-%d'), arrival_date.strftime('%H:%M'),
            discharge_date.strftime('%Y-%m-%d'), discharge_date.strftime('%H:%M')]


def create_phone_number():
    return str(randint(int(1e9), int(1e10 - 1)))

def create_address():
    return 'Warszawska 15, Kraków'


def produce_new_file():
    information_sheet = Document(INPUT_DOCUMENT)
    new_sex = choice(['K', 'M'])
    new_pesel = create_pesel()
    new_name = create_name(new_sex)
    new_dates = create_dates()
    new_address = create_address()
    new_phone_number = create_phone_number()

    paragraph = information_sheet.paragraphs[3]
    paragraph.runs[6].text = f'{new_name}    '
    paragraph.runs[11].text = f'{new_pesel}'

    paragraph = information_sheet.paragraphs[4]
    paragraph.runs[3].text = f'Kraków, {new_dates[3]}'

    paragraph = information_sheet.paragraphs[10]
    paragraph.runs[2].text = f'{new_name}'
    paragraph.runs[7].text = f'{new_pesel}'

    paragraph = information_sheet.paragraphs[11]
    paragraph.runs[3].text = f'{new_dates[0]}'
    paragraph.runs[11].text = f'{new_sex}'

    paragraph = information_sheet.paragraphs[12]
    paragraph.runs[0].text = f'Adres zamieszkania: {new_address}'

    paragraph = information_sheet.paragraphs[13]
    paragraph.runs[0].text = f'Data i godzina przyjęcia pacjenta: {new_dates[1]}, {new_dates[2]}, ' \
                             f'data i godzina wypisu pacjenta: {new_dates[3]}, {new_dates[4]}'

    information_sheet.save(f'{OUTPUT_DIRECTORY}/edited.docx')
