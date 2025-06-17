from flask import Flask, render_template, request, redirect, url_for, flash # Re-added flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os 

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

userDB = {"shane":"012420",
          "ronan": "1234"}

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

@app.route("/", methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    error_message = None

    if request.method == "POST":
        username = request.form.get("username")
        username = username.strip()  
        password = request.form.get("password")
        password = password.strip()

        if username in userDB and userDB[username] == password:
            user = User(username) 
            login_user(user) 
            flash("Login successful!", "success") 
            return redirect(url_for('dashboard')) 
        else:
            error_message = "Invalid username or password."
            flash("Login failed. Check your credentials.", "danger") 

    return render_template("login.html", error=error_message)

@app.route("/dashboard")
def dashboard():
        return  render_template("dashboard.html", username=current_user.id)

@app.route("/logout")
@login_required 
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)