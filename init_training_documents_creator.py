import fake_data_creator
from docx import Document


SOURCE_FILES = "Data/sources"
INPUT_DOCUMENT = f"{SOURCE_FILES}/hospitalInformationSheet.docx"
OUTPUT_DIRECTORY = "Data/generated_documents"


def produce_new_init_document(output_name):
    information_sheet = Document(INPUT_DOCUMENT)

    fake_data = fake_data_creator.FakeDataCreator()
    person = fake_data.create_person()
    address = fake_data.create_address()
    dates = fake_data.create_dates()
    phone_number = fake_data.create_phone_number()

    birthday = person['birthdate']
    start_date = dates['start_date']
    end_date = dates['end_date']

    paragraph = information_sheet.paragraphs[3]
    paragraph.runs[6].text = f"{person['first_name']} {person['last_name']}"
    paragraph.runs[11].text = f"{person['pesel']}"

    paragraph = information_sheet.paragraphs[4]
    paragraph.runs[3].text = f"Kraków, {end_date.strftime('%Y-%m-%d')}"

    paragraph = information_sheet.paragraphs[10]
    paragraph.runs[2].text = f"{person['first_name']} {person['last_name']}"
    paragraph.runs[7].text = f"{person['pesel']}"

    paragraph = information_sheet.paragraphs[11]
    paragraph.runs[3].text = f"{birthday.strftime('%Y-%m-%d')}"
    paragraph.runs[6].text = f" {phone_number}"
    paragraph.runs[13].text = f"{person['sex']}"

    paragraph = information_sheet.paragraphs[12]
    paragraph.runs[0].text = f"Adres zamieszkania: {address['street']}, {address['city']}"

    paragraph = information_sheet.paragraphs[13]
    paragraph.runs[0].text = f"Data i godzina przyjęcia pacjenta: {start_date.strftime('%Y-%m-%d')}, " \
                             f"{start_date.strftime('%H:%M')}, " \
                             f"data i godzina wypisu pacjenta: {end_date.strftime('%y-%m-%d')}, " \
                             f"{end_date.strftime('%H:%M')}"

    information_sheet.save(f"{OUTPUT_DIRECTORY}/{output_name}")


def create_xml():
    information_sheet = Document(INPUT_DOCUMENT)
    with open('HospitalInformationSheet.xml', 'w', encoding='utf-8') as f:
        f.write(information_sheet._element.xml)
#
#
# def print_docx(information_sheet):
#     i = 0
#     for paragraph in information_sheet.paragraphs:
#         print(f'{i}: {paragraph.text}')
#         i += 1
