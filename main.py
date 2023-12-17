#first terminal pip3 install discord.py
import discord 
from discord.ext import commands

#initialize our bot 
client = commands.Bot(command_prefix = '!', intents = discord.Intents.all()) 
#give prefix bot listens in for, using ! as prefix, after ! is command

#event 

@client.event
async def on_ready(): #when bot is ready to recieve commands
    print("Bot is ready") #user wont see this we will in terminal 
    print("------------------") #seperate for clarity 

@client.command()
async def duel(ctx): # command after ! 
    await ctx.send("1v1 me bro") #bot will send message to channel

client.run('MTE4NTc0MDYzODY1MDYzNDM0MA.GYvgGU.c2kPcWp8C7ZTE6mNuS8Kz0ysSLOQaxftNJOXzE') #run bot, update each time you change sthm in discord dev portal 
#link up this code with discord token 

#run python3 main.py in terminal to run bot



