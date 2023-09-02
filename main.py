import argparse
import sys
import cv2
import pytesseract
from PIL import Image

import init_training_documents_creator as Docs
import image_distorting as distort
import file_conversion as convert


def err_exit(err_msg):
    print(f'Error: {err_msg}', file=sys.stderr)
    exit(1)


def read_document(image_path):
    image = cv2.imread(image_path)
    text_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    print(text_data)


def main():
    parser = argparse.ArgumentParser(
        prog="fakesCreator", description="Allows to make documents look like they've been photographed/scanned and "
                                         "fake them while saving exact coordinates where they were modified."
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('-d', '--document', type=str, help="Path to the input document, "
                                                         "supported types: jpg, png, bmp, pdf, doc, docx")
    mode.add_argument('--showcase', action='store_true', help="Creates testing document, applies filters and fakes it.")

    parser.add_argument('-n', type=int, required=True, help="Number of new documents to create")
    parser.add_argument('-t', '--type', type=str,
                        help="Type of document to modify: \"HospitalInformationSheet\" or \"invoice\"")
    parser.add_argument(
        '--only_distort', action='store_true',
        help="If you don't want to fake the file and only apply image distorting. "
             "Exclusive with all other arguments except --image"
    )
    parser.add_argument('--distort_type', required=True, choices=['photo', 'scan'],
                        help="How do you want your output image to look like: \"photo\" or \"scan\"")
    args = vars(parser.parse_args())

    if args['showcase']:
        Docs.generate_training_documents(1)
        args['document'] = "Data/generated_documents/training_documents/training_document_0.jpg"
    # if it's not showcase then:
    elif args['type'] is None:
        err_exit("--type of document not given")

    # check what type of file
    file_wo_extension, extension = args['document'].rsplit('.', 1)
    if extension == 'doc' or extension == 'docx':
        args['document'] = convert.docx_to_jpg(args['document'])
    elif extension == 'pdf':
        args['document'] = convert.pdf_to_jpg(args['document'])
    elif not extension == 'jpg' and not extension == 'png' and not extension == 'bmp':
        err_exit(f"Unsupported file extension {extension}!")

    # read image

    # Distort without rotating
    init_image = Image.open(args['document'])
    enhancer = distort.ImageDistorting()

    if not args['only_distort']:
        read_document(args['document'])

    if args['distort_type'] == 'scan':
        init_image = enhancer.scan_distortion(init_image)
    elif args['distort_type'] == 'scan':
        init_image = enhancer.photo_distortion(init_image)

    # fake the file

    # rotate

    # save file and what changed in it

    # TMP
    init_image.save('Data/generated_documents/output.jpg')

    if args['only_distort'] is not None:
        return 0


if __name__ == '__main__':
    main()
