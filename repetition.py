#-----------------------------------------------------------------------------
# Name:        Repetition (repetition.py)
# Purpose:     Demonstrating while loops, for loops with range(), loop else,
#              break, continue and pass
#
# Author:      Mr. Kowalczewski
# Created:     28-Sept-2026
# Updated:     28-Sept-2026
#-----------------------------------------------------------------------------

# --- while loops -------------------------------------------------------------
count = 1

# the indented code repeats as long as count is less than 11
# the entire loop runs top to bottom - the condition is only checked at the top
while count < 11:
    print(str(count))
    count = count + 1
    
else:
    print("All Done")

# best use of a while loop: repetition with an unknown number of repeats
# keep repeating while the condition is true
answer = int(input("What is 1 + 1? "))
# condition is: wrong answer
while answer != 2:
    print("Wrong!")
    answer = int(input("What is 1 + 1? "))

    if answer == 100:
        print("Whoa that's way off")
        break
else:
    print("Correct!")


# # --- for loops ---------------------------------------------------------------

# for loops are good when there's a pattern, or a known # of repetitions

# count up
for count in range(2, 32, 2):

    # 10 doesn't get printed, because the loop jumps back to the top
    if count == 10:
        continue

    print(count)

    # if count == 10:
    #     break
    
else:
    print("Loop Completed")

print("next loop")

# count down
for count in range(5, 0, -1):
    print(count)


# --- Special cases -----------------------------------------------------------
# pass is only used temporarily - it should never be in a final product
grade = 80
if grade > 80:
    pass

number = int(input("Guess the number: "))
while number != 2:
    if number == 1:
        print("So Close!")
        # ask again before jumping back, or this repeats forever
        number = int(input("Guess the number: "))
        continue

    print("Wrong, try again!")
    number = int(input("Guess the number: "))
else:
    print("Loop Complete")

# avoid while True loops - we only want to see while loops with proper conditions
count = 0
while True:
    print(count)
    count += 1
    if count == 10:
        break
