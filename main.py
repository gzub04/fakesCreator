import init_training_documents_creator as Docs


def generate_training_documents(amount):
    for i in range(amount):
        output_name = f"training_document_{i}.docx"
        if not Docs.produce_new_init_document(output_name):
            return 1

    if not Docs.training_docx_to_jpg():
        return 1


def main():
    generate_training_documents(10)
    # TODO: add image noise on them
    # TODO: create multiple versions of the initial file


if __name__ == '__main__':
    main()
