from django.test import TestCase
from collections import Counter
import copy

# Create your tests here.


class Main():
    def __init__(self, x):
        self.x = x


a = Main(10)
b = copy.deepcopy(a)
b.x = 5
print(a.x)
print(b.x)
