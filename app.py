from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'data')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

admins = ["shane", "ronan"]

SERVICE_HOURS_CSV_FILENAME = 'service_hours.csv'
SERVICE_HOURS_CSV_PATH = os.path.join(app.root_path, 'data', SERVICE_HOURS_CSV_FILENAME)

userDB = {
    "shane": "012420",
    "ronan": "1234",
    "regularuser": "password"
}

leaderboard_data = []

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to load leaderboard data from CSV
# It now only returns (message, category) if there's an error or warning.
# For successful loads, it returns (None, None).
def load_leaderboard_from_csv():
    global leaderboard_data
    message = None
    category = None

    if os.path.exists(SERVICE_HOURS_CSV_PATH):
        try:
            df = pd.read_csv(SERVICE_HOURS_CSV_PATH)
            df.columns = df.columns.str.strip().str.lower()

            if 'name' in df.columns and 'hours' in df.columns:
                df_filtered = df[['name', 'hours']].copy()
            elif 'brother' in df.columns and 'service_hours' in df.columns:
                df_filtered = df[['brother', 'service_hours']].rename(columns={'brother': 'name', 'service_hours': 'hours'}).copy()
            else:
                leaderboard_data = []
                message = "CSV file loaded but missing expected columns ('name'/'hours' or 'brother'/'service_hours'). Leaderboard is empty."
                category = "warning"
                return message, category

            df_filtered['hours'] = pd.to_numeric(df_filtered['hours'], errors='coerce').fillna(0)
            df_sorted = df_filtered.sort_values(by='hours', ascending=False)
            leaderboard_data = df_sorted.to_dict(orient='records')
            # Successfully loaded, return None for message and category

        except pd.errors.EmptyDataError:
            leaderboard_data = []
            message = "Service hours CSV file is empty. Leaderboard is empty."
            category = "warning"
        except Exception as e:
            leaderboard_data = []
            message = f"Error loading service hours data: {e}. Leaderboard is empty."
            category = "danger"
    else:
        leaderboard_data = []
        message = "Service hours CSV file not found. Leaderboard is empty. Please upload one via Admin Dashboard."
        category = "info"
        print("Service hours CSV file not found on startup. Leaderboard is empty.") # Keep for debugging

    return message, category # Will be (None, None) on success

# Initial load during app startup.
# This does NOT flash messages directly.
initial_load_msg, initial_load_cat = load_leaderboard_from_csv()


# --- User Management (Flask-Login) ---
class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return str(self.id)

    def is_admin(self):
        return self.id.lower() in [admin.lower() for admin in admins]

@login_manager.user_loader
def load_user(user_id):
    if user_id in userDB:
        return User(user_id)
    return None

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    # Declare globals at the very beginning of the function if they are to be modified
    global initial_load_msg, initial_load_cat

    # If the user is already authenticated, redirect them
    if current_user.is_authenticated:
        # If there was an initial load message (warning/error/info) from startup,
        # flash it on the dashboard they're redirected to.
        # This ensures it doesn't show on the login page but *does* show up on the dashboard.
        if initial_load_msg:
            flash(initial_load_msg, initial_load_cat)
            initial_load_msg = None # Clear after flashing
            initial_load_cat = None

        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    # If this is the first time visiting login (GET request)
    # AND there's a startup message (warning/error/info) that hasn't been flashed yet,
    # we can decide whether to flash it on the login page.
    # For now, we are explicitly *not* flashing initial load success on the login page.
    # This block handles displaying *only* non-success messages on initial login page load.
    if request.method == "GET":
        if initial_load_msg: # If there's an error/warning/info message
            flash(initial_load_msg, initial_load_cat)
            initial_load_msg = None # Clear it after flashing
            initial_load_cat = None


    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username:
            username = username.strip().lower()
        if password:
            password = password.strip().lower()

        if username in userDB and userDB[username] == password:
            user = User(username)
            login_user(user)
            flash("Login successful!", "success")
            # Any initial load messages (error/warning/info) that were not success and not yet flashed
            # will be caught by the redirect to dashboard/admin_dashboard and flashed there.
            return redirect(url_for('dashboard')) # Redirect will handle admin check internally

        else:
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    return render_template("dashboard.html", username=current_user.id, leaderboard=leaderboard_data)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# --- Admin Dashboard Routes ---
@app.route("/admin_dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    # Declare globals at the very beginning of the function if they are to be modified
    global initial_load_msg, initial_load_cat

    if not current_user.is_admin():
        flash("You do not have administrative access.", "danger")
        return redirect(url_for('dashboard'))

    # Ensure any initial load messages (warning/error/info) that weren't flashed on login
    # or redirect are flashed here when an admin first accesses their dashboard.
    if initial_load_msg:
        flash(initial_load_msg, initial_load_cat)
        initial_load_msg = None
        initial_load_cat = None


    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("No selected file", "danger")
            return redirect(request.url)

        if not file.filename.lower().endswith('.csv'):
            flash("Invalid file type. Please upload a CSV file.", "danger")
            return redirect(request.url)

        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(SERVICE_HOURS_CSV_PATH)

            # Reload and get status from the new CSV
            message, category = load_leaderboard_from_csv()
            if message: # Only flash if there's a specific message (error/warning)
                flash(message, category)
            else: # If load_leaderboard_from_csv returned (None, None), it was a success
                flash("Service hours CSV uploaded and leaderboard updated successfully!", "success")

            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Error saving or processing file: {e}", "danger")
            return redirect(request.url)

    # For GET request, render the admin dashboard template
    return render_template("admin_dashboard.html", username=current_user.id, leaderboard=leaderboard_data)


@app.route('/files/<path:filename>')
@login_required
def serve_file(filename):
    try:
        return redirect(url_for('static', filename='files/' + filename))
    except Exception as e:
        flash(f"Error serving file: {e}", "danger")
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)