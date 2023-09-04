import os
import sys
import doc2pdf
from pdf2image import convert_from_path


def err_exit(err_msg):
    print(f'Error: {err_msg}', file=sys.stderr)
    exit(1)


def docx_to_jpg(file_path) -> str:
    """
    Coverts doc or docx file to jpg and saves it at the same location
    :param file_path: path to doc/docx file
    :return: path to generated jpg
    """
    file_wo_extension, extension = file_path.rsplit('.', 1)
    if not extension == 'doc' and not extension == 'docx':
        print("Error: expected .doc or .docx file!")
        return ''

    doc2pdf.convert(file_path)
    pdf_file = file_wo_extension + '.pdf'
    image = pdf_to_jpg(pdf_file)
    os.remove(pdf_file)

    return image


def pdf_to_jpg(file_path) -> str:
    """
    Converts pdf file to jpg and saves it at the same location
    :param file_path: path to pdf file
    :return: path to generated jpg
    """
    file_wo_extension, extension = file_path.rsplit('.', 1)
    if not extension == 'pdf':
        print("Error: expected .pdf file!")
        return ''
    images = convert_from_path(file_path, fmt='jpg')
    image_name = file_wo_extension + '.jpg'
    images[0].save(image_name, "JPEG")

    return image_name


# ---------- helpers for testing code ----------


def save_test_data_to_csv(read_data):
    output_file = "data/generated_documents/output_data.csv"

    # Open the file for writing
    with open(output_file, "w", encoding="utf-8") as file:
        # Write the header row
        headers = list(read_data.keys())
        file.write("\t".join(headers) + "\n")

        # Write the data rows
        for i in range(len(read_data["text"])):
            row = [str(read_data[key][i]) for key in headers]
            file.write("\t".join(row) + "\n")

    print(f"Data saved to {output_file}")
