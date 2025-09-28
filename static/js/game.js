/**
 * Guess the Word Game - Enhanced JavaScript
 * Handles game interactions and animations
 */

class WordGameController {
    constructor() {
        this.guesses = [];
        this.gameOver = false;
        this.maxGuesses = 5;
        this.wordLength = 5;
        this.currentRow = 0;
        
        this.initializeGame();
        this.setupEventListeners();
    }
    
    initializeGame() {
        this.createGameBoard();
        this.focusInput();
        this.updateGameInfo();
    }
    
    createGameBoard() {
        const board = document.getElementById('game-board');
        if (!board) return;
        
        board.innerHTML = '';
        
        for (let row = 0; row < this.maxGuesses; row++) {
            const rowElement = document.createElement('div');
            rowElement.className = 'guess-row';
            rowElement.id = `row-${row}`;
            
            for (let col = 0; col < this.wordLength; col++) {
                const letterBox = document.createElement('div');
                letterBox.className = 'letter-box';
                letterBox.id = `box-${row}-${col}`;
                letterBox.setAttribute('data-row', row);
                letterBox.setAttribute('data-col', col);
                
                rowElement.appendChild(letterBox);
            }
            
            board.appendChild(rowElement);
        }
    }
    
    setupEventListeners() {
        const guessInput = document.getElementById('guess-input');
        const submitButton = document.getElementById('submit-guess');
        
        if (guessInput) {
            // Auto-uppercase and limit input
            guessInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.toUpperCase().replace(/[^A-Z]/g, '');
                if (e.target.value.length > this.wordLength) {
                    e.target.value = e.target.value.substring(0, this.wordLength);
                }
            });
            
