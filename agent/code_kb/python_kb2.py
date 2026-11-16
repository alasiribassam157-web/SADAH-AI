"""Python snippets for the SADAH v6 tasks (part 1)."""

SNIPPETS = {
    "inheritance": r'''
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

class Dog(Animal):          # Dog inherits from Animal
    def speak(self):        # override the parent method
        return f"{self.name}: Woof!"

print(Dog("Rex").speak())''',
    "interface": r'''
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Circle(Shape):
    def __init__(self, r):
        self.r = r

    def area(self):
        return 3.14159 * self.r ** 2

print(Circle(2).area())''',
    "lambda": r'''
square = lambda x: x * x
print(square(5))                      # 25

people = [("Sara", 30), ("Ali", 25)]
people.sort(key=lambda p: p[1])       # sort by age
print(people)''',
    "map_filter": r'''
nums = [1, 2, 3, 4, 5, 6]
evens = [n for n in nums if n % 2 == 0]       # filter
squares = [n * n for n in nums]               # map
print(evens, squares)
print(list(map(str, filter(lambda n: n > 3, nums))))''',
    "set_ops": r'''
a = {1, 2, 3, 4}
b = {3, 4, 5}
print(a | b)   # union        {1, 2, 3, 4, 5}
print(a & b)   # intersection {3, 4}
print(a - b)   # difference   {1, 2}
print(list(set([1, 1, 2, 2, 3])))   # remove duplicates''',
    "recursion": r'''
def factorial(n: int) -> int:
    if n <= 1:                 # base case
        return 1
    return n * factorial(n - 1)

print(factorial(5))   # 120''',
    "binary_search": r'''
def binary_search(items, target):
    lo, hi = 0, len(items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

print(binary_search([1, 3, 5, 7, 9, 11], 7))   # 3''',
    "quicksort": r'''
def quicksort(items):
    if len(items) <= 1:
        return items
    pivot, *rest = items
    left = [x for x in rest if x < pivot]
    right = [x for x in rest if x >= pivot]
    return quicksort(left) + [pivot] + quicksort(right)

print(quicksort([5, 2, 9, 1, 7, 3]))''',
    "stack_queue": r'''
from collections import deque

stack = []
stack.append(1); stack.append(2)
print(stack.pop())        # 2  (last in, first out)

queue = deque()
queue.append("a"); queue.append("b")
print(queue.popleft())    # a  (first in, first out)''',
    "string_format": r'''
name, score = "Sara", 93.456
print(f"{name} scored {score:.1f}%")          # f-string
print("{} scored {:.2f}".format(name, score))  # str.format
print(f"{'left':<10}|{'right':>10}|")         # alignment''',
    "regex": r'''
import re

email = "user@example.com"
if re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.]+", email):
    print("valid email")

text = "Call 0551234567 or 0569876543"
print(re.findall(r"05\d{8}", text))''',
    "threads": r'''
import threading
import time

def work(n):
    time.sleep(1)
    print(f"task {n} done")

threads = [threading.Thread(target=work, args=(i,)) for i in range(3)]
for t in threads:
    t.start()
for t in threads:
    t.join()          # all three finish in ~1 second''',
    "async_code": r'''
import asyncio

async def fetch(n):
    await asyncio.sleep(1)       # e.g. a network call
    return n * 10

async def main():
    results = await asyncio.gather(fetch(1), fetch(2), fetch(3))
    print(results)               # [10, 20, 30] in ~1 second

asyncio.run(main())''',
}
