import init_training_documents_creator as Docs
import image_conversion
import pytesseract


def main():
    Docs.produce_new_init_document('edited.docx')
    # TODO: add image noise on them
    # TODO: create multiple versions of the initial file


if __name__ == '__main__':
    main()
