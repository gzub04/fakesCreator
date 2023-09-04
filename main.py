import argparse
import cv2
import numpy
import pytesseract
from PIL import Image

import utils
import init_training_documents_creator as Docs
import image_distorting as distort
import faking_files


FAKE_FILES_PATH = 'data/generated_documents/faked_files'


def parse_arguments():
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
        showcase_document = "data/generated_documents/showcase_document.jpg"
        args['document'] = showcase_document
        print(f"Initial document for showcase saved at {showcase_document}")
    # if it's not showcase then:
    elif args['type'] is None:
        utils.err_exit("--type of document not given")

    return args


def read_document(image_path):
    image = cv2.imread(image_path)
    return pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='pol')


def main():
    args = parse_arguments()

    # check what type of file
    file_wo_extension, extension = args['document'].rsplit('.', 1)
    if extension == 'doc' or extension == 'docx':
        args['document'] = utils.docx_to_jpg(args['document'])
    elif extension == 'pdf':
        args['document'] = utils.pdf_to_jpg(args['document'])
    elif not extension == 'jpg' and not extension == 'png' and not extension == 'bmp':
        utils.err_exit(f"Unsupported file extension {extension}!")

    # load initial image to memory
    init_pil_image = Image.open(args['document']).convert('RGB')
    init_cv_image = cv2.cvtColor(numpy.array(init_pil_image), cv2.COLOR_RGB2BGR)

    # read image
    if not args['only_distort']:
        read_data = read_document(args['document'])
        faker = faking_files.FakingFiles(init_cv_image, read_data)
        # utils.save_test_data_to_csv(read_data)

    enhancer = distort.ImageDistorting()

    for i in range(args['n']):
        new_pil_image = init_pil_image.copy()

        # Distort without rotating
        if args['distort_type'] == 'scan':
            new_pil_image = enhancer.scan_distortion(new_pil_image)
        elif args['distort_type'] == 'photo':
            new_pil_image = enhancer.photo_distortion(new_pil_image)

        # Fake the file
        if not args['only_distort']:
            new_cv_image = cv2.cvtColor(numpy.array(new_pil_image), cv2.COLOR_RGB2BGR)

            faker.create_altered_file(new_cv_image)
            cv2.imwrite(f"{FAKE_FILES_PATH}/fake_document_{i}.jpg", new_cv_image)

        new_pil_image.close()

    init_pil_image.close()

    # rotate
    # use cv2

    # save file and what changed in it

    # TMP
    # init_pil_image.save('Data/generated_documents/output.jpg')

    if args['only_distort'] is not None:
        return 0


if __name__ == '__main__':
    main()
