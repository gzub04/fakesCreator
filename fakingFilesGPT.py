import cv2
import pytesseract
from PIL import Image, ImageDraw


def ocr_image(image_path):
    # Load the image using OpenCV
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Perform OCR using Tesseract
    text = pytesseract.image_to_string(gray_image, lang='pol')

    return text


def replace_information(text):
    # Add your logic here to replace specific information in the 'text' variable
    # For example, you can use regular expressions or other techniques to find and replace names, surnames, phone numbers, dates, addresses, etc.

    # For demonstration purposes, let's assume we have already replaced the required information in 'updated_text' variable
    updated_text = text.replace('Wieńczysław Nieszczególny', 'John Doe').replace('00000000000', '12345678901')

    return updated_text


def save_updated_image(image_path, updated_text):
    # Load the image using Pillow
    image = Image.open(image_path)

    # Add the updated text to the image using Pillow's Draw
    draw = ImageDraw.Draw(image)
    draw.text((50, 50), updated_text, fill='black')

    # Save the updated image as a new JPG file
    updated_image_path = 'updated_' + image_path
    image.save(updated_image_path, 'JPEG')
    return updated_image_path


def main():
    input_image_path = 'Data/sources/hospitalInformationSheet.jpg'
    output_image_path = ocr_image(input_image_path)

    updated_text = replace_information(output_image_path)
    updated_image_path = save_updated_image(input_image_path, updated_text)

    print(f"Updated image saved to: {updated_image_path}")


if __name__ == "__main__":
    main()
