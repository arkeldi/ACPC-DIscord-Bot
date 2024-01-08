import discord 
from discord.ext import commands
from dotenv import load_dotenv 
import os
import requests
import random 
from database.db import BotDatabase #importing BotDatabase class from db.py
import json
import aiohttp # pip install this
import asyncio
import time
import re

load_dotenv() #load discord bot key from .env file

#initialize bot 
client = commands.Bot(command_prefix = '!', intents = discord.Intents.all(), help_command=None) 
db = BotDatabase() #create instance of BotDatabase class

@client.event
async def on_ready(): 
    print("Bot is ready") 
    print("------------------") 

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
async def register(ctx, codeforces_handle: str):
    if not await verifyCodeforcesHandle(codeforces_handle):
        await ctx.send("That's not a codeforces username, trust me, i checked via api call xD")
        return
    
    discord_server_id = str(ctx.guild.id)
    discord_user_id = str(ctx.author.id)
    
    if db.is_verification_initiated(discord_user_id) or db.is_user_registered(discord_user_id):
        await ctx.send("You are already registered or in the process of verification.")
        return

    problem_url, problem_id = await getConstraintedProblemsForVerification(codeforces_handle)
    if not problem_url:
        await ctx.send("Failed to find a suitable problem for verification.")
        return

    db.initiate_verification(discord_server_id, discord_user_id, codeforces_handle, problem_id)

    await ctx.send(f"To complete your registration, please submit a solution that results in a compilation/runtime/wrong answer error for this problem: {problem_url}. Once done, use the command `!complete_verification`. In case of any issues, use the command `!restart_registration` to restart the registration process.")


@client.command()
async def complete_verification(ctx):
    discord_user_id = str(ctx.author.id)

    if not db.is_verification_initiated(discord_user_id):
        await ctx.send("You have not initiated a verification process.")
        return

    codeforces_handle, problem_id = db.get_verification_details(discord_user_id)
    if not codeforces_handle:
        await ctx.send("Verification details not found.")
        return

    # check_compilation_error_submission is now an async function, use await
    if await check_compilation_error_submission(codeforces_handle, problem_id):
        db.complete_verification(discord_user_id)
        await ctx.send(f"Verification successful! Your Codeforces account {codeforces_handle} has been linked with {ctx.author.mention}.")
    else:
        await ctx.send("Verification failed. Please ensure you have submitted a compilation/runtime/wrong answer error for the specified problem.")


@client.command()
async def delete_registration(ctx):
    discord_user_id = str(ctx.author.id)

    # Check if the user is registered
    if not db.is_user_registered(discord_user_id):
        await ctx.send("You are not currently registered.")
        return

    # Delete the user's registration
    db.delete_user_registration(discord_user_id)
    await ctx.send("Your registration has been successfully deleted.")


async def check_compilation_error_submission(handle, problem_id):
    """
    this checks if the Codeforces user handle has made a recent submission, within 5 min 
    with a compilation/wrong/answer error for the specified problem.

    :parameter handle: codeforces handle of user.
    :parameter problem_id: The ID of the problem to check submissions for, just good to keep track of 
    :return: true if an error submission is found, false otherwise
    """
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"API request failed with status code: {response.status}")
                    return False

                data = await response.json()
                if data["status"] != "OK":
                    print("Error in response from Codeforces API")
                    return False

        # parsing problem_id
        contest_id, index = '', ''
        if '-' in problem_id:
            contest_id, index = problem_id.split('-')
        else:
            match = re.match(r"(\d+)([A-Za-z]+)", problem_id)
            if match:
                contest_id, index = match.groups()

        if not contest_id or not index:
            print(f"Invalid problem_id format: {problem_id}")
            return False

        current_time = time.time()
        for submission in data["result"]:
            if (str(submission["problem"]["contestId"]) == contest_id and
                submission["problem"]["index"] == index and
                submission["verdict"] in ["COMPILATION_ERROR", "RUNTIME_ERROR", "WRONG_ANSWER"] and
                current_time - submission["creationTimeSeconds"] < 300):
                    return True
        return False

    except aiohttp.ClientError as e:
        print(f"Error fetching problems: {e}")
        return False


async def getConstraintedProblemsForVerification(codeforces_handle):
    userProblems = await getSolvedProblems(codeforces_handle)
    if userProblems is None:
        print(f"Failed to fetch problems for user handle: {codeforces_handle}")
        return None

    async with aiohttp.ClientSession() as session:
        async with session.get("https://codeforces.com/api/problemset.problems") as response:
            if response.status != 200:
                print("Failed to fetch problems from Codeforces API")
                return None
            data = await response.json()
            if data["status"] != "OK":
                print("Error in response from Codeforces API")
                return None

    problems = data["result"]["problems"]
    eligibleProblems = [p for p in problems if "rating" in p and p["rating"] == 800 and (p["contestId"], p["index"]) not in userProblems]

    if not eligibleProblems:
        print("No eligible problems found")
        return None

    problem = random.choice(eligibleProblems)
    contest_id = problem['contestId']
    index = problem['index']
    problem_url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"

    return problem_url, f"{contest_id}{index}"


async def verifyCodeforcesHandle(codeforces_handle):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://codeforces.com/api/user.info?handles={codeforces_handle}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data['status'] == 'OK'  
        except aiohttp.ClientError as e:
            print(f"API request error: {e}")
    return False



