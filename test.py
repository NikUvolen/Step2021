from math import sqrt

for a in range(1, 100000):
    try:
        result = sqrt((sqrt(a ** 2 - 144) + 2) / 4) + sqrt((sqrt(a ** 2 - 144) - 2) / 4)

        if result == 3:
            print(a)
            break
    except ValueError:
        continue