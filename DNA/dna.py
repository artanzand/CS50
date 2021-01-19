from sys import argv, exit
import csv

# checking if 3 values have been entered in command-line
if len(argv) != 3:
    print("Usage: python dna.py data.csv sequence.txt")
    exit(1)

# list of STR counts for the sequence
STR_counts = []

# read sequence to figure out the STR count storing them in a list
sequence = open(argv[2], "r")
S = sequence.read()

# read data in a list to extract STR names
with open(argv[1], "r") as data:
    reader = csv.reader(data)
    headings = next(reader)             # read the first line (column titles) into a list
    headings.pop(0)                     # remove the "name" column title
    for STR in headings:
        # figure out the highest consecutive count
        max_count = 0
        for x in range(len(S)):
            count = 0
            for j in range(x, len(S), len(STR)):
                # checking the substring from j to j+len(STR) character
                if S[j:(j+len(STR))] == STR:
                    count += 1
                else:
                    break

           # store the biggest consecutive count
            if count > max_count:
                    max_count = count

        # create a list of all STR counts to be used below
        STR_counts.append(max_count)


# read data file in a dictionary to compare values
# use boolean found to track a matched row
found = False
with open (argv[1], 'r') as data:
    reader = csv.reader(data)
    next(reader)
    for row in reader:

        # save the name and remove it from row
        name = row[0]
        row.pop(0)

        # changing str to int to allow comparison
        for i in range(0, len(row)):
            row[i] = int(row[i])

        # compare the row with the STR counts
        if row == STR_counts:
            print(name)
            found = True
            exit

    # if no match found
    if not found:
        print("No match")
