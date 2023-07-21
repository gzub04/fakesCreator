import cv2
import pytesseract
from PIL import Image
import argparse
import os

def create_altered_file(image, options):
    """
    Creates files with faked data on them
    :param image: image read by OpenCV
    :param options: set containing all data that is supposed to be changed. Possible options: {name, address, date,
    phone_number, pesel}
    :return: file with data changed according to options
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    pass