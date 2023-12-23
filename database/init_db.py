# define database scheme here 
# sql commands to create tables
import sqlite3

#  initialize the database and create tables
def init_db():
    #connect to the SQLite database
    #conn = sqlite3.connect('discord_bot.db')
    conn = sqlite3.connect('/Users/arkeldi/Desktop/ACPC-Discord-Bot/database/discord_bot.db')


    # create cursor obj to execute SQL commands
    # cursors are like pointers used to go through commands and execute them
    cursor = conn.cursor()

    # sql command to create table for user registrations
    cursor.execute
    ('''
    CREATE TABLE IF NOT EXISTS user_registrations (
        discord_server_id TEXT,
        discord_user_id TEXT PRIMARY KEY,
        codeforces_handle TEXT NOT NULL,
        UNIQUE(discord_server_id, discord_user_id)
    );
    ''')

    # sql command to create table for duel challenges
    cursor.execute
    #autoincrementing duel_id to keep track 
    #the not nulls mean that they have to have a value 
    #foreign key means that the value has to be in the other table, straight line, one to many, one user can have many duels
    ('''
    CREATE TABLE IF NOT EXISTS duel_challenges ( 
        duel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_server_id TEXT NOT NULL,
        challenger_id TEXT NOT NULL,
        challengee_id TEXT NOT NULL,
        problem_level INTEGER,
        status TEXT,
        FOREIGN KEY (challenger_id) REFERENCES user_registrations(discord_user_id),
        FOREIGN KEY (challengee_id) REFERENCES user_registrations(discord_user_id)
    );
    ''')
    # commit and close 
    conn.commit()
    conn.close()

# run to create tables
if __name__ == '__main__':
    init_db()
