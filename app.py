import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required, error

# Configure the application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///chat-app.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    conversations = db.execute("SELECT * FROM conversations WHERE recipientid = (?)", session["user_id"])
    return (render_template("inbox.html", conversations=conversations))

@app.route("/history")
@login_required
def history():
    conversations = db.execute("SELECT * FROM conversations WHERE senderid = (?)", session["user_id"])
    return (render_template("history.html", conversations=conversations))

@app.route("/send", methods=["GET", "POST"])
@login_required
def send():
    if request.method == "POST":
        recipientusername = request.form.get("recipient")
        message = request.form.get("message")
        try:
            recipientid = db.execute("SELECT id FROM users WHERE username = (?)", recipientusername)[0]["id"]
        except IndexError:
            return error("Recipient does not exist.")
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        db.execute("INSERT INTO conversations(senderid, senderusername, recipientid, recipientusername, message, datetime) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], session["username"], recipientid, recipientusername, message, dt_string)
        return (render_template("sent.html"))
    else:
        return (render_template("send.html"))

@app.route("/delete", methods=["POST"])
@login_required
def delete():
    messageid = request.form.get("messageid")
    message = db.execute("SELECT * FROM conversations WHERE id = (?)", messageid)
    print(message[0]["recipientid"])
    print(message[0]["senderid"])
    print(session["user_id"])
    
    if (session["user_id"] == message[0]["recipientid"]):
        db.execute("DELETE FROM conversations WHERE id = (?)", messageid)
        return redirect("/")
    elif(session["user_id"] == message[0]["senderid"]):
        db.execute("DELETE FROM conversations WHERE id = (?)", messageid)
        return redirect("/history")
    else:
        return error("Cannot delete message that isn't yours")
    

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return error("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return error("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return error("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if db.execute("SELECT * FROM users WHERE username = (?)", request.form.get("username")):
            return error("username already taken")
        # Ensure username was submitted
        if not request.form.get("username") or not request.form.get("password"):
            return error("must provide username & password")
        if request.form.get("password") != request.form.get("confirmation"):
            return error("passwords must match")

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", request.form.get(
            "username"), generate_password_hash(request.form.get("password")))
        return redirect("/login")
    else:
        return render_template("register.html")

