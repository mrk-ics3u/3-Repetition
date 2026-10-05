# Lab 3 - Sums and Factors

This lab has two tasks. Both must work for the tests to pass. The `input()`
lines are already in `main.py`; leave them as they are.

Open `main.py` and complete the following:

1. Update the header with your information (Name, Purpose, Author, Created, Updated).

**Task 1** (below `# TASK 1`)

2. Using a `for` loop, add up every whole number from `first_number` to `second_number`, including both. For example, 5 and 8 give 5 + 6 + 7 + 8 = 26.
3. Print `Sum: ____` with the total in the blank.
4. If `first_number` is larger than `second_number`, print `Invalid` instead.

**Task 2** (below `# TASK 2`)

5. Using a `while` loop, find the largest factor of `factor_number`, other than the number itself. For example, the largest factor of 24 is 12.
6. Print `Largest Factor: ____` with the factor in the blank.
7. If the only factor is 1, print `Prime` instead.
8. Do not use `break` in Task 2.

The prompts are already written for you:

- `Input the first number of your series: `
- `Input the second number of your series: `
- `Input a number to find the largest factor: `

Assume every value entered is a whole number, and that `factor_number` is 2 or more.

## Running your program

Open `main.py` and press the Run button in the top right corner of VS Code. Your output appears in the terminal at the bottom.

## Checking your work

Press **Ctrl+Shift+B** to run the tests. You will see one line per test:

```
[PASS] 1. Header is filled in
[FAIL] 2. Sum of 3 to 7, factor of 24
```

When a test fails it shows what was expected and what your program printed. Fix your code and press Ctrl+Shift+B again. Keep going until all tests pass.

## Reminders

- Fill in every field of the header before you write any code.
- Write comments as you go. The `# TASK` lines are already there; add your own that explain your loops.
- Tests check your output exactly. `sum: 25` is not the same as `Sum: 25`.
- A loop that never ends will be stopped after 5 seconds. Make sure your `while` condition eventually becomes false.

## Optional challenges

Finished early? Try the optional challenges in the `challenges` folder. Open `challenges/CHALLENGES.md` for instructions. They are not assessed and do not affect your lab result.
