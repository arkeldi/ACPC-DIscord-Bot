import discord 
from discord.ext import commands
from dotenv import load_dotenv 
import os
import requests
import random 
from database.db import BotDatabase #importing BotDatabase class from db.py
import json

load_dotenv() #load discord bot key from .env file

#initialize bot 
client = commands.Bot(command_prefix = ';', intents = discord.Intents.all(), help_command=None) 
db = BotDatabase() #creating instance of BotDatabase class
#give prefix bot listens in for, using ; as prefix, after ; is command

@client.event
async def on_ready(): #when bot is ready to recieve commands
    print("Bot is ready") #user wont see this we will in terminal 
    print("------------------") #seperate for clarity 

@client.event
async def on_disconnect():
    # close when bot disconnects 
    db.close()
    print("Database connection closed.")

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
#added error handling
def verifyCodeforcesHandle(codeforces_handle):
    try:
        response = requests.get("https://codeforces.com/api/user.info?handles=" + codeforces_handle)
        if response.status_code == 200:
            return True 
    except requests.RequestException as e:
        print(f"API request error: {e}")
    return False 



#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#error handling/message

@client.event
async def on_command_error(ctx, error):
    # irgnore command not found errors
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"Oops, something went wrong: {error}.")

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#


@client.command()
async def duel(ctx, member: discord.Member, level: int):
    if not 800 <= level <= 3500 or level % 100 != 0:
        await ctx.send("Invalid problem difficulty >.<")
        return

    if member is None:
        await ctx.send("Provide a user. Example: `;duel @user [level]`")
        return

    challenger_id = str(ctx.author.id)
    challengee_id = str(member.id)
    discord_server_id = str(ctx.guild.id)

    challenger_handle = db.get_codeforces_handle(discord_server_id, challenger_id)
    challengee_handle = db.get_codeforces_handle(discord_server_id, challengee_id)

    if not challenger_handle or not challengee_handle:
        await ctx.send("Both users need to be registered with their Codeforces handles.")
        return

    problem_info = await getConstraintedProblems(level, challenger_handle, challengee_handle)
    
    if problem_info is None:
        await ctx.send("Failed to find a suitable problem. Please try again.")
        return

    problem_url, problem_id = problem_info

    db.create_duel_challenge(discord_server_id, challenger_id, challengee_id, level, problem_id)
    await ctx.send(f"{member.mention}, you have been challenged to a duel by {ctx.author.mention}! Type ;accept to accept the challenge... if you dare.")


@client.command()
async def accept(ctx, challenger: discord.Member=None):
    opponent_id = str(ctx.author.id)  # Get discord id of opponent
    discord_server_id = str(ctx.guild.id)

    #added @specificUser, if multipel duels are created 
    if challenger:
        duel_challenge = db.get_specific_duel_challenge(discord_server_id, str(challenger.id), opponent_id)
        if duel_challenge is None:
            await ctx.send(f"No duel challenge found from {challenger.mention}.")
            return
    else:
        duel_challenge = db.get_latest_duel_challenge(discord_server_id, opponent_id)
        if duel_challenge is None:
            await ctx.send("No duel challenge found.")
            return

    db.update_duel_status(duel_challenge['duel_id'], 'accepted')

    contest_id, index = duel_challenge['problem_id'][:-1], duel_challenge['problem_id'][-1]
    problem_url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"

    await ctx.send(f"The duel has been accepted! {ctx.author.mention} versus <@{duel_challenge['challenger_id']}>")
    await ctx.send(f"Problem: {problem_url}")


@client.command()
async def complete(ctx):
    discord_user_id = str(ctx.author.id)
    discord_server_id = str(ctx.guild.id)

    if not db.is_user_registered(discord_user_id):
        await ctx.send("Error: User is not registered.")
        return

    ongoing_duel = db.get_ongoing_duel(discord_server_id, discord_user_id)
    if ongoing_duel is None or ongoing_duel['status'] == 'pending':
        await ctx.send("Error: No ongoing duel found.")
        return

    if ongoing_duel['status'] == 'complete':
        await ctx.send("This duel has already been finished. Start another duel to play again.")
        return

    user_handle = db.get_codeforces_handle(discord_server_id, discord_user_id)
    opponent_id = ongoing_duel["challengee_id"] if ongoing_duel["challenger_id"] == discord_user_id else ongoing_duel["challenger_id"]
    opponent_handle = db.get_codeforces_handle(discord_server_id, opponent_id)

    # get problem id from duel 
    problem_id = ongoing_duel["problem_id"]

    #allow codeforces api to check for submissions
    time1 = await getEarliestSubmissionTime(user_handle, problem_id)
    time2 = await getEarliestSubmissionTime(opponent_handle, problem_id)

    if time1 == -1 and time2 == -1:
        await ctx.send("Neither user has completed the problem. Nice try buddy :P")
        return

    # determine winner
    if time1 != -1 and time2 != -1 and time1 == time2: #if both users did submit and they submitted at the same time, tie if case must come first 
        await ctx.send("It's a tie! You both suck. rip")
        return
    elif time1 != -1 and (time2 == -1 or time1 < time2): #if user1 submitted and (user2 didnt or user1 submitted faster than user2)
        winner_id = discord_user_id  #user who initiated the command wins
    elif time2 != -1 and (time1 == -1 or time2 < time1): #if user2 submitted and (user1 didnt or user2 submitted faster than user1)
        winner_id = opponent_id #user who took on the challenge wins
    else:
        await ctx.send("Unable to determine the winner.")
        return

    db.update_duel_status(ongoing_duel["duel_id"], 'complete')

    winner_discord_user = await ctx.guild.fetch_member(int(winner_id))
    await ctx.send(f'{winner_discord_user.mention} has won the duel! Yeaaaaa boiiiiiiiii')


