"""
Database operations for the Guess the Word Game
Handles all SQLite database interactions
"""
import sqlite3
import os
from datetime import datetime, date
from config import Config
from models import PasswordManager

class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.ensure_instance_directory()
        self.init_database()
    
    def ensure_instance_directory(self):
        """Create instance directory if it doesn't exist"""
        instance_dir = os.path.dirname(self.db_path)
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database with all required tables and initial data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            self._create_tables(cursor)
            self._insert_initial_words(cursor)
            self._create_default_admin(cursor)
            conn.commit()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _create_tables(self, cursor):
        """Create all required database tables"""
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                user_type TEXT NOT NULL DEFAULT 'player',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Words table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Game sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_word TEXT NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                is_won BOOLEAN DEFAULT FALSE,
                game_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Guesses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                guess_word TEXT NOT NULL,
                guess_number INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES game_sessions (id)
            )
        ''')
        
        print("✅ Database tables created")
    
    def _insert_initial_words(self, cursor):
        """Insert initial 20 words if they don't exist"""
        for word in Config.INITIAL_WORDS:
            cursor.execute('INSERT OR IGNORE INTO words (word) VALUES (?)', (word,))
        print("✅ Initial words loaded")
    
    def _create_default_admin(self, cursor):
        """Create default admin user if it doesn't exist"""
        admin_password_hash = PasswordManager.hash_password(Config.DEFAULT_ADMIN_PASSWORD)
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, user_type) 
            VALUES (?, ?, ?)
        ''', (Config.DEFAULT_ADMIN_USERNAME, admin_password_hash, 'admin'))
        print("✅ Default admin user created")

class UserRepository:
    """Handles user-related database operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_user(self, username, password):
        """Create a new user account"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = PasswordManager.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, user_type) 
                VALUES (?, ?, ?)
            ''', (username, password_hash, 'player'))
            user_id = cursor.lastrowid
            conn.commit()
            return True, user_id
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, password_hash, user_type 
                FROM users 
                WHERE username = ?
            ''', (username,))
            
            user_data = cursor.fetchone()
            if not user_data:
                return False, None, "Invalid username"
            
            user_id, username, stored_hash, user_type = user_data
            
            if PasswordManager.verify_password(password, stored_hash):
                return True, {
                    'id': user_id,
                    'username': username,
                    'user_type': user_type
                }, "Login successful"
            else:
                return False, None, "Invalid password"
        
        except Exception as e:
            return False, None, str(e)
        finally:
            conn.close()
    
    def get_all_players(self):
        """Get list of all player usernames for admin reports"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT username FROM users 
                WHERE user_type = 'player' 
                ORDER BY username
            ''')
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting players: {e}")
            return []
        finally:
            conn.close()

class GameRepository:
    """Handles game-related database operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_random_word(self):
        """Get a random word for the game"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT word FROM words ORDER BY RANDOM() LIMIT 1')
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting random word: {e}")
            return None
        finally:
            conn.close()
    
    def get_daily_game_count(self, user_id, game_date=None):
        """Get number of games played by user on a specific date"""
        if game_date is None:
            game_date = date.today()
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM game_sessions 
                WHERE user_id = ? AND game_date = ?
            ''', (user_id, game_date))
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting daily game count: {e}")
            return 0
        finally:
            conn.close()
    
    def create_game_session(self, user_id, target_word):
        """Create a new game session"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            today = date.today()
            cursor.execute('''
                INSERT INTO game_sessions (user_id, target_word, game_date) 
                VALUES (?, ?, ?)
            ''', (user_id, target_word, today))
            session_id = cursor.lastrowid
            conn.commit()
            return session_id
        except Exception as e:
            print(f"Error creating game session: {e}")
            return None
        finally:
            conn.close()
    
    def save_guess(self, session_id, guess_word, guess_number):
        """Save a guess to the database"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO guesses (session_id, guess_word, guess_number) 
                VALUES (?, ?, ?)
            ''', (session_id, guess_word, guess_number))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving guess: {e}")
            return False
        finally:
            conn.close()
    
    def complete_game_session(self, session_id, is_won):
        """Mark a game session as completed"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE game_sessions 
                SET is_completed = TRUE, is_won = ? 
                WHERE id = ?
            ''', (is_won, session_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error completing game session: {e}")
            return False
        finally:
            conn.close()

class ReportRepository:
    """Handles admin reporting database operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_daily_report(self, report_date):
        """Get daily statistics for admin report"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(*) as total_games,
                    SUM(CASE WHEN is_won = 1 THEN 1 ELSE 0 END) as correct_guesses
                FROM game_sessions 
                WHERE game_date = ?
            ''', (report_date,))
            
            return cursor.fetchone()
        except Exception as e:
            print(f"Error getting daily report: {e}")
            return (0, 0, 0)
        finally:
            conn.close()
    
    def get_user_report(self, username):
        """Get user-specific statistics for admin report"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    gs.game_date,
                    COUNT(*) as words_tried,
                    SUM(CASE WHEN gs.is_won = 1 THEN 1 ELSE 0 END) as correct_guesses
                FROM game_sessions gs
                JOIN users u ON gs.user_id = u.id
                WHERE u.username = ?
                GROUP BY gs.game_date
                ORDER BY gs.game_date DESC
            ''', (username,))
            
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting user report: {e}")
            return []
        finally:
            conn.close()

# Global database manager instance
db_manager = DatabaseManager()
user_repo = UserRepository(db_manager)
game_repo = GameRepository(db_manager)
report_repo = ReportRepository(db_manager)