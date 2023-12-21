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

duelChallenges = {}
ongoingDuels = {}

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
    
    if discordServer not in duelChallenges:
        duelChallenges[discordServer] = {}

    duelChallenges[discordServer][challenger] = (opponent, level) #store duel challenge in list of challenges
    #in server, user1 challenges user2 to a duel of level x
    #key is discordServer, manage duels for each server 
    #value is tuple: (opponent, level)
    await ctx.send(f"{member.mention}, you have been challenged to a duel by {ctx.author.mention}! Type !accept to accept the challenge... if you dare.")


@client.command()
async def accept(ctx):
    opponentID = str(ctx.author.id) #get discord id of opponent, see if there is ongoing duel in the server
    discordServer = str(ctx.guild.id)

    if discordServer in duelChallenges: #if there is a duel challenge in the server
        for challengerID, (oppID, level) in list(duelChallenges[discordServer].items()): #loop through all challenges in the server
            if oppID == opponentID: #check is current user is the one being challenged, oppID
                challengerHandle = userDict[discordServer][challengerID]
                opponentHandle = userDict[discordServer][opponentID]
                problem = await getConstraintedProblems(level, challengerHandle, opponentHandle)
                print("problem",problem)
                if problem:
                    await ctx.send(f"Ready, set, code: {problem[0]}")
                    ongoingDuels[challengerID] = [opponentID,problem[1]]
                    ongoingDuels[opponentID] = [challengerID,problem[1]]
                else:
                    await ctx.send("error.")
                
                #remove challenge from list
                del duelChallenges[discordServer][challengerID]
                return 
        #if we get here, no challenge found
    await ctx.send("Challenge not found")

@client.command()
async def complete(ctx):
    userID = str(ctx.author.id)
    discordServer = str(ctx.guild.id)

    #check that they are registered
    if userID not in userDict[discordServer]:
        await ctx.send("Error. user is not registered")
        return
    #check that there is an ongoing duel
    codeForcesHandle = userDict[discordServer][userID]
    if userID not in ongoingDuels:
        await ctx.send("Error. User is not currently in a duel")
        return
    #find completion times of both people
    duel = ongoingDuels[userID]
    user1 = userID
    user2 = duel[0]
    handle1 = userDict[discordServer][userID]
    handle2 = userDict[discordServer][duel[0]]
    print("duel[1]",duel[1])
    time1 = await getEarliestSubmissionTime(handle1, duel[1])
    time2 = await getEarliestSubmissionTime(handle2, duel[1])
    print("time1",time1)
    print("time2",time2)

    #compare and print results
    if time1 == -1 and time2 == -1:
        await ctx.send("Neither user has completed the problem")
        return

    if time2 == -1:
        await ctx.send(f'User <@{user1}> has beaten user <@{user2}>')
    elif time1 == -1:
        await ctx.send(f'User <@{user2}> has beaten user <@{user1}>')
    elif time1 < time2:
        await ctx.send(f'User <@{user1}> has beaten user <@{user2}>')
    else:
        await ctx.send(f'User <@{user2}> has beaten user <@{user1}>')

    del ongoingDuels[user1]
    del ongoingDuels[user2]

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



client.run(os.getenv('DISCORD_KEY'))
#client.run must be bottom of all code...
