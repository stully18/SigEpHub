from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

SERVICE_HOURS_CSV_PATH = os.path.join(app.root_path, 'data', 'service_hours.csv')

userDB = {
    "shane": "012420",
    "ronan": "1234"
}

leaderboard_data = []

def load_leaderboard_from_csv():
    global leaderboard_data
    os.makedirs(os.path.dirname(SERVICE_HOURS_CSV_PATH), exist_ok=True)
    if os.path.exists(SERVICE_HOURS_CSV_PATH):
        try:
            df = pd.read_csv(SERVICE_HOURS_CSV_PATH)
            df.columns = df.columns.str.strip().str.lower()
            if 'name' in df.columns and 'hours' in df.columns:
                df_filtered = df[['name', 'hours']].copy()
                df_filtered['hours'] = pd.to_numeric(df_filtered['hours'], errors='coerce').fillna(0)
                df_sorted = df_filtered.sort_values(by='hours', ascending=False)
                leaderboard_data = df_sorted.to_dict(orient='records')
            elif 'brother' in df.columns and 'service_hours' in df.columns:
                df_filtered = df[['brother', 'service_hours']].rename(columns={'brother': 'name', 'service_hours': 'hours'}).copy()
                df_filtered['hours'] = pd.to_numeric(df_filtered['hours'], errors='coerce').fillna(0)
                df_sorted = df_filtered.sort_values(by='hours', ascending=False)
                leaderboard_data = df_sorted.to_dict(orient='records')
            else:
                leaderboard_data = []
        except Exception as e:
            leaderboard_data = []
    else:
        leaderboard_data = []

load_leaderboard_from_csv()

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    if user_id in userDB:
        return User(user_id)
    return None

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username:
            username = username.strip().lower() # Normalize username to lowercase
        if password:
            password = password.strip().lower() # Normalize password to lowercase (if your passwords are lowercase)

        if username in userDB and userDB[username] == password:
            user = User(username)
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    # The leaderboard_data is already loaded at startup and stored globally
    return render_template("dashboard.html", username=current_user.id, leaderboard=leaderboard_data)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Removed the /upload_service_hours route as it's no longer needed

@app.route('/files/<path:filename>')
@login_required
def serve_file(filename):
    # This route is for serving static files from the 'static/files' directory,
    # if you have PDF minutes, etc.
    try:
        return redirect(url_for('static', filename='files/' + filename))
    except Exception as e:
        flash(f"Error serving file: {e}", "danger")
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)