for a in range(1, 101):
    if not a % 5 and not a % 3:
        print("Fizzbuzz")
    elif not a % 5:
        print("buzz")
    elif not a % 3:
        print("Fizz")
    else:
        print(a)

print()