async def getConstraintedProblems(level, challengerHandle, opponentHandle):
    challengerProblems = await getSolvedProblems(challengerHandle)
    if challengerProblems is None:
        print(f"Failed to fetch problems for challenger handle: {challengerHandle}")
        return None

    opponentProblems = await getSolvedProblems(opponentHandle)
    if opponentProblems is None:
        print(f"Failed to fetch problems for opponent handle: {opponentHandle}")
        return None

    combinedProblems = challengerProblems.union(opponentProblems)

    response = requests.get("https://codeforces.com/api/problemset.problems")
    if response.status_code != 200:
        print("Failed to fetch problems from Codeforces API")
        return None

    data = response.json()
    if data["status"] != "OK":
        print("Error in response from Codeforces API")
        return None

    problems = data["result"]["problems"]
    eligibleProblems = [p for p in problems if "rating" in p and p["rating"] == level and (p["contestId"], p["index"]) not in combinedProblems]

    if not eligibleProblems:
        print("No eligible problems found")
        return None

    problem = random.choice(eligibleProblems)
    problem_id = f"{problem['contestId']}{problem['index']}"
    return f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}", problem_id


#what the func above is doing: 
#1. get problems solved by challenger, calling get solved problem func
#2. get problems solved by opponent, calling get solved problem func
#3. combine problems solved by challenger and opponent
#4. get all problems from codeforces api
#5. filter problems by level and NOT solved by challenger or opponent
#6. pick a random problem from the filtered list
#7. return url and problem id


async def getSolvedProblems(handle): 
    if not handle or not isinstance(handle, str):
        print("Invalid handle provided.")
        return None 

    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1"
    print(f"Requesting URL: {url}")

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK":
                problems = set()
                for submission in data["result"]:
                    if submission["verdict"] == "OK":
                        problem = submission["problem"]
                        problems.add((problem["contestId"], problem["index"]))
                print(f"Found {len(problems)} problems solved by {handle}")
                return problems
            else:
                print(f"User handle not found or other API issue: {data['comment']}")
                return None  
        else:
            print(f"API request failed with status code: {response.status_code}")
            if response.content:
                print(f"Response Content: {response.content}")
            return None  
    except requests.RequestException as e:
        print(f"Error fetching problems: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}, Response content: {response.content}")
        return None


import re
async def getEarliestSubmissionTime(handle, problem_id):
    earliest_time = -1
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=100"
    response = requests.get(url)
    if response.status_code != 200:
        return -1
    
    data = response.json()
    if data["status"] != "OK":
        return -1


    match = re.match(r"(\d+)([A-Za-z]+)", problem_id)
    if match:
        contest_id, index = match.groups()
    else:
        print(f"Invalid problem_id format: {problem_id}")
        return -1


    for submission in data["result"]:
        problem = submission.get("problem", {})
        # debugging
        print(f"Checking problem {problem.get('contestId')} - {problem.get('index')} against {contest_id} - {index}")
        if submission.get("verdict") == "OK" and problem.get("contestId") == int(contest_id) and problem.get("index") == index:
            creation_time = submission.get("creationTimeSeconds", -1)
            print(f"Accepted submission found for problem {contest_id}-{index} at time {creation_time}")
            if earliest_time == -1 or (creation_time != -1 and creation_time < earliest_time):
                earliest_time = creation_time

    return earliest_time


#help command for users 
@client.command()
async def help(ctx):
    help_command_message = """
    **Bot Commands:**
    `;register [codeforcesUsername]` - Register your Codeforces username with your Discord account
    `;duel @user level` - Challenge another member to a duel with a Codeforces level
    `;accept` - Accept the duel, you can @ the challenger to accept their duel if there are multiple initiated duels
    `;complete` - Duel as complete, check results, update winner

    **Examples:**
    - `;register myCodeforcesUsername`
    - `;duel @User123 1500`
    - `;accept @user 
    - `;complete`

    **Notes:**
    - Make sure your Codeforces username is correct when registering
    - Duel levels are between 800 and 3500, and divisible by 100
    - Commands related to duels require both users to be registered
    """
    await ctx.send(help_command_message)

#database error handling
def database_error():
    try:
        db.some_database_operation()
    except SomeDatabaseException as e:
        print(f"Database error: {e}")
        return False
    return True

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
client.run(os.getenv('DISCORD_KEY'))
#client.run must be bottom of all code...

# note to run with database: 
# run testDB.py to see if data is being stored in db
# run python3 main.py to run bot



