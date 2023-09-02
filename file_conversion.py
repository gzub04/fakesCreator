import os
import doc2pdf
from pdf2image import convert_from_path


def docx_to_jpg(file_path):
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


def pdf_to_jpg(file_path):
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
