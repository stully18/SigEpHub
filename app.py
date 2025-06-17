from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
# IMPORTANT: Change this secret key to a strong, unique, and randomly generated value in a real application!
# For production, use environment variables (e.g., os.environ.get('SECRET_KEY'))
app.config['SECRET_KEY'] = os.urandom(24) # Generates a random 24-byte key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # This tells Flask-Login which view function handles logins

# Your dummy user database
userDB = {
    "shane": "012420",
    "ronan": "1234"
}

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        # Flask-Login requires this to return a string
        return str(self.id)

# User loader callback: used by Flask-Login to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    if user_id in userDB:
        return User(user_id)
    return None

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"]) # Also make /login accessible
def login():
    # If the user is already logged in, redirect them to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    # If the request method is POST (i.e., form submission)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Basic input cleaning
        if username:
            username = username.strip()
        if password:
            password = password.strip()

        # Check credentials
        if username in userDB and userDB[username] == password:
            user = User(username)
            login_user(user) # Log the user in (Flask-Login handles session)
            flash("Login successful!", "success") # Flash a success message
            return redirect(url_for('dashboard')) # Redirect to dashboard after successful login
        else:
            flash("Invalid username or password.", "danger") # Flash an error message
            # If login fails, render the login page again (no redirect needed here as it's the same page)
            return render_template("login.html") 

    # For GET requests, just render the login page
    return render_template("login.html")

@app.route("/dashboard")
@login_required # Protect this route: only accessible if user is logged in
def dashboard():
    # current_user is provided by Flask-Login when a user is logged in
    return render_template("dashboard.html", username=current_user.id)

@app.route("/logout")
@login_required # Ensure only logged-in users can logout
def logout():
    logout_user() # Log the user out (Flask-Login handles session clearing)
    flash("You have been logged out.", "info") # Flash an info message
    return redirect(url_for('login')) # Redirect to the login page after logout

# Example route for serving files (if you have one and want to serve them securely)
# You might need to create a 'files' directory inside your 'static' folder
# For example, static/files/minutes/2024-05-15_Chapter_Meeting.pdf
@app.route('/files/<path:filename>')
@login_required # Ensure files are only accessible to logged-in users
def serve_file(filename):
    # This is a basic example. For production, consider using Nginx/Apache for static files
    # or a more robust file serving solution.
    # The 'directory' argument should point to the base directory of your files.
    # Make sure your files are within the 'static' folder or configure Flask to serve from another location.
    # If your files are directly in static/, use 'static' as the directory.
    # If they are in static/files/, use os.path.join(app.root_path, 'static', 'files')
    try:
        # Assuming your files are in a 'files' subfolder within 'static'
        # e.g., static/files/minutes/myfile.pdf
        return redirect(url_for('static', filename='files/' + filename))
    except Exception as e:
        flash(f"Error serving file: {e}", "danger")
        return redirect(url_for('dashboard')) # Or render an error page

if __name__ == '__main__':
    app.run(debug=True)