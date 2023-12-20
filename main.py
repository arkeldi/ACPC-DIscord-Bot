import discord 
from discord.ext import commands
from dotenv import load_dotenv 
import os
import requests
import random 

load_dotenv() #load discord bot key from .env file

#initialize our bot 
client = commands.Bot(command_prefix = '!', intents = discord.Intents.all()) 
#give prefix bot listens in for, using ! as prefix, after ! is command

@client.event
async def on_ready(): #when bot is ready to recieve commands
    print("Bot is ready") #user wont see this we will in terminal 
    print("------------------") #seperate for clarity 


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#

userDict = {}
#register discord handle to codeforces handle:

#register user command here:, going the temp memory route, just python dict 
#key,value dictionary for discord -> codeforces handle


@client.command() # register command: !register codeforcesUsername
async def register(ctx, codeforcesHandle: str):
    #check if user is registered ?
    discordHandle = str(ctx.author.id)
    discordServer = str(ctx.guild.id) #make str here is using json later
    discordUserId = str(ctx.author.id)  # use user id as key

    #check if codeforces handle is valid
    if not verifyCodeforcesHandle(codeforcesHandle):
        await ctx.send("Incorrect Codeforces Username, check again silly goose")
        return

    if discordServer not in userDict:
        userDict[discordServer] = {}

    userDict[discordServer][discordUserId] = codeforcesHandle  # Store with user id as key
    await ctx.send(f"You have registered {codeforcesHandle} with {ctx.author.mention}")


# making api call to codeforces to verify handle
def verifyCodeforcesHandle(codeforcesHandle):
    response = requests.get("https://codeforces.com/api/user.info?handles=" + codeforcesHandle)
    if response.status_code == 200:
        return True 
    else:
        return False 


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#duel command goes like this: 
#get problems solved by both users
#get problems avaliable via codeforces api 
#filter problems based on level and unseen 
#output link 
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#


@client.command()
async def duel(ctx, member: discord.Member, level: int): # example command: !duel @user 1500, spaces are not sensitive, i think 

    if not 800 <= level <= 3500 or level % 100 != 0:
        await ctx.send("Invalid problem difficulty >.<")
        return

    challenger = str(ctx.author.id) #get discord id of challenger
    opponent = str(member.id) #get discord id of opponent
    discordServer = str(ctx.guild.id) #get discord server id

    if discordServer not in userDict or challenger not in userDict[discordServer] or opponent not in userDict[discordServer]:
        await ctx.send("Registration error, do command !register codeforcesUsername")
        return
    
    challengerHandle = userDict[discordServer][challenger]
    opponentHandle = userDict[discordServer][opponent]

    #get filtered problems from codeforces api for challenger and opponent, bot outputs link 
    problemLink = await getConstraintedProblems(level, challengerHandle, opponentHandle)
    if problemLink:
        await ctx.send(f"Let the best coder win: {problemLink}")
    else:
        await ctx.send("Error: No suitable problem found.")


async def getConstraintedProblems(level, challengerHandle, opponentHandle):
    # getter for problem not seen for both users 
    challengerProblems = await getProblemNotSeen(challengerHandle)
    opponentProblems = await getProblemNotSeen(opponentHandle)

    # getter for all list of problems from codeforces api
    response = requests.get("https://codeforces.com/api/problemset.problems")
    if response.status_code != 200:
        return None

    data = response.json() #codeforces data is json 
    problems = data["result"]["problems"]

    # problem must be same level requested and not seen by both users
    problemsLevel = [p for p in problems if "rating" in p and p["rating"] == level]
    problemsNotSeen = [p for p in problemsLevel if (p["contestId"], p["index"]) not in challengerProblems and (p["contestId"], p["index"]) not in opponentProblems]

    if not problemsNotSeen:
        return None

    # pick random problem, returning filtered link 
    problem = random.choice(problemsNotSeen)
    return f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"


async def getProblemNotSeen(handle): #getting problem unseen by each user
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1" #url specific to user
    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()
    if data["status"] != "OK":
        return None

    problems = set()
    for submission in data["result"]:
        if submission["verdict"] == "OK":
            problem = submission["problem"]
            problems.add((problem["contestId"], problem["index"]))

    return problems


client.run(os.getenv('DISCORD_KEY'))
#client.run must be bottom of all code...
