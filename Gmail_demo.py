import pyautogui
import webbrowser
import time

# Safety setup
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.4

# Step 1: Open Gmail
webbrowser.open("https://mail.google.com/")
time.sleep(8)  # wait for Gmail to load (increase if slow internet)

# Step 2: Click "Compose" (⚠️ adjust coordinates for your screen)
pyautogui.click(48,179)  # example position — hover over the "Compose" button and note coords
time.sleep(8)

# Step 3: Type recipient email
pyautogui.typewrite("kishoreicat88@gmail.com")

pyautogui.press('enter')   # confirm recipient
time.sleep(4)

pyautogui.press("tab")  # move to subject field
time.sleep(8)

# Step 4: Type subject
pyautogui.typewrite("Automated Mail from PyAutoGUI")
pyautogui.press("tab")  # move to body
time.sleep(8)

# Step 5: Type the message body
pyautogui.typewrite("Hello,\n\nThis is a test email sent using PyAutoGUI automation.\n\nRegards,\nPython Script")
time.sleep(8)

# Step 6: Send the email (Ctrl + Enter)
pyautogui.hotkey("ctrl", "enter")

print("✅ Email sent successfully!")
