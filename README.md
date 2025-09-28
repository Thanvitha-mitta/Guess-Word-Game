
---

````markdown
# Guess the Word Game 🎮

A Flask-based word guessing game with two user roles: **Admin** and **Player**.  
Players can guess words within a daily limit, and admins can view reports on game activity.

---

## 🚀 Features
- User registration and login (with validation).
- Two roles:
  - **Admin** → can view daily reports & user reports.
  - **Player** → can play up to 3 games per day with max 5 guesses per game.
- Game flow:
  - Random 5-letter word is assigned.
  - Player has limited guesses.
  - Correct letters (right place) → **green**, correct letters (wrong place) → **orange**, incorrect letters → **grey**.
  - Win/Loss is tracked.
- Reports:
  - **Daily Report**: number of users & correct guesses.
  - **User Report**: date, number of words tried & correct guesses.
- Error handling with custom error pages.

---

## 🛠️ Tech Stack
- **Backend**: Python, Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Version Control**: Git + GitHub

---

## ⚙️ Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR-USERNAME/guess-the-word.git
   cd guess-the-word

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:

   ```bash
   python app.py
   ```


---


````

