import random
systemNumber = random.randint(0,1000)
while True:
    userInput = int(input("Guess the Number between 0-1000: "))
    if userInput == systemNumber:
        print(f"Correct Answer , {userInput} is correct number")
        break
    elif userInput > systemNumber:
        print(f"{userInput} is larger number , try smaller number")
    else:
        print(f"{userInput} is smaller number , try larger number")
    