            // Submit on Enter key
            guessInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !this.gameOver) {
                    this.makeGuess();
                }
            });
        }
        
        if (submitButton) {
            submitButton.addEventListener('click', () => {
                if (!this.gameOver) {
                    this.makeGuess();
                }
            });
        }
    }
    
    async makeGuess() {
        if (this.gameOver) return;
        
        const guessInput = document.getElementById('guess-input');
        const guess = guessInput.value.trim();
        
        // Validate input
        if (!this.validateGuess(guess)) return;
        
        // Disable input during processing
        this.setInputEnabled(false);
        this.showLoading(true);
        
        try {
            const response = await fetch('/make_guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ guess: guess })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                this.setInputEnabled(true);
                return;
            }
            
            // Process successful guess
            await this.processGuessResult(data);
            
        } catch (error) {
            console.error('Error making guess:', error);
            this.showError('Network error. Please try again.');
            this.setInputEnabled(true);
        } finally {
            this.showLoading(false);
        }
    }
    
    validateGuess(guess) {
        if (!guess) {
            this.showError('Please enter a guess');
            return false;
        }
        
        if (guess.length !== this.wordLength) {
            this.showError(`Please enter exactly ${this.wordLength} letters`);
            return false;
        }
        
        if (!/^[A-Z]+$/.test(guess)) {
            this.showError('Please enter only letters');
            return false;
        }
        
        return true;
    }
    
    async processGuessResult(data) {
        // Display the guess with animation
        await this.displayGuessWithAnimation(data.result, this.currentRow);
        
        this.guesses.push(data.result);
        this.currentRow++;
        
        // Update game info
        this.updateGameInfo(data.guesses_left);
        
        // Clear input
        const guessInput = document.getElementById('guess-input');
        if (guessInput) {
            guessInput.value = '';
        }
        
        if (data.is_completed) {
            this.endGame(data.is_won, data.target_word);
        } else {
            this.setInputEnabled(true);
            this.focusInput();
        }
    }
    
    async displayGuessWithAnimation(result, rowIndex) {
        const animationDelay = 150; // ms between each letter animation
        
        for (let i = 0; i < result.length; i++) {
            const box = document.getElementById(`box-${rowIndex}-${i}`);
            const letter = result[i];
            
            // Add letter with initial animation
            setTimeout(() => {
                box.textContent = letter.letter;
                box.classList.add('animate');
                
                // Add color class after a short delay for dramatic effect
                setTimeout(() => {
                    box.classList.remove('animate');
                    box.classList.add(this.getStatusClass(letter.status));
                }, 100);
            }, i * animationDelay);
        }
        
        // Wait for all animations to complete
        await new Promise(resolve => {
            setTimeout(resolve, result.length * animationDelay + 200);
        });
    }
    
    getStatusClass(status) {
        switch (status) {
            case 'correct': return 'correct';
            case 'wrong_position': return 'wrong-position';
            case 'not_in_word': return 'not-in-word';
            default: return '';
        }
    }
    
    endGame(isWon, targetWord) {
        this.gameOver = true;
        this.setInputEnabled(false);
        
        const resultDiv = document.getElementById('game-result');
        if (!resultDiv) return;
        
        resultDiv.style.display = 'block';
        resultDiv.className = `game-result ${isWon ? 'success' : 'failure'}`;
        
        if (isWon) {
            resultDiv.innerHTML = `
                <h3>🎉 Congratulations!</h3>
                <p>You guessed the word: <strong>${targetWord}</strong></p>
                <p>You solved it in ${this.currentRow} ${this.currentRow === 1 ? 'guess' : 'guesses'}!</p>
                <button onclick="location.href='/dashboard'" class="btn btn-large">Back to Dashboard</button>
                <button onclick="location.href='/game'" class="btn btn-secondary btn-large" style="margin-left: 10px;">Play Again</button>
            `;
        } else {
            resultDiv.innerHTML = `
                <h3>😔 Better luck next time!</h3>
                <p>The word was: <strong>${targetWord}</strong></p>
                <p>Don't give up - you can do better next time!</p>
                <button onclick="location.href='/dashboard'" class="btn btn-large">Back to Dashboard</button>
                <button onclick="location.href='/game'" class="btn btn-secondary btn-large" style="margin-left: 10px;">Try Again</button>
            `;
        }
        
        // Hide input section
        const inputSection = document.getElementById('input-section');
        if (inputSection) {
            inputSection.style.display = 'none';
        }
    }
    
    updateGameInfo(guessesLeft = null) {
        const gameInfoElement = document.getElementById('guesses-left');
        if (gameInfoElement) {
            const remaining = guessesLeft !== null ? guessesLeft : (this.maxGuesses - this.currentRow);
            gameInfoElement.textContent = `Guesses left: ${remaining}`;
        }
    }
    
    setInputEnabled(enabled) {
        const guessInput = document.getElementById('guess-input');
        const submitButton = document.getElementById('submit-guess');
        
        if (guessInput) {
            guessInput.disabled = !enabled;
        }
        
        if (submitButton) {
            submitButton.disabled = !enabled;
            submitButton.textContent = enabled ? 'Submit Guess' : 'Processing...';
        }
    }
    
    showLoading(show) {
        const submitButton = document.getElementById('submit-guess');
        if (submitButton) {
            if (show) {
                submitButton.innerHTML = '🔄 Processing...';
                submitButton.classList.add('loading');
            } else {
                submitButton.innerHTML = 'Submit Guess';
                submitButton.classList.remove('loading');
            }
        }
    }
    
    showError(message) {
        // Create or update error display
        let errorDiv = document.getElementById('game-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'game-error';
            errorDiv.className = 'flash-message flash-error';
            errorDiv.style.marginTop = '20px';
            
            const inputSection = document.getElementById('input-section');
            if (inputSection && inputSection.parentNode) {
                inputSection.parentNode.insertBefore(errorDiv, inputSection.nextSibling);
            }
        }
        
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Auto-hide error after 3 seconds
        setTimeout(() => {
            if (errorDiv) {
                errorDiv.style.display = 'none';
            }
        }, 3000);
    }
    
    focusInput() {
        const guessInput = document.getElementById('guess-input');
        if (guessInput && !this.gameOver) {
            guessInput.focus();
        }
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing game...');
    window.gameController = new WordGameController();
});

// Also provide a fallback function for the old method
function makeGuess() {
    if (window.gameController) {
        window.gameController.makeGuess();
    }
}