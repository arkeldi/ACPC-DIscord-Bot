# ACPC Discord Bot

ACPC Discord Bot is a Discord bot designed for engaging in competitive programming challenges on Codeforces.

## Features

ACPC Discord Bot offers a variety of features, including user registration with Codeforces, challenging and accepting duels, and completing duels with results based on problem-solving time.

### Main Features

- **Registration**: Link Discord IDs with Codeforces handles.
- **Duel Challenges**: Challenge others to solve specific Codeforces problems.
- **Accepting Duels**: Accept challenges from other members.
- **Completing Duels**: Determine duel winners based on problem-solving time and/or submission.

### Additional Functionalities

- **Help Command**: Provides a guide on using the bot's commands.
- **Database Integration**: Manages user data and duel records using SQLite.

### Environment Setup

Create a `.env` file and fill in the environment variable:

- **DISCORD_KEY**: Your Discord bot token.


### Environment Setup

Before running the bot, you need to set up the environment:

1. Create a `.env` file in the root directory of the project.
2. Add the following environment variable to the `.env` file:
   - **DISCORD_KEY**: Your Discord bot token. This token is essential for the bot to connect to the Discord API.

The `.env` file is crucial as it stores sensitive information like your bot token securely.

### Running the Bot

To launch the bot, use:

```bash
python3 main.py

