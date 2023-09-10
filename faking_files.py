import random
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fuzzywuzzy import fuzz

import fake_data_creator
import utils

FONT_PATH = 'data/sources/Arial.ttf'


class FakingFiles:

    def __init__(self, init_cv2_image, read_data, file_type):
        if file_type not in ['hospital_sheet', 'invoice']:
            utils.err_exit("Unknown document type")

        self.file_type = file_type
        self.init_image = init_cv2_image
        self.read_data = read_data
        self.fake_data = fake_data_creator.FakeDataCreator()
        self.data_to_change = {'type': [],  # what type of word should it be replaced with, e.g. first_name
                               'top': [],  # coordinates of top border
                               'left': [],  # coordinate of left border
                               'width': [],  # width of box
                               'height': []  # height of box
                               }
        self._i = 0  # used to iterate through data from tesseract
        self._date_formats = []  # stores format of dates in order
        self._prices_list = []
        self._scan_document()

    def _scan_document(self):
        if self.file_type == 'hospital_sheet':
            keyword_functions = {
                'pacjent': self.process_patient,
                'płeć': self.process_sex,
                'pesel': self.process_pesel,
                'data': self.process_date,
                'godzina': self.process_hour,
                'numer telefonu': self.process_phone_number,
                'tel. kontaktowy': self.process_phone_number,
                'telefon kontaktowy': self.process_phone_number,
                'numer kontaktowy': self.process_phone_number,
                'adres': self.process_address,
            }
        elif self.file_type == 'invoice':
            keyword_functions = {
                'Sprzedawca': self.process_participant,
                'Nabywca': self.process_participant,
                'Odbiorca': self.process_participant,
                'netto': self.process_price,
                'vat': self.process_price,
                'brutto': self.process_price,
            }
        else:
            utils.err_exit("Unknown file type")

        next_date = None
        # Iterate over the detected text regions
        while self._i < len(self.read_data['text']):
            curr_word = self.read_data['text'][self._i]
            for keyword, func in keyword_functions.items():
                # check if current word or two next words match with keyword
                if self._fuzzy_match(keyword, curr_word):
                    func()
                # if the curr_word is longer than 1 word, fuzzy match 2 words (if they exist)
                elif len(curr_word.split()) > 1 and len(self.read_data['text']) > self._i + 1 and \
                        self._fuzzy_match(keyword, curr_word + ' ' + self.read_data['text'][self._i + 1]):
                    func()

            # fake all dates on invoices
            if self.file_type == 'invoice':
                if next_date is None:
                    next_date, formatting = self._next_date_position_and_formatting(self._i)
                if next_date == self._i:
                    self._add_to_dict(next_date, 'date')
                    self._date_formats.append(formatting)
                    next_date, formatting = self._next_date_position_and_formatting(self._i + 1)

            self._i += 1

    def create_altered_file(self, cv_image):
        """
        Creates files with faked data on them and information what has changed
        :param cv_image: image read by OpenCV
        :return: list of dictionaries containing information of what changed in a file
        """
        iterators = {
            'net': 0,
            'vat': 0,
            'gross': 0,
            'date': 0,
        }
        person = self.fake_data.create_person()
        dates = self.fake_data.create_dates()
        phone_number = self.fake_data.create_phone_number()
        address = self.fake_data.create_address()
        rand_price_multiplier = random.uniform(0.7, 1.3)

        if self.file_type == 'hospital_sheet':
            keyword_to_name = {  # converts keyword to proper faked text
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
            }
        elif self.file_type == 'invoice':
            buyer = self.fake_data.create_company()
            seller = self.fake_data.create_company()
            recipient = self.fake_data.create_company()
            keyword_to_name = {
                'seller_name': seller['name'],
                'seller_zip_and_city': seller['zip_and_city'],
                'seller_street': seller['street'],
                'seller_zip_city_street': buyer['zip_and_city'] + ', ' + buyer['street'],
                'seller_NIP': seller['NIP'],
                'buyer_name': buyer['name'],
                'buyer_zip_and_city': buyer['zip_and_city'],
                'buyer_street': buyer['street'],
                'buyer_zip_city_street': buyer['zip_and_city'] + ', ' + buyer['street'],
                'buyer_NIP': buyer['NIP'],
                'recipient_name': recipient['name'],
                'recipient_zip_and_city': recipient['zip_and_city'],
                'recipient_street': recipient['street'],
                'recipient_zip_city_street': buyer['zip_and_city'] + ', ' + buyer['street'],
                'recipient_NIP': recipient['NIP'],
                'full_name': person['first_name'] + ' ' + person['last_name'],
                'zip_and_city': buyer['zip_and_city'],
                'street': buyer['street'],
                'date': dates['start_date'],
                'net_price': 'net',  # all prices are stored in prices dict
                'vat_price': 'vat',
                'gross_price': 'gross',
                'blank': ' ',
            }

        changes_in_file = []  # list of boxes changed
        # Iterate over the detected text regions
        for i in range(len(self.data_to_change['type'])):
            # Extract the text and its bounding box coordinates
            current_keyword = self.data_to_change['type'][i]

            if 'date' in current_keyword:
                text = keyword_to_name[current_keyword].strftime(self._date_formats[iterators['date']])
                iterators['date'] += 1
            elif 'price' in current_keyword:
                true_keyword = keyword_to_name[current_keyword]
                price_iterator = iterators[true_keyword]
                text = str(round(self._prices_list[price_iterator][true_keyword] * rand_price_multiplier, 2))
                price_iterator += 1
            else:
                text = keyword_to_name[current_keyword]

            # tesseract sometimes gives boxes that are slightly too small, so I've made them slightly bigger
            x = self.data_to_change['left'][i] - 1
            y = self.data_to_change['top'][i] - 1
            width = self.data_to_change['width'][i] + 2
            height = self.data_to_change['height'][i] + 2

            # put text on the image
            colour = self._most_common_colour(cv_image)
            box_with_text = self._get_box_with_text(text, width, height, colour)
            box_width = box_with_text.shape[1]
            cv_image[y:y + height, x:x + box_width] = box_with_text
            altered_box = {
                'type': current_keyword,
                'text': text,
                'top_left': (x, y),
                'top_right': (x + box_width, y),
                'bottom_left': (x, y + height),
                'bottom_right': (x + box_width, y + height),
            }
            changes_in_file.append(altered_box)

        return changes_in_file

    def process_patient(self):
        current = self.read_data['text'][self._i].rstrip()
        if current[-1:] == 'a' or current[-2:] == 'a:':
            return  # meant for when it found "pacjenta" somewhere in the text
        # checks if it found ":" in range in case tesseract split incorrectly or imię i nazwisko is after
        up_limit = self._i + 5 if self._i + 5 < len(self.read_data['text']) \
            else len(self.read_data['text'])
        for i in range(self._i, up_limit):
            if ':' in self.read_data['text'][i]:
                i_to_replace = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i + 1)  # find first name
                if i_to_replace == -1 or i_to_replace - i > 5:
                    print(f"Warning: \"{self.read_data[i_to_replace]}\" found, "
                          f"but no following string, replacement was not successful.")
                    return
                self._i = i_to_replace

                i_last_name = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i_to_replace + 1)  # find last name
                if i_last_name == -1 or i_last_name - i > 5:
                    print(f"Warning: \"{self.read_data[i_to_replace]}\" found, but failed to replace last name.")
                    self._add_to_dict(i_to_replace, 'first_name')  # add only first name
                    return
                self._add_to_dict_multiple_merge(i_to_replace, 'full_name', 2)  # replace both first_name and last_name
                self._i = i_last_name
                return

        print('Warning: "Pacjent" found, but could not detect a place to swap')

    def process_sex(self):
        i_to_replace = self._find_next_regex_occurrence(r"^(M|F)$", self._i + 1)
        if i_to_replace == -1 or i_to_replace - self._i > 5:
            print(f"'Warning: \"{self.read_data['text'][self._i]}\" found, "
                  f"but failed to find sex to replace.")
            return
        self._add_to_dict(i_to_replace, 'sex')
        self._i = i_to_replace

    def process_pesel(self):
        i_to_replace = self._find_next_regex_occurrence(r"^\d{11}$", self._i + 1)
        if i_to_replace == -1 or i_to_replace - self._i > 5:
            print(f"'Warning: \"{self.read_data['text'][self._i]}\" found, "
                  f"but failed to find pesel to replace.")
            return
        self._add_to_dict(i_to_replace, 'pesel')
        self._i = i_to_replace

    def process_date(self):

        # find the nearest words to verify what type of date it is
        nearest_words = []
        range_limit = self._i + 4
        for i in range(self._i, range_limit):
            i_of_next_word = self._find_next_regex_occurrence(r"[A-Za-z]{2,}", i)
            if i_of_next_word != -1 and i_of_next_word < range_limit:
                next_word = self.read_data['text'][i]
                nearest_words.append(next_word)

        for word in nearest_words:
            if self._fuzzy_match('urodzenia', word):
                i_to_replace, formatting = self._next_date_position_and_formatting(self._i + 1)
                if -1 < i_to_replace - self._i < 10:
                    self._add_to_dict(i_to_replace, 'birthdate')
                    self._date_formats.append(formatting)
                    return
                print(f"'Warning: \"{self.read_data['text'][self._i]}\" and \"{word}\" found, "
                      f"but failed to find date to replace.")

            for option in ['koniec', 'wypisu']:
                if self._fuzzy_match(option, word):
                    i_to_replace, formatting = self._next_date_position_and_formatting(self._i + 1)
                    if -1 < i_to_replace - self._i < 10:
                        self._add_to_dict(i_to_replace, 'end_date')
                        self._date_formats.append(formatting)
                        return
                    print(f"'Warning: \"{self.read_data['text'][self._i]}\" and \"{word}\" found, "
                          f"but failed to find date to replace.")

        # if neither birthdate nor end date, use start date
        i_to_replace, formatting = self._next_date_position_and_formatting(self._i + 1)
        if -1 < i_to_replace - self._i < 10:
            self._add_to_dict(i_to_replace, 'start_date')
            self._date_formats.append(formatting)
            return
        print(f"'Warning: \"{self.read_data['text'][self._i]}\" found, "
              f"but failed to find date to replace.")

    def process_hour(self):
        i_to_replace = self._find_next_regex_occurrence(r"([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]", self._i + 1)
        if i_to_replace == -1 or i_to_replace - self._i > 5:
            print(f"'Warning: \"{self.read_data['text'][self._i]}\" found, "
                  f"but failed to find time to replace.")
            return
        self._add_to_dict(i_to_replace, 'time')
        self._i = i_to_replace

    def process_phone_number(self):
        i_to_replace = self._find_next_regex_occurrence(r"\+?[1-9][0-9]{7,14}", self._i + 1)
        if i_to_replace == -1 or i_to_replace - self._i > 5:
            print(f"'Warning: \"{self.read_data['text'][self._i]}\" found, "
                  f"but failed to find phone number to replace.")
            return
        self._add_to_dict(i_to_replace, 'phone_number')
        self._i = i_to_replace

    def process_address(self):
        # checks if it found ":" in range in case tesseract split incorrectly or some text after
        up_limit = self._i + 5 if self._i + 5 < len(self.read_data['text']) \
            else len(self.read_data['text'])
        for i in range(self._i, up_limit):
            if ':' in self.read_data['text'][i]:
                i_to_replace = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i + 1)  # find city or street
                if i_to_replace == -1 or i_to_replace - i > 5:
                    print(f"Warning: \"{self.read_data[self._i]}\" found, "
                          f"but no following string, replacement not successful.")
                    return
                # check if next is number, indicating that it's a street and its number, not city
                next_number = self._find_next_regex_occurrence(r"\d+/\d+", i_to_replace + 1)
                next_word = self._find_next_regex_occurrence(r"[a-zA-Z]{2,}", i_to_replace + 1)
                if next_number < next_word:
                    self._add_to_dict_multiple_merge(i_to_replace, 'street', next_number - i_to_replace + 1)
                    self._add_to_dict(next_word, 'city')
                    self._i = next_word
                else:
                    # city first, street after
                    self._add_to_dict(i_to_replace, 'city')
                    self._add_to_dict_multiple_merge(next_word, 'street', next_number - next_word + 1)
                    self._i = next_number - next_word + 1
                return

        print(f"Warning: \"{self.read_data[self._i]}\" found, "
              f"but no following string, replacement not successful.")

    def process_participant(self):
        participant = self.read_data['text'][self._i]
        # prefixes only applicable only if party is a company
        if 'sprzedawca' in participant.lower():
            prefix = 'seller_'
        elif 'nabywca' in participant.lower():
            prefix = 'buyer_'
        elif 'odbiorca' in participant.lower():
            prefix = 'recipient_'
        else:
            return

        x_min = self.read_data['left'][self._i]
        x_max = self.read_data['left'][self._i] + self.read_data['width'][self._i]
        name_i = self._find_regex_occurrence_below(r"[A-Za-z]{3,}", self._i, (x_min, x_max))
        zip_and_city_i = self._find_regex_occurrence_below(r"^\d{2}-\d{3}$", name_i, (x_min, x_max))
        street_i = self._find_regex_occurrence_below(r"[A-Za-z]{3,}", name_i, (x_min, x_max))

        if name_i == -1 or zip_and_city_i == -1 or street_i == -1:
            print(f"Warning: Found \"{self.read_data['text'][self._i]}\", but "
                  f"could not find full information about the party")
            return

        # handles address
        zip_and_city_data = self._find_nearby_words(zip_and_city_i)
        # if one of the 2 last chars is a digit, it also contains the street
        print(zip_and_city_data[2]) #db
        if zip_and_city_data[2][-1].isdigit() or zip_and_city_data[2][-2].isdigit():
            self._add_to_dict_multiple_merge(zip_and_city_data[0], 'zip_city_street',
                                             zip_and_city_data[1] - zip_and_city_data[0] + 1)
        else:
            if self._are_on_same_height(street_i, zip_and_city_i):  # make sure they're on different lines
                street_i = self._find_regex_occurrence_below(r"[A-Za-z]{3,}", street_i, (x_min, x_max))
                if street_i == -1:  # check again
                    print(f"Warning: Found \"{self.read_data['text'][self._i]}\", but "
                          f"could not find party's street name")
                    return

            full_street_name = self._find_nearby_words(street_i)[2]
            # look for address - word(s) that end with a number or number and a letter
            while street_i != -1 and not (full_street_name[-1].isdigit() or full_street_name[-2].isdigit()) and \
                    full_street_name.len() < 30:
                street_i = self._find_regex_occurrence_below(r"[A-Za-z]{3,}", street_i, (x_min, x_max))
                full_street_name = self._find_nearby_words(street_i)[2]
            if street_i == -1:
                print(f"Warning: Found \"{self.read_data['text'][self._i]}\", but "
                      f"could not find party's street name")
            self._find_nearby_and_add_to_dict(zip_and_city_i, 'zip_and_city')
            self._find_nearby_and_add_to_dict(street_i, 'street')

        # if no NIP, it's a private person
        NIP = self._find_regex_occurrence_below(r"^NIP:?$", name_i, (x_min, x_max))
        if NIP == -1:
            print(f"Warning: Found \"{self.read_data['text'][self._i]}\", but could not find \"NIP\". "
                  f"Assuming it's a private person.")
            self._find_nearby_and_add_to_dict(name_i, 'full_name')
        else:   # if company
            NIP_num = self._find_next_regex_occurrence(r"^\d{10}$", NIP)
            if NIP_num == -1 or NIP - NIP_num > 5:
                # different name and no NIP if private person in the off-chance there is word "NIP", but no number
                print(f"Warning: Found \"{self.read_data['text'][self._i]}\" and "
                      f"\"{self.read_data['text'][NIP]}\", but couldn't find company's NIP number. "
                      f"Assuming it's a private person")
                self._find_nearby_and_add_to_dict(name_i, 'full_name')
            else:
                self._find_nearby_and_add_to_dict(name_i, prefix + 'name')
                self._add_to_dict(NIP_num, prefix + 'NIP')

    def process_price(self):
        fuzzy_price_type = self.read_data['text'][self._i]
        if self._fuzzy_match(fuzzy_price_type, 'netto'):
            price_type = 'net_price'
        elif self._fuzzy_match(fuzzy_price_type, 'vat'):
            if self._fuzzy_match(self.read_data['text'][self._i - 1], 'faktura'):
                return
            else:
                price_type = 'vat_price'
        elif self._fuzzy_match(fuzzy_price_type, 'brutto'):
            price_type = 'gross_price'
        else:
            utils.err_exit("Unknown price type")

        # get the closest price and string below, once price is below string, it means we've found all relevant prices
        x_min = self.read_data['left'][self._i]
        x_max = self.read_data['left'][self._i] + self.read_data['width'][self._i]
        next_price_i = self._find_regex_occurrence_below(r"\d+[.,]\d+", self._i, (x_min, x_max))
        price_column_end = self._find_regex_occurrence_below(r"[A-Za-z]{3,}", self._i, (x_min, x_max))

        if next_price_i == -1:
            print(f"Warning: Price below \"{self.read_data['text'][self._i]}\" not found.")
            return
        if price_column_end == -1:
            next_string_top = self.init_image.shape[0]  # height of image
        elif self._are_on_same_height(next_price_i, price_column_end):
            price_column_end = self._find_regex_occurrence_below(r"[A-Za-z]{3,}", price_column_end, (x_min, x_max))
            if price_column_end == -1:
                next_string_top = self.init_image.shape[0]
            else:
                next_string_top = self.read_data['top'][price_column_end]
        else:
            next_string_top = self.read_data['top'][price_column_end]

        while self.read_data['top'][next_price_i] < next_string_top and next_price_i != -1:
            # change to int
            next_price_int = self.read_data['text'][next_price_i]
            next_price_int = re.sub(r"[^0-9.,]", '', next_price_int)  # clean the number
            if ',' in next_price_int:
                next_price_int = float(next_price_int.replace(',', '.'))
            else:
                next_price_int = float(next_price_int)

            # create prices and append them where needed
            if price_type == 'net_price':
                self._prices_list.append(self.fake_data.create_prices(next_price_int))
            self._add_to_dict(next_price_i, price_type)

            # iterate to next price
            next_price_i = self._find_regex_occurrence_below(r"\d+([.,]\d+)?", next_price_i, (x_min, x_max))
            # verify if price and column end aren't on the same height - if they are, column end is text like PLN and
            # not actual end of prices
            if self._are_on_same_height(next_price_i, price_column_end):
                price_column_end = self._find_regex_occurrence_below(r"[A-Za-z]{3,}", price_column_end, (x_min, x_max))
                if price_column_end == -1:
                    next_string_top = self.init_image.shape[0]

    def _find_next_regex_occurrence(self, pattern, start_pos):
        """
        Finds next instance of a word according to a regex pattern
        :param pattern: regex pattern to find
        :param start_pos: position from which you want to start looking
        :return: position of next word occurrence, if it doesn't find anything, returns -1
        """
        for i in range(start_pos, len(self.read_data['text'])):
            if re.search(pattern, self.read_data['text'][i]):
                return i

        return -1

    def _find_regex_occurrence_below(self, pattern, start_pos, x_range):
        """
        Finds next instance of a word below according to regex pattern. If there are multiple words underneath
        in the same line, prioritizes the leftmost word
        :param pattern: regex pattern to find
        :param start_pos: index of a word from which to start looking
        :param x_range: range (min_x, max_x) in which at least part of the word is found
        :return: Index of next word occurrence, if it doesn't find anything, returns -1
        """

        min_x, max_x = x_range
        start_top = self.read_data['top'][start_pos]

        # if direction == 'up':
        #     i_range = range(start_pos, -1, -1)
        # else:
        #     i_range = range(start_pos, len(self.read_data['text']))

        best_pos = -1
        best_top = self.init_image.shape[0]     # height of the image

        for i in range(start_pos, len(self.read_data['text'])):
            text = self.read_data['text'][i]
            top = self.read_data['top'][i]
            left_border = self.read_data['left'][i]
            right_border = self.read_data['left'][i] + self.read_data['width'][i]

            # if pattern matches AND more or less below the word AND are not at the same height AND
            # below the starting position
            if re.search(pattern, text) and \
                    (
                            min_x < left_border < max_x or min_x < right_border < max_x or
                            left_border < min_x < right_border or left_border < max_x < right_border
                    ) and \
                    not self._are_on_same_height(start_pos, i) and \
                    top > start_top:
                # check if better than current best
                if best_top > top:
                    best_top = top
                    best_pos = i

        for i in range(start_pos, -1, -1):
            text = self.read_data['text'][i]
            top = self.read_data['top'][i]
            left_border = self.read_data['left'][i]
            right_border = self.read_data['left'][i] + self.read_data['width'][i]
            # if pattern matches AND more or less below the word AND are not at the same height AND
            # below the starting position
            if re.search(pattern, text) and \
                    (
                            min_x < left_border < max_x or min_x < right_border < max_x or
                            left_border < min_x < right_border or left_border < max_x < right_border
                    ) and \
                    not self._are_on_same_height(start_pos, i) and \
                    top > start_top:
                # check if better than current best
                if best_top < top:
                    best_top = top
                    best_pos = i

        return best_pos

    def _find_nearby_words(self, index):
        """
        Finds nearby words, both backwards and forwards and outputs start, end and the whole found string
        :param index: starting position from which to start looking (both backwards and forwards)
        :return: [start, end, output_string], where 'start' and 'end' are indexes marking location of the found string,
        and 'output_string' is the concatenated string with spaces
        """
        max_distance = self.read_data['height'][index]  # max distance between words
        start = index
        end = index
        output_string = ''
        # first check backwards
        for i in range(index, 0, -1):
            curr_left = self.read_data['left'][i]
            prev_right = self.read_data['left'][i - 1] + self.read_data['width'][i - 1]

            # check if close enough and not in another row
            if not (0 < curr_left - prev_right < max_distance) or not self._are_on_same_height(i, i - 1):
                start = i
                break

        for i in range(start, len(self.read_data['text'])):
            output_string += self.read_data['text'][i] + ' '

            if i + 1 >= len(self.read_data['text']):  # check if next exists
                end = i
                break
            curr_right = self.read_data['left'][i] + self.read_data['width'][i]
            next_left = self.read_data['left'][i + 1]

            # check if close enough and not in another row
            if not (0 < next_left - curr_right < max_distance) or not self._are_on_same_height(i, i + 1):
                end = i
                break
        return start, end, output_string.strip()

    def _add_to_dict(self, position, type_of_data):
        # check if not already edited
        for i in range(len(self.data_to_change['type'])):
            if self.data_to_change['top'][i] == self.read_data['top'][position] and \
                    self.data_to_change['left'][i] == self.read_data['left'][position] and \
                    self.data_to_change['width'][i] == self.read_data['width'][position] and \
                    self.data_to_change['height'][i] == self.read_data['height'][position]:
                print(f"Warning: Trying to overwrite already detected box. Type of data: {type_of_data}")
                return

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
        top = float('inf')
        bottom = 0
        left = float('inf')
        right = 0
        for i in range(num_to_merge):
            curr_top = self.read_data['top'][position + i]
            curr_left = self.read_data['left'][position + i]
            curr_width = self.read_data['width'][position + i]
            curr_height = self.read_data['height'][position + i]

            top = min(top, curr_top)
            bottom = max(bottom, curr_top + curr_height)
            left = min(left, curr_left)
            right = max(right, curr_left + curr_width)

        self.data_to_change['top'].append(top)
        self.data_to_change['left'].append(left)
        self.data_to_change['width'].append(right - left)
        self.data_to_change['height'].append(bottom - top)

    def _find_nearby_and_add_to_dict(self, position, type_of_data):
        start, end, text = self._find_nearby_words(position)
        self._add_to_dict_multiple_merge(start, type_of_data, end - start + 1)

    def _next_date_position_and_formatting(self, start_pos):
        """
        Returns index at which next date is found and how it is formatted
        :param start_pos: position from which it should look for date
        :return: returns a list with [index, formatting] where first one is information about where date is
                 and formatting is the formatting of date compatible with datetime.strftime()
        """
        output = None  # they store [date_location, date_formatting]
        output_2 = None
        regex = r"^\d{2}([-.\/])\d{2}\1\d{4}$"
        date_location = self._find_next_regex_occurrence(regex, start_pos)
        if date_location != -1:
            date = self.read_data['text'][date_location]

            if '-' in date:
                output = [date_location, "%d-%m-%Y"]
            elif '.' in date:
                output = [date_location, "%d.%m.%Y"]
            elif '/' in date:
                output = [date_location, "%d/%m/%Y"]

        regex = r"^\d{4}([-.\/])\d{2}\1\d{2}$"
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
        elif output_2 is None:
            return output
        elif output is None:
            return output_2
        elif output[0] < output_2[0]:
            return output
        elif output_2[0] <= output[0]:
            return output_2

    def _are_on_same_height(self, index_1, index_2):
        top_1 = self.read_data['top'][index_1]
        top_2 = self.read_data['top'][index_2]
        max_misalignment = max(self.read_data['height'][index_1], self.read_data['height'][index_2])
        return True if abs(top_1 - top_2) < max_misalignment else False

    @staticmethod
    def _get_box_with_text(text, width, height, colour):
        text_box = Image.new('RGB', (width, height), colour)

        fontsize = 1
        font = ImageFont.truetype(FONT_PATH, fontsize)

        # iterate until the text size is just larger than the criteria
        while font.getbbox(text)[3] < text_box.height:
            fontsize += 1
            font = ImageFont.truetype(FONT_PATH, fontsize)

        if font.getlength(text) > text_box.width:
            text_box = text_box.resize((int(font.getlength(text, language='pl')), text_box.height))

        draw = ImageDraw.Draw(text_box)
        draw.text((0, 0), text, font=font, fill=(0, 0, 0, 255))  # put text on img

        return utils.pil_image_to_cv2(text_box)  # return in cv2 format

    @staticmethod
    def _fuzzy_match(keyword, text):
        similarity_score = fuzz.ratio(keyword.lower(), text.lower())

        if similarity_score >= 85:
            return True
        else:
            return False

    @staticmethod
    def _most_common_colour(cv2_image):
        a2D = cv2_image.reshape(-1, cv2_image.shape[-1])
        col_range = (256, 256, 256)  # generically : a2D.max(0)+1
        a1D = np.ravel_multi_index(a2D.T, col_range)
        return np.unravel_index(np.bincount(a1D).argmax(), col_range)