@client.command()
async def restart_registration(ctx):
    discord_user_id = str(ctx.author.id)

    if db.is_user_verified(discord_user_id):
        await ctx.send("You are already verified and cannot restart the registration process.")
        return

    if not db.is_verification_initiated(discord_user_id):
        await ctx.send("You have not started the registration process.")
        return

    db.reset_registration(discord_user_id)
    await ctx.send("Your registration process has been reset. You can now register again using `!register`.")


@client.command()
async def problemPractice(ctx, difficulty: int):
    problem_requester_id = str(ctx.author.id)
    discord_server_id = str(ctx.guild.id)
    problem_requester_handle = db.get_codeforces_handle(discord_server_id, problem_requester_id)

    problem = await getConstraintedProblems(difficulty, problem_requester_handle, problem_requester_handle)

    await ctx.send(f"Here's a problem of difficulty {difficulty}: {problem[0]}")


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
    await ctx.send(f"{member.mention}, you have been challenged to a duel by {ctx.author.mention}! Type  `!accept` to accept the challenge... if you dare.")


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
    problem_id = ongoing_duel["problem_id"]
    time1 = await getEarliestSubmissionTime(user_handle, problem_id)
    time2 = await getEarliestSubmissionTime(opponent_handle, problem_id)

    if time1 == -1 and time2 == -1:
        await ctx.send("Neither user has completed the problem. Nice try buddy :P")
        return

    winner_id = None
    if time1 != -1 and (time2 == -1 or time1 < time2):
        winner_id = discord_user_id
    elif time2 != -1 and (time1 == -1 or time2 < time1):
        winner_id = opponent_id

    if winner_id:
        db.update_duel_status(ongoing_duel["duel_id"], 'complete')

        loser_id = opponent_id if winner_id == discord_user_id else discord_user_id
        db.update_user_stats(winner_id, loser_id)

        winner_discord_user = await ctx.guild.fetch_member(int(winner_id))
        await ctx.send(f'{winner_discord_user.mention} has won the duel! Yeaaaa boiiiii')
    else:
        await ctx.send("It's a tie or unable to determine the winner.")


@client.command()
async def stats(ctx, member: discord.Member = None):
    member = member or ctx.author  # if no member is provided, use author
    user_stats = db.get_user_stats(ctx.guild.id, str(member.id))

    if user_stats is None:
        await ctx.send("No statistics available for this user.")
    else:
        duel_wins, duel_losses = user_stats
        await ctx.send(f"{member.mention}'s Stats: Wins - {duel_wins}, Losses - {duel_losses}")


@client.command()
async def problem(ctx, difficulty: int):
    problem_requester_id = str(ctx.author.id)
    discord_server_id = str(ctx.guild.id)
    problem_requester_handle = db.get_codeforces_handle(discord_server_id, problem_requester_id)

    problem = await getConstraintedProblems(difficulty, problem_requester_handle, problem_requester_handle)

    await ctx.send(f"Here's a problem of difficulty {difficulty}",problem[0])


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

    async with aiohttp.ClientSession() as session:
        async with session.get("https://codeforces.com/api/problemset.problems") as response:
            if response.status != 200:
                print("Failed to fetch problems from Codeforces API")
                return None
            data = await response.json()
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

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
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
                    print(f"API request failed with status code: {response.status}")
                    if response.content:
                        content = await response.text()
                        print(f"Response Content: {content}")
                    return None  
        except aiohttp.ClientError as e:
            print(f"Error fetching problems: {e}")
            return None


async def getEarliestSubmissionTime(handle, problem_id):
    earliest_time = -1
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=30"  # look at recent 30 submissions

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return -1

            data = await response.json()
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
        author_handle = submission.get("author", {}).get("members", [{}])[0].get("handle")

        # check if the submission is by the correct handle and matches the problem, xtra layer of security
        if (submission.get("verdict") == "OK" and 
            problem.get("contestId") == int(contest_id) and 
            problem.get("index") == index and 
            author_handle == handle):
            creation_time = submission.get("creationTimeSeconds", -1)
            if earliest_time == -1 or (creation_time != -1 and creation_time < earliest_time):
                earliest_time = creation_time

    return earliest_time


#help command for users 
@client.command()
async def help(ctx):
    help_command_message = """
    **Bot Commands:**
    `!help` - Provides the guide on using all the bot's commands and instructions
    `!register [codeforcesUsername]` - Register your Codeforces username with your Discord account
    `!restart_registration` - Restart the registration process, this can be used if you did not complete the verification process correctly
    `!delete_registration` - Delete your registration, link between the Codeforces username and Discord account you complete_registration with will be removed
    '!complete_verification' - Complete the verification process by submitting a compilation/runtime/wrong answer error for the specified problem
    `!duel @user level` - Challenge another member to a duel with a Codeforces level
    `!accept` - Accept the duel, you can @ the specific challenger to accept their duel if there are multiple initiated duels
    `!complete` - Duel as complete, check results, update winner
    `!stats` - Check your duel statistics

    **Examples:**
    - `!register myCodeforcesUsername`
    - `!duel @User123 1500`
    - `!accept @user` or `!accept`
    - `!complete`
    - `!stats`

    **Notes:**
    - Make sure your Codeforces username is correct when registering, the API does check anyway
    - Duel levels are between 800 and 3500, and divisible by 100
    - Commands related to duels require both users to be registered
    """
    await ctx.send(help_command_message)


client.run(os.getenv('DISCORD_KEY'))
#client.run must be bottom of all code...