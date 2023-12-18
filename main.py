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


# making api call to codeforces to verify handle
# pip3 install requests 
import requests

def verifyCodeforcesHandle(codeforcesHandle):
    response = requests.get("https://codeforces.com/api/user.info?handles=" + codeforcesHandle)
    if response.status_code == 200:
        return True 
    else:
        return False


client.run('') #run bot, update each time you change sthm in discord dev portal, 
#this must be the final line 