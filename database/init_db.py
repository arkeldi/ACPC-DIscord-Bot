import sqlite3
import os 
from dotenv import load_dotenv

def init_db():

    load_dotenv()

    # connect to the SQLite database
    #DISCORD_BOT_DB_PATH is stored in .env file, with Discord bot token
    db_file = os.getenv('DISCORD_BOT_DB_PATH', 'discord_bot.db') 
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS duel_challenges ( 
            duel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_server_id TEXT NOT NULL,
            challenger_id TEXT NOT NULL,
            challengee_id TEXT NOT NULL,
            problem_level INTEGER,
            status TEXT,
            problem_id TEXT,
            FOREIGN KEY (discord_server_id, challenger_id) REFERENCES verified_users (discord_server_id, discord_user_id),
            FOREIGN KEY (discord_server_id, challengee_id) REFERENCES verified_users (discord_server_id, discord_user_id)
        );
    ''')


#fix guild awareness here and in main.py, scroll a lil up in chat gpt

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verified_users (
            discord_user_id TEXT NOT NULL,
            discord_server_id TEXT NOT NULL,
            codeforces_handle TEXT NOT NULL,
            problem_id TEXT, 
            duel_wins INTEGER DEFAULT 0,
            duel_losses INTEGER DEFAULT 0,
            PRIMARY KEY (discord_user_id, discord_server_id)
        );
    ''')
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_process (
            discord_user_id TEXT NOT NULL,
            discord_server_id TEXT NOT NULL,
            codeforces_handle TEXT NOT NULL,
            problem_id TEXT,
            PRIMARY KEY (discord_user_id, discord_server_id)
        );
     ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS current_duel_party (
        discord_server_id TEXT PRIMARY KEY,
        problem_id TEXT
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS duel_party_participants (
    discord_server_id TEXT PRIMARY KEY,
    participant_handles TEXT
    );
    ''')
                   

    # commit and close
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()