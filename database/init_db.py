import sqlite3

def init_db():
    # connect to the SQLite database
    conn = sqlite3.connect('/Users/arkeldi/Desktop/ACPC-Discord-Bot/database/discord_bot.db')

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

    # commit and close
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()