import os
import json
import discord
from RethinkAPI import rethink
from time import sleep
from threading import Thread
import signal
from sstate import *
from datetime import datetime

signal.signal(signal.SIGINT, save_and_exit)
print("Press CTRL+C to stop server")

rethink.url = db["Options"]["RethinkURL"]
msg_autodel_time = db["Options"]["AutoDelete"]
token = db["Options"]["BotToken"]

intents = discord.Intents().default()
intents.messages = True
intents.guild_messages = True
intents.guild_reactions = True
intents.message_content = True
intents.reactions = True
# intents.dm_messages = True

client = discord.Client(intents=intents)

def genmessage(message):
    username = message.author.mention
    message = "From "+username+": "+message.content+"\n"
    return message

@client.event
async def on_ready():
    global db
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    global db
    if message.author == client.user:
        return
    if message.content.startswith('/rt'):
        if message.content.startswith('/rt help'):
            if message.channel.type == discord.ChannelType.private_thread:
                await message.channel.send(open("messages/login.txt", "r").read())
            else:
                await message.channel.send(genmessage(message)+open("messages/help.txt", "r").read(), delete_after=msg_autodel_time)
        elif message.content.startswith('/rt register'):
            thread = await message.channel.create_thread(
                name=str(message.author) + "'s Rethink Login Prompt",
                type=discord.ChannelType.private_thread,
                invitable=False,
                auto_archive_duration=60)
            await thread.send(message.author.mention + "\r" +open("messages/login.txt", "r").read())
            await message.channel.send(genmessage(message)+"A private login thread has been made", delete_after=msg_autodel_time)
        elif message.content.startswith('/rt username'):
            if message.channel.type == discord.ChannelType.private_thread:
                chosen_username = message.content.split("/rt username")[1].strip()
                if bool(chosen_username):
                    try:
                        db["Users"][str(message.author.id)]["RT_USERNAME"] = chosen_username
                    except KeyError:
                        db["Users"][str(message.author.id)] = {
                            "RT_USERNAME": chosen_username
                        }

                    await message.channel.send("Username Set!",delete_after=msg_autodel_time)
                else:
                    await message.channel.send("Could not set the username, did you type it in correctly?",delete_after=msg_autodel_time)
            else:
                await message.channel.send(open("messages/leakcredentials.txt", "r").read(),delete_after=msg_autodel_time)
        elif message.content.startswith('/rt password'):
            if message.channel.type == discord.ChannelType.private_thread:
                chosen_password = message.content.split("/rt password")[1].strip()
                if bool(chosen_password):
                    try:
                        db["Users"][str(message.author.id)]["RT_PASSWORD"] = chosen_password
                    except KeyError:
                        db["Users"][str(message.author.id)] = {
                            "RT_PASSWORD": chosen_password
                        }
                    await message.channel.send("Password Set!",delete_after=msg_autodel_time)
                else:
                    await message.channel.send(
                        "Could not set the username, did you type it in correctly?",
                        delete_after=msg_autodel_time)
            else:
                await message.channel.send(open("messages/leakcredentials.txt", "r").read(),delete_after=msg_autodel_time)
        elif message.content.startswith('/rt week'):
            direction = message.content.split("/rt week")[1].strip()
            if direction == "":
                try:
                    info = rethink.getInfo(db["Users"][str(message.author.id)]["RT_AUTH"])
                except rethink.connectionFailed:
                    await message.channel.send(genmessage(message)+open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
                except rethink.sessionAuthError:
                    await message.channel.send(genmessage(message)+open("messages/tokenexpired.txt", "r").read(),delete_after=msg_autodel_time)
                except KeyError:
                    await message.channel.send(genmessage(message)+open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)
                else:
                    await message.channel.send(genmessage(message)+"Week offset: " +str(info["week"]),delete_after=msg_autodel_time)
            else:
                if direction == "up":
                    try:
                        rethink.shiftWeekUp(db["Users"][str(message.author.id)]["RT_AUTH"])
                    except rethink.connectionFailed:
                        await message.channel.send(genmessage(message)+open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
                    except rethink.sessionAuthError:
                        await message.channel.send(genmessage(message)+open("messages/tokenexpired.txt", "r").read(),delete_after=msg_autodel_time)
                    except KeyError:
                        await message.channel.send(genmessage(message)+open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)
                    else:
                        await message.channel.send(genmessage(message)+"Moved up",delete_after=msg_autodel_time)
                if direction == "down":
                    try:
                        rethink.shiftWeekDown(db["Users"][str(
                            message.author)]["RT_AUTH"])
                    except rethink.connectionFailed:
                        await message.channel.send(genmessage(message)+open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
                    except rethink.sessionAuthError:
                        await message.channel.send(genmessage(message)+open("messages/tokenexpired.txt", "r").read(),delete_after=msg_autodel_time)
                    except KeyError:
                        await message.channel.send(genmessage(message)+open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)
                    else:
                        await message.channel.send(genmessage(message)+"Moved down",delete_after=msg_autodel_time)
        elif message.content.startswith('/rt login'):
            if message.channel.type == discord.ChannelType.private_thread:
                await message.channel.send("Trying to log in...",delete_after=msg_autodel_time)
                try:
                    db["Users"][str(message.author.id)]["RT_USERNAME"]
                except KeyError:
                    await message.channel.send("Username was not set", delete_after=msg_autodel_time)
                try:
                    db["Users"][str(message.author.id)]["RT_PASSWORD"]
                except KeyError:
                    await message.channel.send("Password was not set", delete_after=msg_autodel_time)
                try:
                    auth = rethink.auth(db["Users"][str(message.author.id)]["RT_USERNAME"], db["Users"][str(message.author.id)]["RT_PASSWORD"])
                except rethink.loginIncorrectErr:
                    await message.channel.send("Login incorrect", delete_after=msg_autodel_time)
                except rethink.connectionFailed:
                    await message.channel.send(open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
                except TypeError:
                    await message.channel.send(open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
                else:
                    del db["Users"][str(message.author.id)]["RT_USERNAME"]
                    del db["Users"][str(message.author.id)]["RT_PASSWORD"]
                    db["Users"][str(message.author.id)]["RT_AUTH"] = auth
                    await message.channel.send("Login Successful",delete_after=msg_autodel_time)
                    sleep(1)
                    await message.channel.delete()
                    return
            else:
                await message.channel.send("This command is not avaliable in public chats! Did you mean /rt register?",delete_after=20)
        elif message.content.startswith('/rt add'):
            classid = message.content.split('/rt add')[1].strip()
            try:
                rethink.addClass(db["Users"][str(message.author.id)]["RT_AUTH"], classid)
            except rethink.connectionFailed:
                await message.channel.send(genmessage(message)+open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
            except rethink.sessionAuthError:
                await message.channel.send(genmessage(message)+open("messages/tokenexpired.txt", "r").read(),delete_after=msg_autodel_time)
            except KeyError:
                await message.channel.send(genmessage(message)+open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)     
            else:
                await message.channel.send(genmessage(message)+"Added!",delete_after=msg_autodel_time)
        elif message.content.startswith('/rt remove'):
            classid = message.content.split('/rt remove')[1].strip()
            try:
                rethink.removeClass(db["Users"][str(message.author.id)]["RT_AUTH"], classid)
            except rethink.connectionFailed:
                await message.channel.send(genmessage(message)+open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
            except rethink.sessionAuthError:
                await message.channel.send(genmessage(message)+open("messages/tokenexpired.txt", "r").read(),delete_after=msg_autodel_time)
            except KeyError:
                await message.channel.send(genmessage(message)+open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)     
            else:
                await message.channel.send(genmessage(message)+"Removed!",delete_after=msg_autodel_time)
        elif message.content.startswith('/rt logout'):
            await message.channel.send(genmessage(message)+"Logging out...",delete_after=msg_autodel_time)
            try:
                del db["Users"][str(message.author.id)]
            except KeyError:
                await message.channel.send(open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)
            else:
                await message.channel.send("Logged out",delete_after=msg_autodel_time)
        elif message.content.startswith('/rt list'):
            if message.content.split('/rt list')[1].strip() in ("public", "pub"):
                try:
                    classes = rethink.getAllClasses(db["Users"][str(message.author.id)]["RT_AUTH"])
                except rethink.connectionFailed:
                    await message.channel.send(genmessage(message)+open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
                except rethink.sessionAuthError:
                    await message.channel.send(genmessage(message)+open("messages/tokenexpired.txt", "r").read(),delete_after=msg_autodel_time)
                except KeyError:
                    await message.channel.send(genmessage(message)+open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)     
                else:
                    if len(classes) == 0:
                        await message.channel.send(genmessage(message)+"No classes this week",delete_after=msg_autodel_time)
                    else:
                        await message.channel.send(genmessage(message),delete_after=msg_autodel_time)
                        finout = ""
                        selday = ""
                        for c in classes:
                            if selday != c["date"]:
                                finout = finout + "**```"+datetime.strptime(c["date"], '%Y-%m-%d').strftime("%A")+" "+c["date"]+"```**\n"
                                selday = c["date"]
                            finout = finout + "`"
                            if c["type"].lower() != "open":
                                finout = finout+"["+c["type"]+"]"
                            finout = finout+"("+c["classid"]+")"
                            finout = finout+"["+c["firstname"]+" "+c["lastname"]+"] "
                            finout = finout+c["classname"]
                            finout = finout+" in "+c["room"]
                            finout = finout + "`"
                            finout = finout + "\n"
                        temp = ""
                        for peice in finout.split("\n"):
                            if len(temp)+len(peice) > 1500:
                                await message.channel.send(temp,delete_after=msg_autodel_time)
                                temp=""
                            temp = temp + peice + "\n"
                        if temp != "":
                            await message.channel.send(temp,delete_after=msg_autodel_time)
            elif message.content.split('/rt list')[1].strip() == "" or message.content.split('/rt list')[1].strip() in "enrolled":
                try:
                    classes = rethink.getEnrolledClasses(db["Users"][str(message.author.id)]["RT_AUTH"])
                except rethink.connectionFailed:
                    await message.channel.send(genmessage(message)+open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
                except rethink.sessionAuthError:
                    await message.channel.send(genmessage(message)+open("messages/tokenexpired.txt", "r").read(),delete_after=msg_autodel_time)
                except KeyError:
                    await message.channel.send(genmessage(message)+open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)     
                else:
                    if len(classes) == 0:
                        await message.channel.send(genmessage(message)+"No classes this week",delete_after=msg_autodel_time)
                    else:
                        await message.channel.send(genmessage(message),delete_after=msg_autodel_time)
                        finout = ""
                        selday = ""
                        for c in classes:
                            if selday != c["date"]:
                                finout = finout + "**```"+datetime.strptime(c["date"], '%Y-%m-%d').strftime("%A")+" "+c["date"]+"```**\n"
                                selday = c["date"]
                            finout = finout + "`"
                            if c["type"].lower() != "open":
                                finout = finout+"["+c["type"]+"]"
                            finout = finout+"("+c["classid"]+")"
                            finout = finout+"["+c["firstname"]+" "+c["lastname"]+"] "
                            finout = finout+c["classname"]
                            finout = finout+" in "+c["room"]
                            finout = finout + "`"
                            finout = finout + "\n"
                        temp = ""
                        for peice in finout.split("\n"):
                            if len(temp)+len(peice) > 1500:
                                await message.channel.send(temp,delete_after=msg_autodel_time)
                                temp=""
                            temp = temp + peice + "\n"
                        if temp != "":
                            await message.channel.send(temp,delete_after=msg_autodel_time)
            else:
                await message.channel.send(genmessage(message)+"Invalid arguments",delete_after=msg_autodel_time)
        elif message.content.startswith('/rt remind'):
            await message.channel.send(genmessage(message)+"Command not implimented yet.",delete_after=msg_autodel_time)
        elif message.content.startswith('/rt users'):
            final = ""
            for user in db["Users"].keys():
                final = final + str(await client.fetch_user(user)) 
                try:
                    test = rethink.authCheck(db["Users"][str(user)]["RT_AUTH"])
                except rethink.connectionFailed:
                    final = final + " (err)"
                except rethink.sessionAuthError:
                    final = final + " (auth expired)"
                final = final + "\n"
            await message.channel.send(genmessage(message)+"Users:\n" + final,delete_after=msg_autodel_time)
        elif message.content.startswith('/rt status'):
            await message.channel.send(genmessage(message),delete_after=msg_autodel_time)
            try:
                test = rethink.authCheck(db["Users"][str(message.author.id)]["RT_AUTH"])
            except rethink.connectionFailed:
                await message.channel.send(open("messages/servererror.txt", "r").read(),delete_after=msg_autodel_time)
            except rethink.sessionAuthError:
                await message.channel.send(open("messages/tokenexpired.txt", "r").read(),delete_after=msg_autodel_time)
            except KeyError:
                await message.channel.send(open("messages/notloggedin.txt", "r").read(),delete_after=msg_autodel_time)
            else:
                await message.channel.send("Rethink is linked to your account.",delete_after=msg_autodel_time)
                if test == True:
                    await message.channel.send("Rethink token is still valid",delete_after=msg_autodel_time)
                else:
                    await message.channel.send("Rethink token expired, you might need to re-register to fix this",delete_after=msg_autodel_time)
        else:
            await message.channel.send(genmessage(message)+"Commad not found, try /rt help",delete_after=msg_autodel_time)
        await message.delete()

client.run(token)
