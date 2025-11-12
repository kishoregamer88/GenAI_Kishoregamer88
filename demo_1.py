import pyautogui
import time
import webbrowser

#Step 1:Open browser
webbrowser.open("https://www.google.com")
time.sleep(5) #wait for browser to open

#Step 2: Click on the search bar (adjust x,y to your screen)
pyautogui.click( 1016, 472) #Adjust as needed
time.sleep(1)

#Step 3: Type the search query
pyautogui.write("New Zealand vs West Indies  ", interval=0.05)
pyautogui.press("enter")
time.sleep(5) #wait for results to load

#Step 4: Click first link (adjust x,y to the first link's location)
pyautogui.click(400, 400) #Adjust as needed