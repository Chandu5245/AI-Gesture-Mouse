import mediapipe as mp

class GestureDetector:

    def __init__(self):
        mp_hands = mp.solutions.hands

        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        self.drawer = mp.solutions.drawing_utils

    def detect(self, frame):
        return self.hands.process(frame)