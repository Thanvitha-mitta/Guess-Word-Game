"""
Data models and validation functions for the Guess the Word Game
"""
import hashlib
import re
from config import Config

class UserValidator:
    """Handles user input validation"""
    
    @staticmethod
    def validate_username(username):
        """
        Validate username according to OpenText specifications:
        - At least 5 letters
        - Must contain both upper and lower case letters
        - Only alphabetic characters allowed
        """
        if not username or len(username) < Config.MIN_USERNAME_LENGTH:
            return False, f"Username must be at least {Config.MIN_USERNAME_LENGTH} characters long"
        
        if not username.isalpha():
            return False, "Username must contain only letters"
        
        has_upper = any(c.isupper() for c in username)
        has_lower = any(c.islower() for c in username)
        
        if not (has_upper and has_lower):
            return False, "Username must contain both upper and lower case letters"
        
        return True, "Valid username"
    
    @staticmethod
    def validate_password(password):
        """
        Validate password according to OpenText specifications:
        - At least 5 characters
        - Must contain alphabetic characters
        - Must contain numeric characters  
        - Must contain special characters ($, %, *, @)
        """
        if not password or len(password) < Config.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters long"
        
        has_alpha = any(c.isalpha() for c in password)
        has_numeric = any(c.isdigit() for c in password)
        has_special = any(c in Config.REQUIRED_SPECIAL_CHARS for c in password)
        
        if not has_alpha:
            return False, "Password must contain alphabetic characters"
        
        if not has_numeric:
            return False, "Password must contain numeric characters"
        
        if not has_special:
            return False, f"Password must contain special characters ({Config.REQUIRED_SPECIAL_CHARS})"
        
        return True, "Valid password"

class PasswordManager:
    """Handles password hashing and verification"""
    
    @staticmethod
    def hash_password(password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify password against hash"""
        return PasswordManager.hash_password(password) == password_hash

class GameLogic:
    """Handles game mechanics and word analysis"""
    
    @staticmethod
    def analyze_guess(guess, target_word):
        """
        Analyze a guess against the target word and return color coding:
        - 'correct': Letter is in correct position (Green)
        - 'wrong_position': Letter is in word but wrong position (Orange)  
        - 'not_in_word': Letter is not in the word (Grey)
        """
        guess = guess.upper()
        target_word = target_word.upper()
        result = []
        
        # Create copies to work with
        target_letters = list(target_word)
        guess_letters = list(guess)
        
        # First pass: mark correct positions (exact matches)
        for i in range(len(guess)):
            if guess_letters[i] == target_letters[i]:
                result.append({
                    'letter': guess_letters[i], 
                    'status': 'correct',
                    'position': i
                })
                # Remove matched letters to avoid double counting
                target_letters[i] = None
                guess_letters[i] = None
            else:
                result.append({
                    'letter': guess_letters[i], 
                    'status': 'unknown',
                    'position': i
                })
        
        # Second pass: check for wrong positions and not in word
        for i in range(len(result)):
            if result[i]['status'] == 'unknown':
                letter = guess_letters[i]
                if letter in target_letters:
                    result[i]['status'] = 'wrong_position'
                    # Remove the matched letter to avoid double counting
                    target_letters[target_letters.index(letter)] = None
                else:
                    result[i]['status'] = 'not_in_word'
        
        return result
    
    @staticmethod
    def validate_guess(guess):
        """Validate that a guess meets the game requirements"""
        if not guess:
            return False, "Guess cannot be empty"
        
        guess = guess.strip().upper()
        
        if len(guess) != Config.WORD_LENGTH:
            return False, f"Guess must be exactly {Config.WORD_LENGTH} letters"
        
        if not guess.isalpha():
            return False, "Guess must contain only letters"
        
        return True, guess

class User:
    """User model for handling user data"""
    
    def __init__(self, user_id, username, user_type='player'):
        self.id = user_id
        self.username = username
        self.user_type = user_type
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.user_type == 'admin'
    
    def is_player(self):
        """Check if user is a player"""
        return self.user_type == 'player'
    
    def __repr__(self):
        return f"<User {self.username} ({self.user_type})>"

class GameSession:
    """Game session model for tracking individual games"""
    
    def __init__(self, session_id, user_id, target_word, game_date):
        self.id = session_id
        self.user_id = user_id
        self.target_word = target_word
        self.game_date = game_date
        self.is_completed = False
        self.is_won = False
        self.guesses = []
    
    def add_guess(self, guess):
        """Add a guess to the game session"""
        self.guesses.append(guess)
    
    def is_game_over(self):
        """Check if the game is over (won or max guesses reached)"""
        return self.is_won or len(self.guesses) >= Config.MAX_GUESSES_PER_GAME
    
    def guesses_left(self):
        """Get number of guesses remaining"""
        return Config.MAX_GUESSES_PER_GAME - len(self.guesses)
    
    def __repr__(self):
        return f"<GameSession {self.id}: {self.target_word}>"