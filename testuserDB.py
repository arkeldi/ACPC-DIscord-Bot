#in order to see if data is being stored in db, run this simple sql query:
import sqlite3

# connect to the database
conn = sqlite3.connect('/Users/arkeldi/Desktop/ACPC-Discord-Bot/database/discord_bot.db')
cursor = conn.cursor()
# query to see all rows from the user_registrations table
cursor.execute('SELECT * FROM user_registrations')
rows = cursor.fetchall()
# print
for row in rows:
    print(row)
conn.close()
