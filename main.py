import InitTrainingDocumentsCreator as Docs
import imageConversion
import pytesseract


def main():
    Docs.produce_new_file()
    # TODO: add image noise on them
    # TODO: create multiple versions of the initial file


if __name__ == '__main__':
    main()
