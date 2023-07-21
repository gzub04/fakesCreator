import cv2
import pytesseract
from PIL import Image
import argparse
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="path to input image")
    ap.add_argument("-p", "--preprocess", type=str, default="thresh", help="type of preprocessing to be done")
    args = vars(ap.parse_args())

    # load the image and convert to grayscale
    image = cv2.imread(args["image"])
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # check if we need to apply thresholding
    if args["preprocess"] == "thresh":
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU) [1]
    # check if blur should be used
    elif args["preprocess"] == "blur":
        gray = cv2.medianBlur(gray, 3)

    # write grayscale img to disk as a temp file, so we can apply OCR
    filename = "{}.png".format(os.getpid())
    cv2.imwrite(filename, gray)
    # load image as Pillow image, apply OCR and delete temp file
    text = pytesseract.image_to_string(Image.open(filename))
    os.remove(filename)

    # show output text and images
    print(text)
    cv2.imshow("Image", image)
    cv2.imshow("Output", gray)
    cv2.waitKey(0)

if __name__ == '__main__':
    main()