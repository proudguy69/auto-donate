import time
import threading
from selenium import webdriver
import pytchat
import pyautogui as pag
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# List to store users
users = []

# Test chats for development mode
testChats = ["/join CosmicNisho 4607034531", "/join ImagineRoIeplaying 10850886131"]

# Development mode flag
dev = True

# Path to Chrome executable
chrome_path = 'c:\Program Files\Google\Chrome\Application\chrome.exe'

# Create a new instance of Chrome WebDriver
driver = webdriver.Chrome()

# The ammount of robux an item has to be
robux = 10

# Function to check if the asset is valid
def checkAsset(user, asset_id):
    r = requests.get(f"https://economy.roblox.com/v2/assets/{asset_id}/details")
    data = r.json()
    creator = data['Creator']['Name']
    for_sale = data['IsForSale']
    price = data['PriceInRobux']
    if not user.lower() == creator.lower():
        print("Wrong user")
        return False
    if not for_sale:
        print("Not for sale")
        return False
    if price > robux:
        print(f"Price over {robux} robux")
        return False
    return {'Creator': creator, 'link': f"https://www.roblox.com/catalog/{asset_id}/"}

# Function to read chat messages
def read_chat(chat:pytchat.LiveChat):
    if not dev:
        while chat.is_alive():
            for c in chat.get().sync_items():
                if not c.message.startswith('/join'):
                    continue
                args = c.message.split(' ')
                if not len(args) == 3:
                    continue
                asset = checkAsset(args[1], args[2])
                if not asset:
                    continue
                if checkUser(asset['Creator']):
                    continue
                name = {'name': asset['Creator'], 'selected': False, 'asset': asset['link']}
                users.append(name) 
    else:
        for c in testChats:
            args = c.split(' ')
            asset = checkAsset(args[1], args[2])
            if not asset:
                continue
            if checkUser(asset['Creator']):
                continue
            name = {'name': asset['Creator'], 'selected': False, 'asset': asset['link']}
            users.append(name)

# Function to check if a user is already in the list
def checkUser(user):
    for person in users:
        if person['name'] == user:
            return True
    return False

# Function to close the browser window
def close():
    time.sleep(9)
    driver.execute_script(f'window.close('');')

# Function to locate and click on an image
def locateAndClick(dir):
    location = pag.locateOnScreen(dir, confidence=0.9)
    pag.moveTo(location[0], location[1], 1)
    pag.click()   

# Function to open a new browser window with a given link
def open(link):
    driver.switch_to.window(driver.window_handles[0]) 
    driver.execute_script(f'window.open('');')
    driver.switch_to.window(driver.window_handles[1]) 
    driver.get(link)

# Function to purchase the winner's asset
def purchaseWinner(link):
    time.sleep(2)
    open(link)
    t = threading.Thread(target=close)
    t.start()
    time.sleep(1)
    locateAndClick('images/buy_green.png')
    time.sleep(1)
    locateAndClick('images/buy_white.png')
    time.sleep(1)
    locateAndClick('images/dots.png')
    time.sleep(1)
    locateAndClick('images/image.png')

# Route to start the chat stream
@app.route('/api/stream', methods=['POST'])
def stream():
    data = request.get_json(force=True)
    if not dev:
        stream_id = data['stream_id']
        try:
            chat = pytchat.create(video_id=stream_id, interruptable=False)
        except pytchat.exceptions.InvalidVideoIdException:
            return jsonify({"status": "failed", 'message':'Error: Invalid Stream Id'})
        except:
            return jsonify({"status": "failed", 'message':'Error: Unknown Error'})
    else:
        chat = "test"
    
    t = threading.Thread(target=read_chat, args=[chat])
    t.start()

    return jsonify({"status": "success"})

# Route to handle the winner request
@app.route('/api/winner', methods=['POST'])
def winner():
    global users
    data = request.get_json(force=True)
    name = data['name']
    for person in users:
        if person['name'] == name:
            link = person['asset']
            t = threading.Thread(target=purchaseWinner, args=[link])
            t.start()
            users = []
    for person in users:
        print(person)
        users.remove(person)
    return jsonify({"status": "success"})

# Route to get the list of names
@app.route('/api/names')
def names():
    return jsonify({'names': users})

@app.route('/api/robux', methods=['POST'])
def changeRobux():
    global robux
    data = request.get_json(force=True)
    robux = data['robux']
    return jsonify({"status": "success"})
    

# Open the login page and make the user log in
driver.get('http://localhost:5173/')
open('https://www.roblox.com/login')

# Run the Flask app
app.run(debug=False)



