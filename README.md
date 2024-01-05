# ACPC Discord Duel Bot

ACPC Discord Duel Bot is a Discord bot designed to allow members to engage in a friendly coding game

## Features

Some features include 2-step regsitration which syncs up with each user's Codeforces account, challenging and accepting duels, and completing duels with results based on problem-solving time

I incoroparted the backend workflow of this program in a series of steps: 
When a user tried to !register their DiscordID with their Codeforces handle, this info is temporarily stored into the verification_process SQL table. 
Then if the user successfully completes the 2-step verification process, their information which was temporarily stored, 
Is then pushed into the verified_users table. 

This was the most robust and efficient way I planned out to work out this 2-step verification feature within the backend. 


### Main Features

Command is ;

- **Registration**:
  ![codeforceshandle]
  Link Discord IDs with Codeforces handles
  Bot gives a Codeforces problem link, asks user to submit a file that gives an error
- **Complete Registration**:
  ![complete_verification]
  If the user who initiated registration (discord link to Codeforces) successfully submits 
  API check to verify user has completed registration
- **Duel Challenges**:
  ![duel] @[otherMember] [codeForces level 800-3500, divisible by 100]
  Challenge others to solve specific Codeforces problems
- **Accepting Duels**:
  ![accept @specificUser]
  Accept challenges from other members
  Can @specific user initiated duel, to account for multiple duels initiated
- **Completing Duels**:
  ![complete]
  Determine duel winners based on problem-solving time and/or submission

### Additional Functionalities

- **Help Command**: Provides a guide on using all the bot's commands and instructions
- **Database Integration**: Manages user data and duel records using SQLite

### Environment Setup

Before running the bot, you need to set up the environment:

1. Create a `.env` file in the root directory of the project
2. Add the following environment variable to the `.env` file:
   - **DISCORD_KEY**: Your Discord bot token. This token is essential for the bot to connect to the Discord API

The `.env` file is crucial as it stores sensitive information like your bot token securely

### Database Setup

Before launching the bot, it's important to set up the database:

1. Run `init_db.py` to initialize and configure the SQLite database. This script will create the necessary tables for storing user data and duel records
   
   ```bash
   python3 init_db.py

2. You can run testDB.py to run a quick simple test case to see if the database is working

  ```bash
   python3 testDB.py
```

### Database Scheme
DBscheme.png, file in the GitHub repo, is a diagram that shows the relationships between the database table

### Running the Bot

To launch the bot, use:

```bash
python3 main.py
```


   


