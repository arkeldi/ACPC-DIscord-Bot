#first terminal pip3 install discord.py, if needed
import discord 
from discord.ext import commands
from dotenv import load_dotenv 
import os

load_dotenv() #load key from .env file


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

#run python3 main.py in terminal to run bot
#/Applications/Python\ 3.9/Install\ Certificates.command



#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#


#Register discord handle to codeforces handle:

#Register user command here:, going the temp memory route, just python dict 
#key,value dictionary for discord -> codeforces handle

userDict = {}

@client.command() # register command: !register codeforcesUsername
async def register(ctx, codeforcesHandle: str):
    #check if user is registered ?
    discordHandle = str(ctx.author.id)
    discordServer = str(ctx.guild.id) #make str here is using json later

    #check if codeforces handle is valid
    if not verifyCodeforcesHandle(codeforcesHandle):
        await ctx.send("Incorrect Codeforces Username, check again silly goose")
        return

    discordHandle = f"{ctx.author.name}#{ctx.author.discriminator}"

    if discordServer not in userDict: #check is server is in dict
        userDict[discordServer] = {} 
    
    #update map for user
    userDict[discordServer][discordHandle] = codeforcesHandle
    
    await ctx.send("You have registered " + codeforcesHandle + " with " + discordHandle)

@client.command() # generate a problem of difficulty command: !problem difficulty
async def problem(ctx, difficulty: str):
    #check if string is valid problem difficulty 800-3500
    if not difficulty.isnumeric() or int(difficulty) < 800 or int(difficulty) > 3500 or int(difficulty) % 100 != 0:
        await ctx.send("Invalid problem difficulty >.<")
        return
    
    problemlink = generateProblem(int(difficulty))

    await ctx.send("Here's a problem of difficulty " +  difficulty + " " + problemlink)


# making api call to codeforces to verify handle
# pip3 install requests 
import requests

def verifyCodeforcesHandle(codeforcesHandle):
    response = requests.get("https://codeforces.com/api/user.info?handles=" + codeforcesHandle)
    if response.status_code == 200:
        return True 
    else:
        return False 


def generateProblem(difficulty: int):
    #grab list of problems of difficulty (10,000 problems)
    response = requests.get("https://codeforces.com/api/problemset.problems")
    data = response.json()
    problems = data['result']['problems']

    for problem in problems:
        if "rating" in problem and problem["rating"] == difficulty:
            return "https://codeforces.com/problemset/problem/" + str(problem["contestId"]) + "/" + problem['index']
    
    return "no problem of that difficulty for you, goon."


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#

client.run(os.getenv('DISCORD_KEY'))
#run bot, update each time you change sthm in discord dev portal, stored key 
#client.run must be bottom of all code...