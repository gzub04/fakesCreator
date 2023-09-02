from random import randint, choice
import datetime
import sys

SOURCE_FILES = "Data/sources"


def err_exit(err_msg):
    print(f'Error: {err_msg}', file=sys.stderr)
    exit(1)


class FakeDataCreator:
    def __init__(self):
        try:
            with open(f'{SOURCE_FILES}/male_firstnames.csv', 'r', encoding='utf-8') as f_male_first_names, \
                    open(f'{SOURCE_FILES}/male_lastnames.csv', 'r', encoding='utf-8') as f_male_last_names, \
                    open(f'{SOURCE_FILES}/female_firstnames.csv', 'r', encoding='utf-8') as f_female_first_names, \
                    open(f'{SOURCE_FILES}/female_lastnames.csv', 'r', encoding='utf-8') as f_female_last_names, \
                    open(f'{SOURCE_FILES}/cities.csv', 'r', encoding='utf-8') as f_cities, \
                    open(f'{SOURCE_FILES}/street_names.csv', 'r', encoding='utf-8') as f_streets:

                self.male_first_names = f_male_first_names.readlines()
                self.male_last_names = f_male_last_names.readlines()
                self.female_first_names = f_female_first_names.readlines()
                self.female_last_names = f_female_last_names.readlines()

                self.street_names = f_streets.readlines()
                self.cities_data = []  # list in format [(city, population)]
                for line in f_cities:
                    city, population = line.strip().split(';')
                    self.cities_data.append((city, int(population)))

        except FileNotFoundError:
            print(f"File Not Found Error: Missing csv files in {SOURCE_FILES}.")
            exit(1)
        except PermissionError:
            print(f"Permission Error: Can't access csv files in {SOURCE_FILES}.")
            exit(1)
        except Exception as e:
            print(f"An error occurred while opening csv files in {SOURCE_FILES}: {str(e)}")
            exit(1)

    def create_person(self):
        """
        Creates a dictionary with randomly generated person's data.
        :return: Dictionary with keys: first_name, last_name, sex, birthdate and PESEL.
        birthdate is datetime datatype, all others are strings
        """
        person = {'sex': choice(['M', 'F'])}

        if person['sex'] == 'M':
            person['first_name'] = choice(self.male_first_names).rstrip('\n').capitalize()
            person['last_name'] = choice(self.male_last_names).rstrip('\n').capitalize()
        else:
            person['first_name'] = choice(self.female_first_names).rstrip('\n').capitalize()
            person['last_name'] = choice(self.female_last_names).rstrip('\n').capitalize()

        # generate birthdate date from 23 to 60 years ago
        person['birthdate'] = datetime.date.today() - datetime.timedelta(days=(randint(23, 60) * 365))

        # PESEL
        p_year = str(person['birthdate'].year)[-2:]  # last two digits of year

        p_month = ''
        if 1800 <= person['birthdate'].year < 1900:
            p_month = str(person['birthdate'].month + 80)
        elif person['birthdate'].year < 2000:
            if person['birthdate'].month < 10:
                p_month = '0'
            p_month += str(person['birthdate'].month)
        elif person['birthdate'].year < 2100:
            p_month = str(person['birthdate'].month + 20)
        else:
            err_exit('Birth year is not between 1800-2100')

        if person['birthdate'].day < 10:
            p_day = '0' + str(person['birthdate'].day)
        else:
            p_day = str(person['birthdate'].day)

        p_ordinal_number = ''.join([str(randint(0, 9)) for _ in range(3)])
        if person['sex'] == 'M':
            p_ordinal_number += str(randint(0, 4) * 2 + 1)
        else:
            p_ordinal_number += str(randint(0, 4) * 2)

        pesel_wo_last_number = p_year + p_month + p_day + p_ordinal_number

        factors = [1, 3, 7, 9]
        result_sum = 0
        for i in range(10):
            digit = int(pesel_wo_last_number[i])
            result_sum += digit * factors[i % 4]
        p_control_number = result_sum % 10

        person['pesel'] = pesel_wo_last_number + str(p_control_number)

        return person

    def create_address(self):
        """
        Creates a dictionary containing random address
        :return: Dictionary with keys: city, street.
        Street contains both street name and house number with apartment number (if apartment number is generated)
        """
        address = dict()

        total_population = sum(population for _, population in self.cities_data)
        # Chooses city with higher chance for the city to be more populated
        random_number = randint(1, total_population)
        cumulative_population = 0
        for city, population in self.cities_data:
            cumulative_population += population
            if cumulative_population >= random_number:
                address['city'] = city
                break

        address['street'] = choice(self.street_names).rstrip('\n') + ' ' + str(randint(1, 100))

        if randint(1, 100) > 55:  # chance for someone to live in a flat
            address['street'] += '/' + str(randint(1, 100))
        return address

    @staticmethod
    def create_dates():
        """
        Creates a pair of dates in the past, where second date happens 1-7 days after the first one
        :return: Dictionary containing keys 'start_date' and 'end_date' that hold datetime() type as values
        """
        dates = dict()

        # Generate a random start date between 7 days and 20 years ago
        dates['start_date'] = datetime.datetime.now() - datetime.timedelta(days=randint(7, 365 * 20))
        dates['start_date'] = dates['start_date'].replace(hour=randint(10, 18), minute=randint(0, 59))

        # Generate random discharge date between 1 and 7 days after the arrival date
        dates['end_date'] = dates['start_date'] + datetime.timedelta(days=randint(1, 5))
        dates['end_date'] = dates['end_date'].replace(hour=randint(10, 18), minute=randint(0, 59))

        return dates

    @staticmethod
    def create_phone_number():
        phone_number = str(randint(5, 8))  # first digit
        phone_number += ''.join([str(randint(0, 9)) for _ in range(8)])  # remaining digits
        return phone_number
