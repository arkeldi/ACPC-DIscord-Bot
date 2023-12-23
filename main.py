import discord 
from discord.ext import commands
from dotenv import load_dotenv 
import os
import requests
import random 
from database.db import BotDatabase #importing BotDatabase class from db.py

load_dotenv() #load discord bot key from .env file

#initialize bot 
client = commands.Bot(command_prefix = ';', intents = discord.Intents.all()) 
db = BotDatabase() #creating instance of BotDatabase class
#give prefix bot listens in for, using ! as prefix, after ! is command

@client.event
async def on_ready(): #when bot is ready to recieve commands
    print("Bot is ready") #user wont see this we will in terminal 
    print("------------------") #seperate for clarity 

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#

#**** note *****
#using discord id's, ctx.author.id and member.id, remain the same regardless of username changes

@client.command() # register command: !register codeforcesUsername, linking discord id to codeforces handle while in the right guild aka server
async def register(ctx, codeforces_handle: str):
    if not verifyCodeforcesHandle(codeforces_handle):
        await ctx.send("Incorrect Codeforces Username, check again silly goose")
        return
    db.register_user(ctx.guild.id, ctx.author.id, codeforces_handle) #adding this data to database, user_registrations table
    await ctx.send(f"You have registered {codeforces_handle} with {ctx.author.mention}")


# making api call to codeforces to verify handle
def verifyCodeforcesHandle(codeforces_handle):
    response = requests.get("https://codeforces.com/api/user.info?handles=" + codeforces_handle)
    if response.status_code == 200:
        return True 
    else:
        return False 


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#

@client.command()
async def duel(ctx, member: discord.Member, level: int): # example command: !duel @user 1500, spaces are not sensitive, i think 
    
    if not 800 <= level <= 3500 or level % 100 != 0:
        await ctx.send("Invalid problem difficulty >.<")
        return

    challenger = str(ctx.author.id) #get discord id of challenger
    opponent = str(member.id) #get discord id of opponent
    discordServer = str(ctx.guild.id) #get discord server id

    if not db.is_user_registered(challenger) or not db.is_user_registered(opponent):
        await ctx.send("Error. One or more users are not registered")
        return

    #adding duel in db 
    db.create_duel_challenge(discordServer, challenger, opponent, level) #create duel challenge in database
    await ctx.send(f"{member.mention}, you have been challenged to a duel by {ctx.author.mention}! Type !accept to accept the challenge... if you dare.")



@client.command()
async def accept(ctx):
    opponentID = str(ctx.author.id) #get discord id of opponent, see if there is ongoing duel in the server
    
    duel_challenge = db.get_duel_challenge(str(ctx.guild.id), opponentID)
    if duel_challenge is None:
        await ctx.send("Challenge not found")
        return
    # update duel status to accepted
    db.update_duel_status(duel_challenge['duel_id'], 'accepted')
    await ctx.send(f" The duel has been accepted! {ctx.author.mention} versus <@{duel_challenge['challenger_id']}>")



@client.command()
async def complete(ctx):
    user_id = str(ctx.author.id)
    discord_server_id = str(ctx.guild.id)

    if not db.is_user_registered(user_id):
        await ctx.send("Error. User is not registered")
        return

    ongoing_duel = db.get_ongoing_duel(discord_server_id, user_id)
    if ongoing_duel is None:
        await ctx.send("Error. User is not currently in a duel")
        return

    # Assume problem_id is stored in ongoing_duel
    problem_id = ongoing_duel["problem_id"]

    time1 = await getEarliestSubmissionTime(user_id, problem_id)
    opponent_id = ongoing_duel["opponent_id"]
    time2 = await getEarliestSubmissionTime(opponent_id, problem_id)

    if time1 == -1 and time2 == -1:
        await ctx.send("Neither user has completed the problem")
    elif time2 == -1 or time1 < time2:
        await ctx.send(f'User <@{user_id}> has beaten user <@{opponent_id}>')
    else:
        await ctx.send(f'User <@{opponent_id}> has beaten user <@{user_id}>')

    # update duel status in the database ******** to do **********
    db.update_duel_status(ongoing_duel["duel_id"], 'completed')


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
    return f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}", problem


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

async def getEarliestSubmissionTime(handle, problem):
    earliestTime = -1
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1"
    response = requests.get(url)
    if response.status_code != 200:
        return -1
    
    data = response.json()
    if data["status"] != "OK":
        return -1

    for submission in data["result"]:
        if submission["verdict"] == "OK" and submission["problem"] == problem: # correct problem
            if earliestTime == -1 or earliestTime != -1 and submission["creationTimeSeconds"] < earliestTime: # better time
                earliestTime = submission["creationTimeSeconds"]

    return earliestTime

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
client.run(os.getenv('DISCORD_KEY'))
#client.run must be bottom of all code...

# note to run with database: 



