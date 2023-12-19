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

@client.command()
async def duel(ctx, member: discord.Member, level: int): # example command: !duel @user 1500

    challenger = str(ctx.author.id) #get discord id of challenger
    opponent = str(member.id) #get discord id of opponent
    discordServer = str(ctx.guild.id) #get discord server id

    if discordServer not in userDict or challenger not in userDict[discordServer] or opponent not in userDict[discordServer]:
        await ctx.send("One of you is not registered, do command !register codeforcesUsername")
        return
    challengerHandle = userDict[discordServer][challenger]
    opponentHandle = userDict[discordServer][opponent]

    #get problems from codeforces api for challenger
    challengerProblem = await getProblem(challengerHandle)
    challengerLink = await giveLink(level, challengerProblem)

    if challengerLink:
        await ctx.send(f"{ctx.author.mention}, click if you dare: {challengerLink}")
    else: 
        await ctx.send("error, no problem found. rip.")


    #and now opponent    
    opponentProblem = await getProblem(opponentHandle)
    opponentLink = await giveLink(level, opponentProblem)

    if opponentLink:
        await ctx.send(f"{member.mention}, click if you dare: {opponentLink}")
    else:
        await ctx.send("error, no problem found. rip.")
    

async def getLink(level, ):
    






async def getProblem(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    
    response = response.json()
    if response["status"] != "OK":
        return None
    problems = set() 
    for submission in response["result"]:
        if submission["verdict"] == "OK":
            problem = submission["problem"]
            problems.add((problem["contestId"], problem["index"]))
    return problems

async def filterProblem(ctx, level, challengerProblem, opponentProblem):
    response = requests.get("https://codeforces.com/api/problemset.problems")
    if response.status_code != 200:
        await ctx.send("error getting problem")
        return
    response = response.json()
    problems = response["result"]["problems"]
    problemsLevel = [p for p in problems if "rating" in p and p["rating"] == level] #check problems equal to specificed level in command 
    problemsNotSeen = [p for p in problemsLevel if (p["contestId"], p["index"]) not in challengerProblem and (p["contestId"], p["index"]) not in opponentProblem]

    if len(problemsNotSeen) == 0:
        await ctx.send("No problems available")
        return

    problem = random.choice(problemsNotSeen)
    await ctx.send(f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}")
    return



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


# making api call to codeforces to verify handle
def verifyCodeforcesHandle(codeforcesHandle):
    response = requests.get("https://codeforces.com/api/user.info?handles=" + codeforcesHandle)
    if response.status_code == 200:
        return True 
    else:
        return False 


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#

#check which problems have been solved by codeforces accoint 


client.run(os.getenv('DISCORD_KEY'))
#run bot, update each time you change sthm in discord dev portal, stored key 
#client.run must be bottom of all code...