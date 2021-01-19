from cs50 import get_string
import math


number = get_string("number: ")

sep = [int(i) for i in str(number)]                 # turns str(123) into [1,2,3]

even_sum = 0
for i in range(len(sep) - 2, -1, -2):               # starting from 2nd to last and counting down
    j = 2 * sep[i]                                  # multiply each digit by two
    k = [int(i) for i in str(j)]
    even_sum += sum(k)                              # sum the two digits of the number


odd_sum = 0
for i in range(len(sep) - 1, -1, -2):               # we start counting from len to -1 to also count sep[0]
    odd_sum += sep[i]


z = math.floor(int(number) / 10 ** 14)              # to extract the first two digits of a 16 digit number
x = math.floor(int(number) / 10 ** 13)              # to extract the first two digits of a 15 digit number


if (even_sum + odd_sum) % 10 != 0:
    print ("INVALID")

elif z > 50 and z < 56:
    print("MASTERCARD")

elif x == 34 or x == 37:
    print("AMEX")

elif math.floor(int(number) / 10 **15) == 4:
    print("VISA")

elif math.floor(int(number) / 10 ** 12) == 4:
    print("VISA")

else:
    print ("INVALID")
