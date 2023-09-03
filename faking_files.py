import cv2
import re
from fuzzywuzzy import fuzz

import fake_data_creator


class FakingFiles:

    def __init__(self, init_cv2_image, read_data):
        self.fake_data = fake_data_creator.FakeDataCreator()
        self.init_image = init_cv2_image
        self.read_data = read_data
        self.data_to_change = {'type': [],      # what type of word should it be replaced with, e.g. first_name
                               'top': [],       # coordinates of top border
                               'left': [],      # coordinate of left border
                               'width': [],     # width of box
                               'height': []     # height of box
                               }
        self.iterator = 0    # used to iterate through data from tesseract

        self.person = None

        self._scan_document()

    @staticmethod
    def fuzzy_match(keyword, text):
        similarity_score = fuzz.partial_ratio(keyword.lower(), text.lower())

        if similarity_score >= 85:
            return True
        else:
            return False

    def _scan_document(self):
        keyword_functions = {
            "pacjent": self.process_pacjent,
            "pesel": self.process_pesel,
            "Adres": self.process_adres,
            "Data urodzenia": self.process_data_urodzenia,
            "Data i godzina": self.process_data_i_godzina,
        }

        # Iterate over the detected text regions
        while self.iterator < len(self.read_data['text']):
            for keyword, func in keyword_functions.items():
                if self.fuzzy_match(keyword, self.read_data['text'][self.iterator]):
                    if 'pacjenta:' == keyword:
                        continue
                    print(self.read_data['text'][self.iterator])
                    func()

            self.iterator += 1

    def create_altered_file(self, cv_image):
        """
        Creates files with faked data on them
        :param cv_image: image read by OpenCV
        :return: file with changed data
        """

        self.person = self.fake_data.create_person()

        # Iterate over the detected text regions
        for i in range(len(self.data_to_change['type'])):
            # Extract the word and its bounding box coordinates
            word = self.person[self.data_to_change['type'][i]]
            x = self.data_to_change['left'][i]
            y = self.data_to_change['top'][i]
            width = self.data_to_change['width'][i]
            height = self.data_to_change['height'][i]

            # Draw a rectangle around the new word on the image
            cv2.rectangle(cv_image, (x, y), (x + width, y + height), (0, 255, 0), 2)

            # Put the new word at the same location
            cv2.putText(cv_image, word, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)


    def process_pacjent(self):
        print("Pacjent found")  # debug
        # checks if it found ":" in range in case tesseract split incorrectly or imię i nazwisko is after
        up_limit = self.iterator + 5 if self.iterator + 5 < len(self.read_data['text']) else len(self.read_data['text'])
        for i in range(self.iterator, up_limit):
            # print(f"{i}:{self.read_data['text'][i]}")
            if ':' in self.read_data['text'][i]:
                i_to_replace = self.find_next_text_occurrence(i + 1)    # find first name
                if i_to_replace == -1 or i_to_replace - i > 5:
                    print('Warning: "Pacjent" found, but no following string, replacement not successful.')
                    return
                self._add_to_dict(i_to_replace, 'first_name')
                # self.replace(i_to_replace, self.person['first_name'])
                self.iterator = i_to_replace

                i_to_replace = self.find_next_text_occurrence(i_to_replace + 1)     # find last name
                if i_to_replace == -1 or i_to_replace - i > 5:
                    print('Warning: "Pacjent" found, but failed to replace last name.')
                    return
                self._add_to_dict(i_to_replace, 'last_name')
                self.iterator = i_to_replace
                return

        print('Warning: "Pacjent" found, but could not detect a place to swap')

    def process_pesel(self):
        # print("Pesel found")
        pass

    def process_adres(self):
        # print("Adres found")
        pass

    def process_data_urodzenia(self):
        # print("Data urodzenia found")
        pass

    def process_data_i_godzina(self):
        # print("data i godzina found")
        pass

    def find_next_text_occurrence(self, start_pos):
        """
        Finds next instance of a word made out of at least two letters
        :param start_pos: position from which you want to start looking
        :return: position of next word occurrence, if it doesn't find anything, returns 0
        """
        pattern = r"[a-zA-Z]{2,}"
        for i in range(start_pos, len(self.read_data['text'])):
            if re.search(pattern, self.read_data['text'][i]):
                return i

        return -1

    def _add_to_dict(self, i, type_of_data):
        self.data_to_change['type'].append(type_of_data)
        self.data_to_change['top'].append(self.read_data['top'][i])
        self.data_to_change['left'].append(self.read_data['left'][i])
        self.data_to_change['width'].append(self.read_data['width'][i])
        self.data_to_change['height'].append(self.read_data['height'][i])
