import cv2
import re

from PIL import Image, ImageDraw, ImageFont
from fuzzywuzzy import fuzz

import fake_data_creator
import utils

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
        self.date_formats = []      # stores format of dates in order
        self._scan_document()

    def _scan_document(self):
        keyword_functions = {
            'pacjent': self.process_pacjent,
            'płeć': self.process_plec,
            'pesel': self.process_pesel,
            'data': self.process_date,
            'godzina': self.process_godzina,
            'numer telefonu': self.process_phone_number,
            'tel. kontaktowy': self.process_phone_number,
            'telefon kontaktowy': self.process_phone_number,
            'numer kontaktowy': self.process_phone_number,
            'adres': self.process_adres,
        }

        # Iterate over the detected text regions
        while self.iterator < len(self.read_data['text']):
            curr_word = self.read_data['text'][self.iterator]
            for keyword, func in keyword_functions.items():
                # check if current word or two next words match with keyword
                if self._fuzzy_match(keyword, curr_word) or (len(self.read_data['text']) > self.iterator + 1 and
                   self._fuzzy_match(keyword, curr_word + ' ' + self.read_data['text'][self.iterator + 1])):
                    func()

            self.iterator += 1

    def create_altered_file(self, cv_image):
        """
        Creates files with faked data on them and information what has changed
        :param cv_image: image read by OpenCV
        :return: list of dictionaries containing information of what changed in a file
        """
        date_iterator = 0
        person = self.fake_data.create_person()
        dates = self.fake_data.create_dates()
        phone_number = self.fake_data.create_phone_number()
        address = self.fake_data.create_address()

        keyword_to_name = {    # converts keyword to proper faked text
            'first_name': person['first_name'],
            'last_name': person['last_name'],
            'full_name': person['first_name'] + ' ' + person['last_name'],
            'pesel': person['pesel'],
            'sex': person['sex'],
            'birthdate': person['birthdate'],
            'start_date': dates['start_date'],
            'end_date': dates['end_date'],
            'time': dates['start_date'].strftime("%H:%M"),
            'phone_number': phone_number,
            'city': address['city'],
            'street': address['street'],
            'blank': '',
        }

        changes_in_file = []  # list of boxes changed
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

            # put text on the image
            box_with_text = self._get_box_with_text(text, width, height)
            box_width = box_with_text.shape[1]
            cv_image[y:y+height, x:x+box_width] = box_with_text
            # debug showcase
            # cv2.rectangle(cv_image, (x, y), (x + box_width, y + height), (0, 255, 0), 2)
            # cv2.putText(cv_image, text, (x, y - 10), cv2.FONT_HERSHEY_COMPLEX, height/30, (0, 255, 0), 2)
            altered_box = {
                'text': text,
                'top_left': (x, y),
                'top_right': (x + box_width, y),
                'bottom_left': (x, y + height),
                'bottom_right': (x + box_width, y + height),
            }
            changes_in_file.append(altered_box)

        return changes_in_file

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
                    print(f"Warning: \"{self.read_data[i_to_replace]}\" found, "
                          f"but no following string, replacement was not successful.")
                    return
                self.iterator = i_to_replace

                i_last_name = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i_to_replace + 1)  # find last name
                if i_last_name == -1 or i_last_name - i > 5:
                    print(f"Warning: \"{self.read_data[i_to_replace]}\" found, but failed to replace last name.")
                    self._add_to_dict(i_to_replace, 'first_name')   # add only first name
                    return
                self._add_to_dict_multiple_merge(i_to_replace, 'full_name', 2)   # replace both first_name and last_name
                self.iterator = i_last_name
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
            if i_of_next_word != -1 and i_of_next_word < range_limit:
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

    def process_godzina(self):
        i_to_replace = self._find_next_regex_occurrence(r"([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]", self.iterator + 1)
        if i_to_replace == -1 or i_to_replace - self.iterator > 5:
            print(f"'Warning: \"{self.read_data['text'][self.iterator]}\" found, "
                  f"but failed to find time to replace.")
            return
        self._add_to_dict(i_to_replace, 'time')
        self.iterator = i_to_replace

    def process_phone_number(self):
        i_to_replace = self._find_next_regex_occurrence(r"\+?[1-9][0-9]{7,14}", self.iterator + 1)
        if i_to_replace == -1 or i_to_replace - self.iterator > 5:
            print(f"'Warning: \"{self.read_data['text'][self.iterator]}\" found, "
                  f"but failed to find phone number to replace.")
            return
        self._add_to_dict(i_to_replace, 'phone_number')
        self.iterator = i_to_replace

    def process_adres(self):
        # checks if it found ":" in range in case tesseract split incorrectly or some text after
        up_limit = self.iterator + 5 if self.iterator + 5 < len(self.read_data['text']) else len(self.read_data['text'])
        for i in range(self.iterator, up_limit):
            if ':' in self.read_data['text'][i]:
                i_to_replace = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i + 1)  # find city or street
                if i_to_replace == -1 or i_to_replace - i > 5:
                    print(f"Warning: \"{self.read_data[self.iterator]}\" found, "
                          f"but no following string, replacement not successful.")
                    return
                # check if next is number, indicating that it's a street and its number, not city
                next_number = self._find_next_regex_occurrence(r"\d+/\d+", i_to_replace + 1)
                next_word = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i_to_replace + 1)
                if next_number < next_word:
                    self._add_to_dict_multiple_merge(i_to_replace, 'street', next_number - i_to_replace + 1)
                    self._add_to_dict(next_word, 'city')
                    self.iterator = next_word
                else:
                    # city first, street after
                    self._add_to_dict(i_to_replace, 'city')
                    self._add_to_dict_multiple_merge(next_word, 'street', next_number - next_word + 1)
                    self.iterator = next_number - next_word + 1
                return

        print(f"Warning: \"{self.read_data[self.iterator]}\" found, "
              f"but no following string, replacement not successful.")

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

    def _add_to_dict(self, position, type_of_data):
        self.data_to_change['type'].append(type_of_data)
        self.data_to_change['top'].append(self.read_data['top'][position])
        self.data_to_change['left'].append(self.read_data['left'][position])
        self.data_to_change['width'].append(self.read_data['width'][position])
        self.data_to_change['height'].append(self.read_data['height'][position])

    def _add_to_dict_multiple_merge(self, position, type_of_data, num_to_merge):
        """
        Adds to a dictionary multiple words in a row as a single entry, with box containing all symbols
        :param position: position in self.read_data
        :param type_of_data:
        :param num_to_merge:
        :return:
        """
        self.data_to_change['type'].append(type_of_data)
        top = 0
        bottom = float('inf')
        left = float('inf')
        right = 0
        for i in range(num_to_merge):
            curr_top = self.read_data['top'][position + i]
            curr_left = self.read_data['left'][position + i]
            curr_width = self.read_data['width'][position + i]
            curr_height = self.read_data['height'][position + i]

            top = max(top, curr_top)
            bottom = min(bottom, curr_top - curr_height)
            left = min(left, curr_left)
            right = max(right, curr_left + curr_width)

        self.data_to_change['top'].append(top)
        self.data_to_change['left'].append(left)
        self.data_to_change['width'].append(right - left)
        self.data_to_change['height'].append(top - bottom)

    def _next_date_position_and_formatting(self, start_pos):
        """
        Returns index at which next date is found and how it is formatted
        :param start_pos: position from which it should look for date
        :return: returns a list with [index, formatting] where first one is information about where date is
                 and formatting is the formatting of date compatible with datetime.strftime()
        """
        output = output_2 = None    # they store [regex, date_formatting, date]
        regex = r"\d{2}([-.\/])\d{2}\1\d{4}"
        date_location = self._find_next_regex_occurrence(regex, start_pos)
        if date_location != -1:
            date = self.read_data['text'][date_location]

            if '-' in date:
                output = [date_location, "%d-%m-%Y"]
            elif '.' in date:
                output = [date_location, "%d.%m.%Y"]
            elif '/' in date:
                output = [date_location, "%d/%m/%Y"]

        regex = r"\d{4}([-.\/])\d{2}\1\d{2}"
        date_location = self._find_next_regex_occurrence(regex, start_pos)
        if date_location != -1:
            date = self.read_data['text'][date_location]

            if '-' in date:
                output_2 = [date_location, "%Y-%m-%d"]
            elif '.' in date:
                output_2 = [date_location, "%Y.%m.%d"]
            elif '/' in date:
                output_2 = [date_location, "%Y/%m/%d"]

        if output is None and output_2 is None:
            return -1, ''
        elif output_2 is None or output[0] < output_2[0]:
            return output
        elif output is None or output_2[0] < output[0]:
            return output_2

    @staticmethod
    def _fuzzy_match(keyword, text):
        similarity_score = fuzz.ratio(keyword.lower(), text.lower())

        if similarity_score >= 80:
            return True
        else:
            return False

    @staticmethod
    def _get_box_with_text(text, width, height):
        text_box = Image.new('RGB', (width, height), color='white')

        fontsize = 1
        font = ImageFont.truetype(FONT_PATH, fontsize)

        # iterate until the text size is just larger than the criteria
        while font.getbbox(text)[3] < text_box.height:
            fontsize += 1
            font = ImageFont.truetype(FONT_PATH, fontsize)

        if font.getlength(text) > text_box.width:
            text_box = text_box.resize((int(font.getlength(text, language='pl')), text_box.height))

        draw = ImageDraw.Draw(text_box)
        draw.text((0, 0), text, font=font, fill=(0, 0, 0, 255))   # put text on img

        return utils.pil_image_to_cv2(text_box)  # return in cv2 format
