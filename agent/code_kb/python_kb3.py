"""Python snippets for the SADAH v6 tasks (part 2)."""

SNIPPETS = {
    "unit_test": r'''
import unittest

def add(a, b):
    return a + b

class TestAdd(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

if __name__ == "__main__":
    unittest.main()''',
    "enum": r'''
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2

print(Color.RED.name, Color.RED.value)
for c in Color:
    print(c)''',
    "palindrome": r'''
def is_palindrome(text: str) -> bool:
    clean = "".join(ch.lower() for ch in text if ch.isalnum())
    return clean == clean[::-1]

print(is_palindrome("Racecar"))   # True''',
    "fibonacci_code": r'''
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

print(list(fibonacci(10)))   # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]''',
    "prime_check": r'''
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True

print([n for n in range(30) if is_prime(n)])''',
    "matrix": r'''
a = [[1, 2], [3, 4]]
b = [[5, 6], [7, 8]]
result = [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
print(result)     # [[19, 22], [43, 50]]

# with NumPy:  import numpy as np;  print(np.array(a) @ np.array(b))''',
    "user_input": r'''
name = input("What's your name? ")
age = int(input("Your age: "))
print(f"Hello {name}, next year you will be {age + 1}")''',
    "linked_list": r'''
class Node:
    def __init__(self, value, next=None):
        self.value, self.next = value, next

class LinkedList:
    def __init__(self):
        self.head = None

    def push(self, value):
        self.head = Node(value, self.head)

    def __iter__(self):
        node = self.head
        while node:
            yield node.value
            node = node.next

items = LinkedList()
for v in (3, 2, 1):
    items.push(v)
print(list(items))   # [1, 2, 3]''',
    "count_words": r'''
from collections import Counter

text = "the cat and the hat and the bat"
words = text.split()
print(len(words))                       # 8 words
print(Counter(words).most_common(2))    # [('the', 3), ('and', 2)]''',
    "custom_exception": r'''
class InsufficientFunds(Exception):
    pass

def withdraw(balance, amount):
    if amount > balance:
        raise InsufficientFunds(f"need {amount - balance} more")
    return balance - amount

try:
    withdraw(100, 150)
except InsufficientFunds as e:
    print("Error:", e)''',
    "csv_file": r'''
import csv

with open("people.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "age"])
    writer.writerow(["Sara", 30])

with open("people.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        print(row["name"], row["age"])''',
    "database": r'''
import sqlite3

con = sqlite3.connect("app.db")
con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
con.execute("INSERT INTO users (name) VALUES (?)", ("Sara",))   # ? prevents SQL injection
con.commit()
for row in con.execute("SELECT id, name FROM users"):
    print(row)
con.close()''',
}
