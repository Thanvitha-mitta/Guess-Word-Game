"""
Configuration settings for the Guess the Word Game
"""
import os

class Config:
    """Base configuration class"""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'opentext_guess_game_2025'
    
    # Database Settings
    DATABASE_PATH = 'instance/guess_game.db'
    
    # Game Settings
    MAX_DAILY_GAMES = 3
    MAX_GUESSES_PER_GAME = 5
    WORD_LENGTH = 5
    
    # Initial words for the game (20 five-letter words)
    INITIAL_WORDS = [
        'APPLE', 'BRAVE', 'CHARM', 'DANCE', 'EAGLE',
        'FAITH', 'GRACE', 'HEART', 'IMAGE', 'JOLLY',
        'KNEEL', 'LIGHT', 'MAGIC', 'NOBLE', 'OCEAN',
        'PEACE', 'QUEEN', 'RADIO', 'STORM', 'TRUTH'
    ]
    
    # Admin User Credentials
    DEFAULT_ADMIN_USERNAME = 'Admin'
    DEFAULT_ADMIN_PASSWORD = 'Admin@123'
    
    # Validation Rules
    MIN_USERNAME_LENGTH = 5
    MIN_PASSWORD_LENGTH = 5
    REQUIRED_SPECIAL_CHARS = '$%*@'