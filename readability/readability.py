from cs50 import get_string


t = get_string("Text: ")

# count the number of word in a string
words = len(t.split())
# count sentences ending in .!?
sentences = t.count('.') + t.count('?') + t.count('!')
# count number of letters in a string
letters = 0
for i in t:
    if i.isalpha():
        letters += 1

L = 100 * letters / words
S = 100 * sentences / words

index = round(0.0588 * L - 0.296 * S - 15.8)

if index > 16:
    print("Grade 16+")
    
elif index < 1:
    print("Before Grade 1")
    
else:
    print(f"Grade {index}")
