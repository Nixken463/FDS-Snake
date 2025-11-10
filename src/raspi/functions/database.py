import sqlite3
from datetime import datetime

DB_NAME = "Leaderboard.db"

class DataBase:
    def __init__(self):
        try:
            self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cur = self.conn.cursor()
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS Highscores (Teamname TEXT, Punkte INTEGER, Zeitpunkt TEXT)"
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error connecting to database {DB_NAME}: {e}")
            self.conn = None
            self.cur = None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def append_team(self, teamname, score):
        """Appends a new team score to the database."""
        if not self.cur: return
        
        try:
            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cur.execute(
                "INSERT INTO Highscores VALUES(?,?,?)", (teamname, score, finished_at)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error appending team: {e}")

    def in_top10(self, score: int) -> bool:
        """Checks if a score is high enough for the top 10."""
        if not self.cur: return False
        
        try:
            self.cur.execute(
                "SELECT Punkte FROM Highscores ORDER BY Punkte DESC LIMIT 1 OFFSET 9"
            )
            row = self.cur.fetchone()
            if row is None:
                return True  # Database is not full, so it's in the top 10
            return score > row[0]
        except sqlite3.Error as e:
            print(f"Error checking top 10: {e}")
            return False

    def get_top_score(self) -> int:
        """Gets the single highest score from the database."""
        if not self.cur: return 0
        
        try:
            self.cur.execute("SELECT MAX(Punkte) FROM Highscores")
            result = self.cur.fetchone()
            return result[0] if result and result[0] is not None else 0
        except sqlite3.Error as e:
            print(f"Error getting top score: {e}")
            return 0

    def get_best_alltime(self):
        """Returns the top 10 scores of all time."""
        if not self.cur: return {"Highscores": []}
        
        try:
            self.cur.execute("SELECT * FROM Highscores ORDER BY Punkte DESC LIMIT 10")
            game_data = self.cur.fetchall()
            # Convert rows to dicts for JSON serialization
            return {"Highscores": [dict(row) for row in game_data]}
        except sqlite3.Error as e:
            print(f"Error getting all-time best: {e}")
            return {"Highscores": []}

    def get_best_date(self, days_ago: int, offset: int):
        """Returns top 10 scores from a specified date range."""
        if not self.cur: return {"Highscores": []}
        
        try:
            query = f"SELECT * FROM Highscores WHERE date(Zeitpunkt) >= date('now', '-{days_ago} days') ORDER BY Punkte DESC LIMIT 10 OFFSET ?"
            self.cur.execute(query, (offset,))
            best_date = self.cur.fetchall()
            return {"Highscores": [dict(row) for row in best_date]}
        except sqlite3.Error as e:
            print(f"Error getting best by date: {e}")
            return {"Highscores": []}

    def get_stats(self):
        """Returns game count statistics."""
        if not self.cur: return {}

        default_results = {"Daily": 0, "Weekly": 0, "Monthly": 0, "AllTime": 0}
        try:
            self.cur.execute(
                """
            SELECT
                COUNT(*),
                SUM(CASE WHEN date(Zeitpunkt) = date('now') THEN 1 ELSE 0 END),
                SUM(CASE WHEN date(Zeitpunkt) >= date('now', '-6 days') THEN 1 ELSE 0 END),
                SUM(CASE WHEN date(Zeitpunkt) >= date('now', '-29 days') THEN 1 ELSE 0 END) 
            FROM Highscores
                """
            )
            games_date = self.cur.fetchone()
            
            if games_date:
                results = {
                    "Daily": games_date[1] or 0,
                    "Weekly": games_date[2] or 0,
                    "Monthly": games_date[3] or 0,
                    "AllTime": games_date[0] or 0,
                }
                return results
            else:
                return default_results
        except sqlite3.Error as e:
            print(f"Error getting stats: {e}")
            return default_results
