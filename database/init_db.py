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
            discord_user_id TEXT,
            FOREIGN KEY (challenger_id) REFERENCES verified_users (discord_user_id),
            FOREIGN KEY (challengee_id) REFERENCES verified_users (discord_user_id)
        );
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verified_users (
            discord_user_id TEXT PRIMARY KEY,
            discord_server_id TEXT,
            codeforces_handle TEXT NOT NULL,
            problem_id TEXT, 
            duel_wins INTEGER DEFAULT 0,
            duel_losses INTEGER DEFAULT 0
        );
    ''')
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_process (
            discord_user_id TEXT PRIMARY KEY,
            discord_server_id TEXT,
            codeforces_handle TEXT NOT NULL,
            problem_id TEXT
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