import os
import sys

import cv2
import doc2pdf
import numpy
from PIL import Image
from pdf2image import convert_from_path


def err_exit(err_msg):
    print(f'Error: {err_msg}', file=sys.stderr)
    exit(1)


def docx_to_bmp(file_path) -> str:
    """
    Coverts odt, doc or docx file to bmp and saves it at the same location
    :param file_path: path to doc/docx file
    :return: path to generated bmp file
    """
    file_wo_extension, extension = file_path.rsplit('.', 1)
    extensions = ['odt', 'doc', 'docx']
    if extension not in extensions:
        print("Error: Expected one of the following extensions: ", end='')
        print(*extensions, sep=', ')
        return ''

    doc2pdf.convert(file_path)
    pdf_file = file_wo_extension + '.pdf'
    image = pdf_to_bmp(pdf_file)
    os.remove(pdf_file)

    return image


def pdf_to_bmp(file_path) -> str:
    """
    Converts pdf file to bmp and saves it at the same location
    :param file_path: path to pdf file
    :return: path to generated bmp
    """
    file_wo_extension, extension = file_path.rsplit('.', 1)
    if not extension == 'pdf':
        print("Error: expected .pdf file!")
        return ''
    images = convert_from_path(file_path, fmt='bmp')
    image_name = file_wo_extension + '.bmp'
    images[0].save(image_name, "BMP")

    return image_name


def pil_image_to_cv2(pil_image):
    return cv2.cvtColor(numpy.array(pil_image.convert('RGB')), cv2.COLOR_RGB2BGR)


def cv2_image_to_pil(cv2_image):
    return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
