import discord 
from discord.ext import commands
from dotenv import load_dotenv 
import os
import requests
import random 
from database.db import BotDatabase #importing BotDatabase class from db.py

load_dotenv() #load discord bot key from .env file

#initialize bot 
client = commands.Bot(command_prefix = ';', intents = discord.Intents.all(), help_command=None) 
db = BotDatabase() #creating instance of BotDatabase class
#give prefix bot listens in for, using ; as prefix, after ; is command

@client.event
async def on_ready(): #when bot is ready to recieve commands
    print("Bot is ready") #user wont see this we will in terminal 
    print("------------------") #seperate for clarity 

#@client.event
#async def on_disconnect():
    # close when bot disconnects 
#    db.close()
#    print("Database connection closed.")
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
#Error handling 

@client.event
async def on_command_error(ctx, error):
    # irgnore command not found errors
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"Oops, something went wrong: {error}. Make sure you are using the correct command: ;duel @user level")

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------#

@client.command()
async def duel(ctx, member: discord.Member, level: int): # example command: ;duel @user 1500, spaces are not sensitive, i think 
    
    if not 800 <= level <= 3500 or level % 100 != 0:
        await ctx.send("Invalid problem difficulty >.<")
        return
    
    if member is None or level is None:
        await ctx.send("provide a user and level. example: `;duel @user [level]`")
        return

    challenger = str(ctx.author.id) #get discord id of challenger
    opponent = str(member.id) #get discord id of opponent
    discordServer = str(ctx.guild.id) #get discord server id

    #adding duel in db 
    db.create_duel_challenge(discordServer, challenger, opponent, level) #create duel challenge in database
    await ctx.send(f"{member.mention}, you have been challenged to a duel by {ctx.author.mention}! Type ;accept to accept the challenge... if you dare.")



@client.command()
async def accept(ctx, challenger: discord.Member=None):
    opponentID = str(ctx.author.id) #get discord id of opponent, see if there is ongoing duel in the server
    discordServer = str(ctx.guild.id)
    
    # if challenger is specified, @user, after ;accept, then get specific duel challenge,else go to last duel challenge
    if challenger:
        duel_challenge = db.get_specific_duel_challenge(discordServer, str(challenger.id), opponentID)
        if duel_challenge is None:
            await ctx.send(f"No duel challenge found from {challenger.mention}.")
            return
    else:
        duel_challenge = db.get_latest_duel_challenge(discordServer, opponentID)
        if duel_challenge is None:
            await ctx.send("No duel challenge found.")
            return

    # update duel status to accepted
    db.update_duel_status(duel_challenge['duel_id'], 'accepted')

    
    problem_url, _ = await getConstraintedProblems(duel_challenge['problem_level'], duel_challenge['challenger_id'], duel_challenge['challengee_id'])
    if problem_url:
        await ctx.send(f"Duel problem: {problem_url}. Solve this problem to win the duel!")
    else:
        await ctx.send("Could not find a suitable problem.")

    await ctx.send(f"The duel has been accepted! {ctx.author.mention} versus <@{duel_challenge['challenger_id']}>")



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


async def getProblemNotSeen(handle): #get unseen problem from each user
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1"
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
                return problems
    except requests.RequestException as e:
        print(f"Error fetching problems: {e}")

    return set()  # Return an empty set if there are no problems or in case of errors


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



