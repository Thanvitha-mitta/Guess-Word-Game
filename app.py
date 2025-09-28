"""
Main Flask application for Guess the Word Game - OpenText Project
This file contains only the routes and Flask app configuration
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import date
from functools import wraps

# Import our custom modules
from config import Config
from models import UserValidator, GameLogic, User, GameSession
from database import user_repo, game_repo, report_repo

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# --- DECORATORS ---
def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- MAIN ROUTES ---
@app.route('/')
def index():
    """Home page - Welcome screen"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate username
        is_valid, message = UserValidator.validate_username(username)
        if not is_valid:
            flash(message, 'error')
            return render_template('register.html')
        
        # Validate password
        is_valid, message = UserValidator.validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('register.html')
        
        # Check password confirmation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Create user account
        success, result = user_repo.create_user(username, password)
        if success:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Registration failed: {result}', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Authenticate user
        success, user_data, message = user_repo.authenticate_user(username, password)
        
        if success:
            # Set session data
            session['user_id'] = user_data['id']
            session['username'] = user_data['username']
            session['user_type'] = user_data['user_type']
            
            flash(f'Welcome back, {user_data["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - different views for admin vs player"""
    if session.get('user_type') == 'admin':
        return render_template('admin_dashboard.html')
    else:
        # Get today's game count for player
        today = date.today()
        games_today = game_repo.get_daily_game_count(session['user_id'], today)
        can_play = games_today < Config.MAX_DAILY_GAMES
        
        return render_template('player_dashboard.html', 
                             games_today=games_today, 
                             can_play=can_play,
                             max_games=Config.MAX_DAILY_GAMES)

# --- GAME ROUTES ---
@app.route('/game')
@login_required
def game():
    """Start a new game - only for players"""
    if session.get('user_type') == 'admin':
        flash('Admins cannot play the game. Use admin functions instead.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if player can start a new game
    today = date.today()
    games_today = game_repo.get_daily_game_count(session['user_id'], today)
    
    if games_today >= Config.MAX_DAILY_GAMES:
        flash(f'Daily limit reached! You can play {Config.MAX_DAILY_GAMES} games per day.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get random word and create game session
    target_word = game_repo.get_random_word()
    if not target_word:
        flash('Error starting game. Please try again.', 'error')
        return redirect(url_for('dashboard'))
    
    session_id = game_repo.create_game_session(session['user_id'], target_word)
    if not session_id:
        flash('Error creating game session. Please try again.', 'error')
        return redirect(url_for('dashboard'))
    
    # Set up game session data
    session['current_game'] = session_id
    session['target_word'] = target_word
    session['guesses'] = []
    
    return render_template('game.html', 
                         max_guesses=Config.MAX_GUESSES_PER_GAME,
                         word_length=Config.WORD_LENGTH)

@app.route('/make_guess', methods=['POST'])
@login_required
def make_guess():
    """Process a player's guess - AJAX endpoint"""
    # Validate active game session
    if 'current_game' not in session:
        return jsonify({'error': 'No active game session'})
    
    # Get and validate the guess
    guess = request.json.get('guess', '').strip()
    is_valid, processed_guess = GameLogic.validate_guess(guess)
    
    if not is_valid:
        return jsonify({'error': processed_guess})  # processed_guess contains error message
    
    # Check guess limit
    current_guesses = session.get('guesses', [])
    if len(current_guesses) >= Config.MAX_GUESSES_PER_GAME:
        return jsonify({'error': 'Maximum guesses reached'})
    
    # Analyze the guess
    target_word = session['target_word']
    guess_result = GameLogic.analyze_guess(processed_guess, target_word)
    
    # Update session data
    current_guesses.append(guess_result)
    session['guesses'] = current_guesses
    
    # Save guess to database
    game_repo.save_guess(session['current_game'], processed_guess, len(current_guesses))
    
    # Check if game is completed
    is_won = processed_guess == target_word.upper()
    is_completed = is_won or len(current_guesses) >= Config.MAX_GUESSES_PER_GAME
    
    if is_completed:
        game_repo.complete_game_session(session['current_game'], is_won)
    
    # Return game state
    return jsonify({
        'result': guess_result,
        'is_won': is_won,
        'is_completed': is_completed,
        'guesses_left': Config.MAX_GUESSES_PER_GAME - len(current_guesses),
        'target_word': target_word if is_completed else None,
        'total_guesses': len(current_guesses)
    })

# --- ADMIN ROUTES ---
@app.route('/admin/daily_report')
@login_required
@admin_required
def daily_report():
    """Admin daily report page"""
    report_date = request.args.get('date', str(date.today()))
    
    # Get daily statistics
    stats = report_repo.get_daily_report(report_date)
    
    return render_template('daily_report.html', 
                         stats=stats, 
                         report_date=report_date)

@app.route('/admin/user_report')
@login_required
@admin_required
def user_report():
    """Admin user report page"""
    selected_username = request.args.get('username', '')
    
    # Get user-specific data if username is provided
    user_data = []
    if selected_username:
        user_data = report_repo.get_user_report(selected_username)
    
    # Get all player usernames for dropdown
    all_users = user_repo.get_all_players()
    
    return render_template('user_report.html', 
                         user_data=user_data, 
                         selected_username=selected_username,
                         all_users=all_users)

# --- ERROR HANDLERS ---
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

# --- UTILITY FUNCTIONS ---
@app.context_processor
def inject_config():
    """Make config variables available in templates"""
    return {
        'config': {
            'MAX_DAILY_GAMES': Config.MAX_DAILY_GAMES,
            'MAX_GUESSES_PER_GAME': Config.MAX_GUESSES_PER_GAME,
            'WORD_LENGTH': Config.WORD_LENGTH
        }
    }

if __name__ == '__main__':
    print("🎯 Guess the Word Game - OpenText Project")
    print("=" * 50)
    print("✅ Modular structure loaded")
    print("✅ Database initialized")
    print("✅ User authentication system ready")
    print("✅ Game logic loaded")
    print("✅ Admin reporting ready")
    print(f"✅ Default admin: {Config.DEFAULT_ADMIN_USERNAME} / {Config.DEFAULT_ADMIN_PASSWORD}")
    print("🚀 Starting Flask development server...")
    print("📱 Access the game at: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True)