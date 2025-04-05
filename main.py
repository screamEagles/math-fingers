import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import random
import time
import os

# Configurable min and max result range
max_number = 5
min_number = 1

# Game settings
game_duration = 10  # seconds

# High score file path
high_score_file = "highscore.txt"

# Function to read high score
def read_high_score():
    if not os.path.exists(high_score_file):
        return 0, game_duration
    with open(high_score_file, 'r') as file:
        data = file.read().strip()
        if data:
            score_str, time_str = data.split(',')
            return int(score_str), int(time_str)
        return 0, game_duration

# Function to update high score if needed
def update_high_score(new_score, game_time):
    old_score, _ = read_high_score()
    if new_score > old_score:
        with open(high_score_file, 'w') as file:
            file.write(f"{new_score},{game_time}")

# Equation generator
def generate_equation(min_number=1, max_number=5):
    operations = ['+', '-', '*', '/']
    while True:
        op = random.choice(operations)
        result = None
        a, b = 0, 0

        if op == '+':
            a = random.randint(min_number, max_number)
            b_max = max_number - a
            if b_max < min_number:
                continue
            b = random.randint(min_number, b_max)
            result = a + b

        elif op == '-':
            a = random.randint(min_number, max_number)
            b_min = a - max_number
            b_max = a - min_number
            if b_max < min_number:
                continue
            b = random.randint(max(b_min, min_number), min(b_max, max_number))
            result = a - b

        elif op == '*':
            a = random.randint(min_number, max_number)
            possible_b = [b for b in range(min_number, max_number + 1) if min_number <= a * b <= max_number]
            if not possible_b:
                continue
            b = random.choice(possible_b)
            result = a * b

        elif op == '/':
            b = random.randint(min_number, max_number)
            possible_results = [r for r in range(min_number, max_number + 1) if r * b <= max_number * max_number]
            if not possible_results:
                continue
            result = random.choice(possible_results)
            a = result * b

        if min_number <= result <= max_number:
            return f"{a} {op} {b} = ?", result

# Game states
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
game_state = STATE_MENU

# Load high score
high_score, high_score_time = read_high_score()

# Initialize camera
cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1)

# Game variables
score = 0
question, answer = generate_equation(min_number, max_number)
correct_display_timer = 0
start_time = 0

while True:
    success, image = cap.read()
    image = cv2.flip(image, 1)
    hands, image = detector.findHands(image, draw=False, flipType=True)
    key = cv2.waitKey(1) & 0xFF

    if game_state == STATE_MENU:
        cvzone.putTextRect(image, f"Maths - With Fingers", (120, 100), scale=2, colorR=(140, 196, 20))
        cvzone.putTextRect(image, "Start (S)", (100, 200), scale=1.5, colorR=(125, 116, 40))
        cvzone.putTextRect(image, "Quit (Q)", (400, 200), scale=1.5, colorR=(86, 86, 168))
        cvzone.putTextRect(image, f"High Score: {high_score}", (200, 300), scale=1.5, colorR=(140, 196, 20))

        if key == ord('s'):
            start_time = time.time()
            score = 0
            question, answer = generate_equation(min_number, max_number)
            correct_display_timer = 0
            game_state = STATE_PLAYING
        elif key == ord('q'):
            break

    elif game_state == STATE_PLAYING:
        elapsed_time = int(time.time() - start_time)
        time_left = game_duration - elapsed_time

        if time_left > 0:
            if hands:
                hand1 = hands[0]
                fingers1 = detector.fingersUp(hand1)
                finger_count = fingers1.count(1)

                cvzone.putTextRect(image, f"{finger_count}", (400, 50), colorR=(250, 196, 2))

                if finger_count == answer:
                    correct_display_timer = 30
                    score += 1
                    question, answer = generate_equation(min_number, max_number)

            cvzone.putTextRect(image, f"{question}", (50, 50), colorR=(0, 255, 0))

            if correct_display_timer > 0:
                cvzone.putTextRect(image, "Correct!", (200, 200), scale=2.2, colorR=(0, 200, 255), offset=15)
                correct_display_timer -= 1

            cvzone.putTextRect(image, f"{score}pts", (50, 105), scale=2, colorR=(0, 200, 150))
            cvzone.putTextRect(image, f"{time_left}s", (500, 105), scale=2, colorR=(255, 0, 0))

            # Mid-game menu & restart options
            cvzone.putTextRect(image, "Restart (R)", (50, 450), scale=2, colorR=(180, 255, 100), offset=8)
            cvzone.putTextRect(image, "Main Menu (M)", (300, 450), scale=2, colorR=(255, 150, 150), offset=8)

            # Handle mid-game key presses
            if key == ord('r'):
                start_time = time.time()
                score = 0
                question, answer = generate_equation(min_number, max_number)
                correct_display_timer = 0

            elif key == ord('m'):
                high_score, _ = read_high_score()
                game_state = STATE_MENU

        else:
            is_new_high = score > high_score
            if is_new_high:
                update_high_score(score, game_duration)
                high_score = score  # update locally too
            game_state = STATE_GAME_OVER

    elif game_state == STATE_GAME_OVER:
        if score >= high_score:
            cvzone.putTextRect(image, "New High Score!!!", (50, 240), scale=3.6, colorR=(0, 255, 0))
            cvzone.putTextRect(image, f"{high_score}pts!!", (250, 300), scale=3, colorR=(0, 255, 0))
        else:
            cvzone.putTextRect(image, "Great Game!", (220, 100), scale=2, colorR=(0, 200, 255), offset=20)
            cvzone.putTextRect(image, f"You Scored {score}pts!", (200, 200), scale=1.8, colorR=(0, 200, 255))
            cvzone.putTextRect(image, f"Wanna score {high_score}pts in {game_duration}s?", (100, 400), scale=1.5, colorR=(255, 215, 0))

        cvzone.putTextRect(image, "Restart (R)", (50, 450), scale=2, colorR=(100, 255, 100))
        cvzone.putTextRect(image, "Main Menu (M)", (300, 450), scale=2, colorR=(255, 100, 100))

        if key == ord('r'):
            start_time = time.time()
            score = 0
            question, answer = generate_equation(min_number, max_number)
            correct_display_timer = 0
            game_state = STATE_PLAYING
        elif key == ord('m'):
            high_score, _ = read_high_score()
            game_state = STATE_MENU

    cv2.imshow("Math Game", image)

cap.release()
cv2.destroyAllWindows()
