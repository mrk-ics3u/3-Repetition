# Lesson 3 - Repetition (while and for)

The example code for this lesson is in `repetition.py`. Open it alongside these
notes and run it as we go.

A loop completes the same (or a similar) task over and over until a particular
condition is reached. In this course we focus on two looping structures:
`while` and `for`.

## while loops

A while loop keeps going while a condition is `True`. Think of it as an if
statement that repeats until the condition is no longer true.

```python
count = 1

# the indented code repeats as long as count is less than 11
while count < 11:
    print(str(count))
    count = count + 1
else:
    print("All Done")

# best use of a while loop: repetition with an unknown number of repeats
answer = int(input("What is 1 + 1? "))
while answer != 2:
    print("Wrong!")
    answer = int(input("What is 1 + 1? "))
else:
    print("Correct!")
```

The structure is very similar to an if statement. Anything you can check in an
if, you can check in a while.

Use a while loop when you do not know how many times the loop needs to run. Use
a for loop when you do.

## for loops

A for loop counts from one value to another by a set increment:

```python
for iterator in range(start, stop, step):
    pass
```

- `iterator` is an integer variable created on the spot. It changes every time
  the loop starts over. Its main job is to control the number of repetitions,
  but you can use it like any other variable (in if statements and so on).
- `range()` creates the values the iterator takes on inside the loop.
- `start` is the first value.
- `stop` is where the range ends. Python does **not** include this value.
- `step` is how much the iterator changes each time.

```python
# count up
for count in range(2, 30, 2):
    print(count)
    if count == 22:
        print("Yay!")
        break
else:
    print("Loop Completed")

print("next loop")

# count down
for count in range(5, 0, -1):
    print(count)
```

There are more advanced uses of for loops. We will point them out when we get
to those concepts.

## else

Both kinds of loop can have an `else`, just like an if statement. The else runs
when the loop finishes normally:

- for a while loop, when the condition becomes false
- for a for loop, when every value has been used

So when would `else` NOT run?

## Special cases

- `break` leaves a loop early.  Use it rarely (such as your program may crash).
- `continue` jumps back to the start of the loop early. Use it rarely.
- `pass` does nothing. Use it only temporarily, as a placeholder.
- `while True` loops run forever unless something breaks out. Avoid relying on
  them; we want while loops with proper conditions.

```python
# pass is only used temporarily - it should never be in a final product
grade = 80
if grade > 80:
    pass

number = int(input("Guess the number: "))
while number != 2:
    if number == 1:
        print("So Close!")
        number = int(input("Guess the number: "))
        continue

    print("Wrong, try again!")
    number = int(input("Guess the number: "))
else:
    print("Loop Complete")

# avoid while True loops like this one
count = 0
while True:
    print(count)
    count += 1
    if count == 10:
        break
```

Note that the `continue` example asks for a new guess before it jumps back.
Without that line, a guess of 1 would repeat "So Close!" forever.

## Lab

That is it for the lesson. Move on to Lab 3, in `README.md`.
