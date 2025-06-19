from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'data') # Define upload folder

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

admins = ["shane"]

SERVICE_HOURS_CSV_PATH = os.path.join(app.root_path, 'data', 'service_hours.csv')

userDB = {
    "shane": "012420",
    "ronan": "1234",
    "regularuser": "password" # Example regular user
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
                flash("CSV file loaded but missing 'name'/'hours' or 'brother'/'service_hours' columns.", "warning")
        except pd.errors.EmptyDataError:
            leaderboard_data = []
            flash("Service hours CSV file is empty.", "warning")
        except Exception as e:
            leaderboard_data = []
            flash(f"Error loading service hours data: {e}", "danger")
    else:
        leaderboard_data = []
        flash("Service hours CSV file not found. Please upload one.", "info")


load_leaderboard_from_csv()

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return str(self.id)

    def is_admin(self):
        # Normalize the username for comparison
        return self.id.lower() in [admin.lower() for admin in admins]

@login_manager.user_loader
def load_user(user_id):
    if user_id in userDB:
        return User(user_id)
    return None

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        # If already authenticated, redirect based on admin status
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
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
            # Redirect based on admin status immediately after login
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    # If an admin tries to access the regular dashboard, redirect them
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
    if not current_user.is_admin():
        flash("You do not have administrative access.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("No selected file", "danger")
            return redirect(request.url)
        if file and file.filename.endswith('.csv'):
            filename = secure_filename('service_hours.csv') # Force filename to be consistent
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(file_path)
                load_leaderboard_from_csv() # Reload data after successful upload
                flash("Service hours CSV uploaded and leaderboard updated successfully!", "success")
                return redirect(url_for('admin_dashboard'))
            except Exception as e:
                flash(f"Error saving or processing file: {e}", "danger")
                return redirect(request.url)
        else:
            flash("Invalid file type. Please upload a CSV file.", "danger")
            return redirect(request.url)

    return render_template("admin_dashboard.html", username=current_user.id)


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