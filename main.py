import argparse
import json
import os
from math import sin, cos, radians

import cv2
import pytesseract
from PIL import Image
from progress.bar import Bar

import faking_files
import image_distorting as distort
import utils

FAKE_FILES_PATH = 'output/faked_files'
JSON_DIR_PATH = 'output/output_json'
JSON_NAME = 'file_changes.json'


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="fakesCreator", description="Allows to make documents look like they've been photographed/scanned and "
                                         "fake them while saving exact coordinates where they were modified."
    )

    # mode = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('-d', '--document', type=str, required=True,
                        help="Path to the input document, supported types: jpg, png, bmp, pdf, odt, doc, docx")
    parser.add_argument('--showcase', action='store_true', help="Creates an new image, marking with red boxes "
                                                                "all data that would be replaced")

    parser.add_argument('-n', type=int, help="Number of new documents to create")
    parser.add_argument('-t', '--type', type=str, required=True,
                        help="Type of document to modify: \"HospitalInformationSheet\" or \"invoice\"")
    parser.add_argument(
        '--only_distort', action='store_true',
        help="If you don't want to fake the file and only apply image distorting. "
             "Exclusive with all other arguments except --document and --distort_type"
    )
    parser.add_argument('--distort_type', choices=['photo', 'scan'],
                        help="How do you want your output image to look like: \"photo\" or \"scan\"")
    args = vars(parser.parse_args())

    if args['showcase'] and any([args['n'], args['distort_type']]) and args['only_distort'] is True:
        utils.err_exit("--showcase can only be used only with --document and --type")
    elif not args['showcase'] and all(arg is None for arg in [args['n'], args['distort_type']]):
        utils.err_exit("Missing -n or --distort_type arguments")

    return args


def read_document(image_path):
    image = cv2.imread(image_path)
    return pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='pol')


def adjust_coordinates(init_document_info, rotation_info, pil_image):
    """
    Adjust coordinates from before the rotation to after the rotation
    :param init_document_info: a list of changes in file, changes must be dicts with keys:
    text, top_left, top_right, bottom_left, bottom_right, where all but text are coordinates of changes
    :param rotation_info: by how many degrees was image rotated
    :param pil_image: rotated pillow image
    :return: Returns a new list of changes in file with adjusted coordinates
    """
    rotation = radians(- rotation_info['rotation'])
    x_increase = rotation_info['width_increase'] // 2
    y_increase = rotation_info['height_increase'] // 2
    width, height = pil_image.size
    center = [width // 2, height // 2]

    for box in init_document_info:
        for key, value in box.items():
            if key not in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:  # if not coordinates
                continue

            x, y = value
            # adjust starting location before rotating
            new_x = x + x_increase
            new_y = y + y_increase

            # rotate coordinates
            new_x = (new_x - center[0]) * cos(rotation) - (new_y - center[1]) * sin(rotation) + center[0]
            new_y = (new_x - center[0]) * sin(rotation) + (new_y - center[1]) * cos(rotation) + center[1]

            new_x = int(new_x)
            new_y = int(new_y)

            box[key] = [new_x, new_y]

    return init_document_info


def main():
    args = parse_arguments()

    # check what type of file
    file_wo_extension, extension = args['document'].rsplit('.', 1)
    if extension == 'doc' or extension == 'docx' or extension == 'odt':
        args['document'] = utils.docx_to_jpg(args['document'])
    elif extension == 'pdf':
        args['document'] = utils.pdf_to_jpg(args['document'])
    elif not extension == 'jpg' and not extension == 'png' and not extension == 'bmp':
        utils.err_exit(f"Unsupported file extension {extension}!")
    if args['document'] == '':
        utils.err_exit("Initial image not found")

    # set up paths
    if not os.path.exists(FAKE_FILES_PATH):
        os.makedirs(FAKE_FILES_PATH)
    files = os.listdir(FAKE_FILES_PATH)
    for file in files:
        file_path = os.path.join(FAKE_FILES_PATH, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # load initial image to memory
    init_pil_image = Image.open(args['document'])
    init_cv_image = utils.pil_image_to_cv2(init_pil_image)

    # read image
    if not args['only_distort']:
        read_data = read_document(args['document'])
        faker = faking_files.FakingFiles(init_cv_image, read_data, args['type'])
        # utils.save_test_data_to_csv(read_data)
        # exit(0)

    # if it's just showcase
    if args['showcase'] and len(faker.data_to_change['type']) > 0:
        font_size = faker.data_to_change['height'][0] / 30
        for i in range(len(faker.data_to_change['type'])):
            text = faker.data_to_change['type'][i]
            x = faker.data_to_change['left'][i]
            y = faker.data_to_change['top'][i]
            width = faker.data_to_change['width'][i]
            height = faker.data_to_change['height'][i]
            cv2.rectangle(init_cv_image, (x, y), (x + width, y + height), (0, 0, 255), 2)
            if args['type'] == 'invoice':
                out_coordinates = (x + width + 10, y)
            else:
                out_coordinates = (x, y - 10)
            cv2.putText(init_cv_image, text, out_coordinates, cv2.FONT_HERSHEY_DUPLEX, font_size, (0, 0, 255), 1)
        cv2.imwrite(f'{FAKE_FILES_PATH}/showcase.jpg', init_cv_image)
        return 0
    elif args['showcase']:
        utils.err_exit("No data to change was found")

    enhancer = distort.ImageDistorting()

    changes = {}  # dictionary containing changes on all faked files
    with Bar("Creating new files...") as bar:
        for i in range(args['n']):
            new_pil_image = init_pil_image.copy()
            new_document_name = f"distorted_document_{i}.jpg"

            # Distort without rotating
            if args['distort_type'] == 'scan':
                new_pil_image = enhancer.scan_distortion(new_pil_image)
            elif args['distort_type'] == 'photo':
                new_pil_image = enhancer.photo_distortion(new_pil_image)

            # Fake the file
            if not args['only_distort']:
                new_cv_image = utils.pil_image_to_cv2(new_pil_image)

                new_document_name = f"fake_document_{i}.jpg"
                document_changes = faker.create_altered_file(new_cv_image)

                new_pil_image.close()
                new_pil_image = utils.cv2_image_to_pil(new_cv_image)

            # rotate image to make it look more realistic
            new_pil_image, rotation_info = enhancer.rotate_img(new_pil_image, args['distort_type'])

            if not args['only_distort']:
                document_changes = adjust_coordinates(document_changes, rotation_info, new_pil_image)
                changes[new_document_name] = document_changes

            new_pil_image.save(f"{FAKE_FILES_PATH}/{new_document_name}")
            new_pil_image.close()
            bar.next()

    init_pil_image.close()

    # save to
    if not args['only_distort']:
        if not os.path.exists(JSON_DIR_PATH):
            os.makedirs(JSON_DIR_PATH)

        json_object = json.dumps(changes, indent=4, ensure_ascii=False)
        with open(f'{JSON_DIR_PATH}/{JSON_NAME}', "w", encoding="utf-8") as f_out:
            f_out.write(json_object)


if __name__ == '__main__':
    main()
