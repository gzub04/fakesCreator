import cv2
import pytesseract
from PIL import Image
import argparse
import os


def create_altered_file(image, options: set()):
    """
    Creates files with faked data on them
    :param image: image read by OpenCV
    :param options: set containing all data that is supposed to be changed. Possible options: {name, address, date,
    phone_number, pesel}
    :return: file with data changed according to options
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]  # thresholding for better quality

    text_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    # Iterate over the detected text regions
    for i in range(len(text_data['text'])):
        # Extract the word and its bounding box coordinates
        word = text_data['text'][i]
        x = text_data['left'][i]
        y = text_data['top'][i]
        width = text_data['width'][i]
        height = text_data['height'][i]

        # Check if the word matches the target word
        if word in "Pacjent":
            # Replace the word with a new word
            new_word = 'NewWord'
            text_data['text'][i+1] = new_word

            # Draw a rectangle around the new word on the image
            cv2.rectangle(image, (x, y), (x + width, y + height), (0, 255, 0), 2)

            # Put the new word at the same location
            cv2.putText(image, new_word, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Generate a new image with modified text
    new_image = image.copy()

    # Iterate over the detected text regions again to update the new image
    for i in range(len(text_data['text'])):
        # Extract the updated word and its bounding box coordinates
        updated_word = text_data['text'][i]
        x = text_data['left'][i]
        y = text_data['top'][i]
        width = text_data['width'][i]
        height = text_data['height'][i]

        # Put the updated word at the same location in the new image
        cv2.putText(new_image, updated_word, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Save the new image with modified text
    cv2.imwrite('path/to/new_image.png', new_image)

    # Display the new image with modified text
    cv2.imshow('New Image with Modified Text', new_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    pass
