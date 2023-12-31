# functions to get data from database 
# path: database/db.py

import sqlite3

class BotDatabase:
    def __init__(self, db_file='/Users/arkeldi/Desktop/ACPC-Discord-Bot/database/discord_bot.db'):
        print(f"Using database file: {db_file}")
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row

    def register_user(self, discord_server_id, discord_user_id, codeforces_handle):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO user_registrations (discord_server_id, discord_user_id, codeforces_handle)
                VALUES (?, ?, ?)
                ON CONFLICT(discord_user_id) DO UPDATE SET codeforces_handle = excluded.codeforces_handle
            ''', (discord_server_id, discord_user_id, codeforces_handle))
        
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        # error
    
    def get_codeforces_handle(self, discord_server_id, discord_user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT codeforces_handle FROM user_registrations
                WHERE discord_server_id = ? AND discord_user_id = ?
            ''', (discord_server_id, discord_user_id))
            row = cursor.fetchone()
            return row['codeforces_handle'] if row else None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None


    def is_user_registered(self, discord_user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user_registrations WHERE discord_user_id = ?', (discord_user_id,))
        return cursor.fetchone() is not None



    def create_duel_challenge(self, discord_server_id, challenger_id, challengee_id, level, problem_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO duel_challenges (discord_server_id, challenger_id, challengee_id, problem_level, status, problem_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (discord_server_id, challenger_id, challengee_id, level, 'pending', problem_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during create_duel_challenge: {e}")


    def get_ongoing_duel(self, discord_server_id, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM duel_challenges
                WHERE discord_server_id = ? AND (challenger_id = ? OR challengee_id = ?) AND (status = 'accepted' OR status = 'ongoing' OR status = 'complete')
                ORDER BY duel_id DESC
                LIMIT 1
            ''', (discord_server_id, user_id, user_id))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def update_duel_status(self, duel_id, new_status, winner_id=None):
        try:
            cursor = self.conn.cursor()
            if winner_id:
                cursor.execute('''
                    UPDATE duel_challenges SET status = ?, winner_id = ? WHERE duel_id = ?
                ''', (new_status, winner_id, duel_id))
            else:
                cursor.execute('''
                    UPDATE duel_challenges SET status = ? WHERE duel_id = ?
                ''', (new_status, duel_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during update_duel_status: {e}")
    

    def get_duel_challenge(self, discord_server_id, challengee_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT duel_id, discord_server_id, challenger_id, challengee_id, problem_level, status, problem_id
            FROM duel_challenges 
            WHERE discord_server_id = ? AND challengee_id = ? AND status = 'pending'
        ''', (discord_server_id, challengee_id))
        return cursor.fetchone()

    def get_specific_duel_challenge(self, discord_server_id, challenger_id, challengee_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT duel_id, discord_server_id, challenger_id, challengee_id, problem_level, status, problem_id
            FROM duel_challenges
            WHERE discord_server_id = ? AND challenger_id = ? AND challengee_id = ? AND status = 'pending'
            ORDER BY duel_id DESC
        ''', (discord_server_id, challenger_id, challengee_id))
        return cursor.fetchone()

    def get_latest_duel_challenge(self, discord_server_id, challengee_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT duel_id, discord_server_id, challenger_id, challengee_id, problem_level, status, problem_id
            FROM duel_challenges
            WHERE discord_server_id = ? AND challengee_id = ? AND status = 'pending'
            ORDER BY duel_id DESC
            LIMIT 1
        ''', (discord_server_id, challengee_id))
        return cursor.fetchone()



    def close(self):
        self.conn.close()
