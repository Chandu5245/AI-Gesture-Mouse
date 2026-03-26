import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np

pyautogui.FAILSAFE = False

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

mp_draw = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()

smoothening = 8
MOVE_DEADZONE = 0.005

prev_x, prev_y = 0, 0
prev_index_x, prev_index_y = None, None

dragging = False
gesture = "MOVE"

# 👉 NEW: system toggle
system_active = True

prev_time = 0

DOUBLE_CLICK_THRESHOLD = 0.03

# cooldowns
last_double_click_time = 0
DOUBLE_CLICK_COOLDOWN = 1

last_right_click_time = 0
RIGHT_CLICK_COOLDOWN = 0.6

last_play_pause_time = 0
PLAY_PAUSE_COOLDOWN = 1

# gesture confirmation
gesture_start_time = 0
GESTURE_DELAY = 0.3
current_gesture = None

# play pause lock
play_pause_active = False


def confirm_gesture(name):
    global gesture_start_time, current_gesture

    now = time.time()

    if current_gesture != name:
        current_gesture = name
        gesture_start_time = now
        return False

    if now - gesture_start_time > GESTURE_DELAY:
        return True

    return False


while True:

    gesture = "MOVE"

    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    frame_h, frame_w, _ = frame.shape

    # ===== ONLY CHANGE: wrap everything inside this =====
    if system_active and results.multi_hand_landmarks:

        # TWO HAND ZOOM
        if len(results.multi_hand_landmarks) == 2:

            gesture = "TWO HAND ZOOM"

            pyautogui.keyDown("ctrl")
            pyautogui.scroll(40)
            pyautogui.keyUp("ctrl")

        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(frame,
                                   hand_landmarks,
                                   mp_hands.HAND_CONNECTIONS)

            index = hand_landmarks.landmark[8]
            middle = hand_landmarks.landmark[12]
            thumb = hand_landmarks.landmark[4]
            ring = hand_landmarks.landmark[16]
            pinky = hand_landmarks.landmark[20]

            index_x,index_y = index.x,index.y
            middle_x,middle_y = middle.x,middle.y
            thumb_x,thumb_y = thumb.x,thumb.y
            ring_x,ring_y = ring.x,ring.y
            pinky_x,pinky_y = pinky.x,pinky.y

            x = int(index_x * frame_w)
            y = int(index_y * frame_h)

            # CURSOR MOVEMENT
            if prev_index_x is not None:

                dx = abs(index_x-prev_index_x)
                dy = abs(index_y-prev_index_y)

                if dx > MOVE_DEADZONE or dy > MOVE_DEADZONE:

                    screen_x = int((x/frame_w) * screen_w)
                    screen_y = int((y/frame_h) * screen_h)

                    curr_x = prev_x + (screen_x-prev_x)/smoothening
                    curr_y = prev_y + (screen_y-prev_y)/smoothening

                    pyautogui.moveTo(int(curr_x), int(curr_y))

                    prev_x, prev_y = curr_x, curr_y

            else:

                prev_x = int(index_x*screen_w)
                prev_y = int(index_y*screen_h)

            prev_index_x, prev_index_y = index_x, index_y

            # DISTANCES
            left_click_dist  = ((index_x - thumb_x)**2  + (index_y - thumb_y)**2)**0.5
            right_click_dist = ((ring_x   - thumb_x)**2 + (ring_y   - thumb_y)**2)**0.5
            double_click_dist = ((index_x - middle_x)**2 + (index_y - middle_y)**2)**0.5
            volume_dist = ((thumb_x - pinky_x)**2 + (thumb_y - pinky_y)**2)**0.5

            now = time.time()

            # LEFT CLICK
            if left_click_dist < 0.04:

                if confirm_gesture("LEFT CLICK"):

                    gesture = "LEFT CLICK"

                    if not dragging:
                        pyautogui.mouseDown()
                        dragging = True
            else:

                if dragging:
                    pyautogui.mouseUp()
                    dragging = False

            # RIGHT CLICK
            if right_click_dist < 0.04:

                if confirm_gesture("RIGHT CLICK"):

                    if now - last_right_click_time > RIGHT_CLICK_COOLDOWN:

                        gesture = "RIGHT CLICK"
                        pyautogui.click(button="right")

                        last_right_click_time = now

            # DOUBLE CLICK
            if double_click_dist < DOUBLE_CLICK_THRESHOLD:

                if confirm_gesture("DOUBLE CLICK"):

                    if now - last_double_click_time > DOUBLE_CLICK_COOLDOWN:

                        gesture = "DOUBLE CLICK"
                        pyautogui.doubleClick()

                        last_double_click_time = now

            # PLAY / PAUSE WITH LOCK
            three_fingers_up = (
                index_y < hand_landmarks.landmark[6].y and
                middle_y < hand_landmarks.landmark[10].y and
                ring_y < hand_landmarks.landmark[14].y
            )

            if three_fingers_up:

                if not play_pause_active:

                    if confirm_gesture("PLAY PAUSE"):

                        if now - last_play_pause_time > PLAY_PAUSE_COOLDOWN:

                            gesture = "PLAY/PAUSE"
                            pyautogui.press("space")

                            last_play_pause_time = now
                            play_pause_active = True

            else:
                play_pause_active = False

            # VOLUME DISPLAY
            volume_level = np.interp(volume_dist,[0.02,0.2],[0,100])

            cv2.putText(frame,
                        f"Volume:{int(volume_level)}%",
                        (10,170),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255,255,255),
                        2)

    # ===== STATUS TEXT =====
    status = "ACTIVE" if system_active else "PAUSED"

    cv2.putText(frame,
                f"System: {status}",
                (10,200),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,255,0) if system_active else (0,0,255),
                2)

    # GESTURE LABEL
    cv2.putText(frame,
                f"Gesture:{gesture}",
                (10,110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,255,0),
                2)

    # FPS
    curr_time = time.time()
    fps = 1/(curr_time-prev_time) if curr_time-prev_time != 0 else 0
    prev_time = curr_time

    cv2.putText(frame,
                f"FPS:{int(fps)}",
                (10,140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,255,255),
                2)

    cv2.imshow("Hand Mouse Control", frame)

    # ===== KEY CONTROL =====
    key = cv2.waitKey(1)

    if key == 27:
        break
    elif key == ord('p'):
        system_active = not system_active

cap.release()
cv2.destroyAllWindows()