# ACPC Discord Duel Bot

ACPC Discord Duel Bot is a Discord bot designed to allow members to engage in a friendly coding game

Our bot works asynchronously, which means that it can handle multiple commands/tasks simultaneously without waiting for each API call to finish. 
Implementing asynchronous calls is like having several hot dog stands instead of just one. This way, instead of a long line of users waiting at a single stand, multiple stands can serve users all at the same time. 

I decided that this was an essential implementation to take in deploying our bot. As a result, interactions are responsive and more robust, enhancing the overall user experience.

This bot is hosted on AWS EC2 for faster response times, 24/7 online service and better management. I found out that AWS gives you a free 1 year trial so this was the best option for our bot! 

## Features and Framework Workflow 

Main features include 2-step regsitration which syncs up with each user's Codeforces account, challenging and accepting duels, and completing duels with results based on problem-solving time

I incoroparted the backend workflow of the register command in a series of steps: 
When a user tried to !register their DiscordID with their Codeforces handle, this info is temporarily stored into the verification_process SQL table. 
Then, if the user successfully completes the 2-step verification process, their information which was temporarily stored, 
Is then pushed into the verified_users table. 
In case of any mishaps, users can delete their registration and restart. 
This way, error and test case handling are extremely robust; duplicate calls are handled well because of the backend workflow.

Similarly, the workflow of the dueling works in these steps: 
Registered users initiate a duel, ex. !duel @otherUser 800, this duel is now in the database with a 'pending' tag
If the otherUser !accepts, the duel is updated to 'accepted', the duel is now in play. 
The Codeforces problem is selected based on requested level and is a problem neither user has ever seen before, to ensure fairness. 
The user with the faster time is notified as the winner. The bot finally updates the duel's status in the database to 'completed' and records the winner's ID.

### Commands

Command is !

    **Bot Commands:**
    - `!help` - Provides the guide on using all the bot's commands and instructions
    - `!register [codeforcesUsername]` - Register your Codeforces account with your Discord account
    - `!restart_registration` - Can be used if you did not complete the verification process yet or if you want to change your Codeforces username before completing verification 
    - `!delete_registration` - Delete your registration, link between the Codeforces username and Discord account you complete_registration with will be removed
    - `!complete_verification` - Do this command after you complete the verification process by submitting a compilation/runtime/wrong answer error for the specified problem
    - `!duel @user level` - Challenge another member to a duel with a Codeforces level
    - `!accept` - Accept the duel, you can @ the specific challenger to accept their duel if there are multiple initiated duels
    - `!accept @user` - Accept the duel from a specific user if there are multiple initiated duels
    - `!complete` - Duel as complete, check results, update winner
    - `!stats` - Check your 1v1 duel statistics
    - `!problemPractice level [tag]` - Get a problem of a specific level, and optionally a tag, that you have not solved before
    - `!duel_party level @user1 @user2 @user3` - Start a duel party with a specific level and users, first to solve the problem wins
    - `!complete_duel_party` - Complete the duel party, check results, update winner
    

### Additional Functionalities

- **Coding Practice**: Users can use the bot to give them random coding problems with a specific topic. Ex. !problemPractice 1500 dp or !problemPractice 1500 strings
- **Database Integration**: Manages user data and duel records using SQLite
- **Exceptional Test Case Handling**: Tese are covered in every way possible because of thorough planning and testing of bot. Take my word for it!
- **Debugging**: Code has thorough debugging statements to make testing more efficient and reduce silent fails 

### Environment Setup

Before running the bot, you need to set up the environment:

1. Create a `.env` file in the root directory of the project
2. Add the following environment variable to the `.env` file:
   - **DISCORD_KEY**: Your Discord bot token. This token is essential for the bot to connect to the Discord API
   - **DISCORD_BOT_DB_PATH**: Your discord_bot.db path, created after running init_db.py (the file that contains all SQL tables)

The `.env` file is crucial as it stores sensitive information like your bot token securely

### Database Setup

Before launching the bot, it's important to set up the database:

1. Run `init_db.py` to initialize and configure the SQLite database. This script will create the necessary tables for storing user data and duel records
   
   ```bash
   python3 init_db.py


### Database Scheme
DatabaseScheme.png, file in the GitHub repo, is a diagram that shows the relationships between the database table

### Running the Bot

To launch the bot, use:

```bash
python3 main.py
```

