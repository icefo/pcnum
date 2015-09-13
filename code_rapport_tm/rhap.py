__author__ = 'adrien'
from random import randint
from time import sleep


def slow_function(number_of_numbers=10):
    for __ in range(number_of_numbers):
        unpredictable = randint(-5, 10)
        sleep(2)
        yield unpredictable

# un nombre sortira chaque 2 secondes
for number in slow_function():
    print(number)


def slow_blocking_function(number_of_numbers=10):
    storage = list()
    for __ in range(number_of_numbers):
        unpredictable = randint(-5, 10)
        sleep(2)
        storage.append(unpredictable)
    return storage

# tous les nombres sortiront presque instanement au bout de 20 secondes
for number in slow_blocking_function():
    print(number)