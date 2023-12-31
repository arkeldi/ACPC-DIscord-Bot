import sqlite3

def init_db():
    # connect to the SQLite database
    conn = sqlite3.connect('/Users/arkeldi/Desktop/ACPC-Discord-Bot/database/discord_bot.db')

    # create cursor object to execute SQL commands
    cursor = conn.cursor()

    # SQL command to create table for user registrations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_registrations (
            discord_server_id TEXT,
            discord_user_id TEXT PRIMARY KEY,
            codeforces_handle TEXT NOT NULL,
            UNIQUE(discord_server_id, discord_user_id)
        );
    ''')

    # SQL command to create table for duel challenges
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS duel_challenges ( 
            duel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_server_id TEXT NOT NULL,
            challenger_id TEXT NOT NULL,
            challengee_id TEXT NOT NULL,
            problem_level INTEGER,
            status TEXT,
            problem_id TEXT,  
            FOREIGN KEY (challenger_id) REFERENCES user_registrations(discord_user_id),
            FOREIGN KEY (challengee_id) REFERENCES user_registrations(discord_user_id)
        );
    ''')

    # commit and close
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()

#sqlite3 /Users/arkeldi/Desktop/ACPC-Discord-Bot/database/discord_bot.db