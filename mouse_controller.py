import pyautogui


pyautogui.FAILSAFE = False

class MouseController:

    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()
        self.prev_x = 0
        self.prev_y = 0

    def move(self, x, y):
        pyautogui.moveTo(x, y)

    def left_down(self):
        pyautogui.mouseDown()

    def left_up(self):
        pyautogui.mouseUp()

    def right_click(self):
        pyautogui.click(button='right')

    def scroll(self, amount):
        pyautogui.scroll(amount)