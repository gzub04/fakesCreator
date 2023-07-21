import csv

with open('male_lastnames_.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # skip the first row
    first_column = []
    i = 0
    for row in reader:
        if i == 600:
            break
        i += 1
        first_column.append(row[0])

with open('male_lastnames.csv', mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    for name in first_column:
        writer.writerow([name])
