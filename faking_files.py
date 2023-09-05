import cv2
import re


from fuzzywuzzy import fuzz

import fake_data_creator

FONT_PATH = 'data/sources/Arial.ttf'


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
        self.iterator = 0           # used to iterate through data from tesseract
        self.date_formats = []      # stores format so here are stored
        self.date_iterator = 0      #

        self._scan_document()

    def _scan_document(self):
        keyword_functions = {
            'pacjent': self.process_pacjent,
            'płeć': self.process_plec,
            'pesel': self.process_pesel,
            'data': self.process_date,
            'numer telefonu': self.process_phone_number,
            'tel. kontaktowy': self.process_phone_number,
            'numer kontaktowy': self.process_phone_number,
            'adres': self.process_adres,    # TODO
        }

        # Iterate over the detected text regions
        while self.iterator < len(self.read_data['text']):
            curr_word = self.read_data['text'][self.iterator]
            for keyword, func in keyword_functions.items():
                if self._fuzzy_match(keyword, curr_word) or (len(self.read_data['text']) > self.iterator + 2 and
                   self._fuzzy_match(keyword, curr_word + ' ' + self.read_data['text'][self.iterator + 1])):
                    func()

            self.iterator += 1

    def create_altered_file(self, cv_image):
        """
        Creates files with faked data on them
        :param cv_image: image read by OpenCV
        :return: file with changed data
        """
        date_iterator = 0
        person = self.fake_data.create_person()
        dates = self.fake_data.create_dates()
        phone_number = self.fake_data.create_phone_number()

        keyword_to_name = {    # converts keyword to proper faked text
            'name': person['first_name'] + ' ' + person['last_name'],
            'pesel': person['pesel'],
            'sex': person['sex'],
            'birthdate': person['birthdate'],
            'start_date': dates['start_date'],
            'end_date': dates['end_date'],
            'phone_number': phone_number,
            'blank': '',
        }

        # Iterate over the detected text regions
        for i in range(len(self.data_to_change['type'])):
            # Extract the text and its bounding box coordinates
            current_keyword = self.data_to_change['type'][i]

            if 'date' in current_keyword:
                text = keyword_to_name[current_keyword].strftime(self.date_formats[date_iterator])
                date_iterator += 1
            else:
                text = keyword_to_name[current_keyword]

            x = self.data_to_change['left'][i]
            y = self.data_to_change['top'][i]
            width = self.data_to_change['width'][i]
            height = self.data_to_change['height'][i]

            # Draw a rectangle around the new text on the image
            cv2.rectangle(cv_image, (x, y), (x + width, y + height), (0, 255, 0), 2)

            # Put the new text at the same location
            cv2.putText(cv_image, text, (x, y - 10), cv2.FONT_HERSHEY_COMPLEX, height/30, (0, 255, 0), 2)

    def process_pacjent(self):
        current = self.read_data['text'][self.iterator].rstrip()
        if current[-1:] == 'a' or current[-2:] == 'a:':
            return  # meant for when it found "pacjenta" somewhere in the text
        # checks if it found ":" in range in case tesseract split incorrectly or imię i nazwisko is after
        up_limit = self.iterator + 5 if self.iterator + 5 < len(self.read_data['text']) else len(self.read_data['text'])
        for i in range(self.iterator, up_limit):
            if ':' in self.read_data['text'][i]:
                i_to_replace = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i + 1)    # find first name
                if i_to_replace == -1 or i_to_replace - i > 5:
                    print('Warning: "Pacjent" found, but no following string, replacement not successful.')
                    return
                self.iterator = i_to_replace

                i_to_replace_2 = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i_to_replace + 1)  # find last name
                if i_to_replace_2 == -1 or i_to_replace_2 - i > 5:
                    print('Warning: "Pacjent" found, but failed to replace last name.')
                    return
                # first cover surname, then paste full name
                self._add_to_dict(i_to_replace_2, 'blank')
                self._add_to_dict(i_to_replace, 'name')
                self.iterator = i_to_replace_2
                return

        print('Warning: "Pacjent" found, but could not detect a place to swap')

    def process_plec(self):
        i_to_replace = self._find_next_regex_occurrence(r"^(M|F)$", self.iterator + 1)
        if i_to_replace == -1 or i_to_replace - self.iterator > 5:
            print(f"'Warning: \"{self.read_data['text'][self.iterator]}\" found, "
                  f"but failed to find sex to replace.")
            return
        self._add_to_dict(i_to_replace, 'sex')
        self.iterator = i_to_replace

    def process_pesel(self):
        # checks if it found ":" in range in case tesseract split incorrectly or imię i nazwisko is after
        i_to_replace = self._find_next_regex_occurrence(r"^\d{11}$", self.iterator + 1)
        if i_to_replace == -1 or i_to_replace - self.iterator > 5:
            print(f"'Warning: \"{self.read_data['text'][self.iterator]}\" found, "
                  f"but failed to find pesel to replace.")
            return
        self._add_to_dict(i_to_replace, 'pesel')
        self.iterator = i_to_replace

    def process_date(self):

        # find the nearest words to verify what type of date it is
        nearest_words = []
        range_limit = self.iterator + 4
        for i in range(self.iterator, range_limit):
            i_of_next_word = self._find_next_regex_occurrence(r"[A-Za-z]{2,}", i)
            if i_of_next_word != -1 and i < range_limit:
                next_word = self.read_data['text'][i]
                nearest_words.append(next_word)

        for word in nearest_words:
            if self._fuzzy_match('urodzenia', word):
                i_to_replace, formatting = self._next_date_position_and_formatting(self.iterator + 1)
                if -1 < i_to_replace - self.iterator < 10:
                    self._add_to_dict(i_to_replace, 'birthdate')
                    self.date_formats.append(formatting)
                    return
                print(f"'Warning: \"{self.read_data['text'][self.iterator]}\" and \"{word}\" found, "
                      f"but failed to find date to replace.")

            for option in ['koniec']:
                if self._fuzzy_match(option, word):
                    i_to_replace, formatting = self._next_date_position_and_formatting(self.iterator + 1)
                    if -1 < i_to_replace - self.iterator < 10:
                        self._add_to_dict(i_to_replace, 'end_date')
                        self.date_formats.append(formatting)
                        return
                    print(f"'Warning: \"{self.read_data['text'][self.iterator]}\" and \"{word}\" found, "
                          f"but failed to find date to replace.")

        # if neither birthdate nor end date, use start date
        i_to_replace, formatting = self._next_date_position_and_formatting(self.iterator + 1)
        if -1 < i_to_replace - self.iterator < 10:
            self._add_to_dict(i_to_replace, 'start_date')
            self.date_formats.append(formatting)
            return
        print(f"'Warning: \"{self.read_data['text'][self.iterator]}\" found, "
              f"but failed to find date to replace.")

    def process_phone_number(self):
        i_to_replace = self._find_next_regex_occurrence(r"\+?[1-9][0-9]{7,14}", self.iterator + 1)
        if i_to_replace == -1 or i_to_replace - self.iterator > 5:
            print(f"'Warning: \"{self.read_data['text'][self.iterator]}\" found, "
                  f"but failed to find phone number to replace.")
            return
        self._add_to_dict(i_to_replace, 'phone_number')
        self.iterator = i_to_replace

    def process_adres(self):
        # print("Adres found")
        pass

    @staticmethod
    def _fuzzy_match(keyword, text):
        similarity_score = fuzz.ratio(keyword.lower(), text.lower())

        if similarity_score >= 80:
            return True
        else:
            return False

    def _find_next_regex_occurrence(self, pattern, start_pos):
        """
        Finds next instance of a word made out of at least two letters
        :param start_pos: position from which you want to start looking
        :return: position of next word occurrence, if it doesn't find anything, returns 0
        """
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

    def _next_date_position_and_formatting(self, start_pos):
        output = output_2 = None
        regex = r"\d{2}([-.\/])\d{2}\1\d{4}"
        date_location = self._find_next_regex_occurrence(regex, start_pos)
        if date_location != -1:
            date = self.read_data['text'][date_location]

            if '-' in date:
                output = [date_location, re.sub(regex, "%d-%m-%Y", date)]
            elif '.' in date:
                output = [date_location, re.sub(regex, "%d.%m.%Y", date)]
            elif '/' in date:
                output = [date_location, re.sub(regex, "%d/%m/%Y", date)]

        regex = r"\d{4}([-.\/])\d{2}\1\d{2}"
        date_location = self._find_next_regex_occurrence(regex, start_pos)
        if date_location != -1:
            date = self.read_data['text'][date_location]

            if '-' in date:
                output_2 = [date_location, re.sub(regex, "%Y-%m-%d", date)]
            elif '.' in date:
                output_2 = [date_location, re.sub(regex, "%Y.%m.%d", date)]
            elif '/' in date:
                output_2 = [date_location, re.sub(regex, "%Y/%m/%d", date)]

        if output is None and output_2 is None:
            return -1, ''
        elif output_2 is None:
            return output
        elif output is None:
            return output_2
        elif output[0] < output_2[0]:
            return output
        elif output_2[0] < output[0]:
            return output_2
