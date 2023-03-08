import os, json
from time import sleep
from threading import Thread
shutdownsignal = False

if os.path.isfile("data.db"):
    db = json.load(open("data.db"))
    try:
        db = json.load(open("data.db"))
        db["Options"]["BotToken"]
        db["Options"]["AutoDelete"]
        db["Options"]["RethinkURL"]
        db["Users"]
        int(db["Options"]["AutoDelete"])
    except (ValueError, KeyError, json.decoder.JSONDecodeError):
        print("options.json not valid, fix the file or delete this file")
        exit()
else:
    db = {}
    print("File data.db doesn't exist, making new one")
    db["Options"] = {}
    db["Users"] = {}
    print("What is your bot token?")
    db["Options"]["BotToken"] = input(">")
    print("How long in seconds should the bot wait until it deletes command output? Ex:200")
    db["Options"]["AutoDelete"] = int(input(">"))
    print("What is the Rethink URL?")
    db["Options"]["RethinkURL"] = input(">")
    json.dump(db, open("data.db", "w"), indent=4)

def saveState():
    json.dump(db, open("data.db", "w"), indent=4)

def saveLoop():
    global shutdownsignal
    time=0
    while not shutdownsignal:
        if time > 60:
            saveState(db)
            time=0
        else:
            sleep(1)
    asyncio.run(client.close())
        
save_daemon = Thread(target=saveLoop, daemon=True, name='SaveLoop')
save_daemon.start()

def save_and_exit(*args):
    print("Sent shutdown signal")
    shutdownsignal = True
    print("Saving...")
    saveState()
    print("Done")
    exit(1)