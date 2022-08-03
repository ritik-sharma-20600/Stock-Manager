import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


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
    rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
    while True:
        try:
            rows2 = db.execute("SELECT * FROM stocks WHERE username=?", rows[0]["username"])
            break
        except IndexError:
            session.clear()
            return redirect("/")
    y=0
    finlist=[]
    for row in rows2:
        sym = row["symbol"]
        symd = lookup(sym)
        shares = row["shares"]
        x = symd["price"]*float(shares)
        round(x, 2)
        y = y + symd["price"]*float(shares)
        newdic = {
            "symbol":symd["symbol"],
            "name":symd["name"],
            "price":usd(symd["price"]),
            "shares":shares,
            "total":usd(x),
        }
        finlist.append(newdic)
    gtotal=float(y)+float(rows[0]["cash"])
    return render_template("index.html", symbols=finlist, cash=usd(rows[0]["cash"]), gtotal=usd(gtotal))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")
    else:
        sym = request.form.get("symbol")
        if not sym:
            return apology("Enter a symbol!")
        if lookup(sym) is None:
            return apology("Enter a valid symbol!")
        shares = request.form.get("shares")
        if not shares:
            return apology("Enter the number of shares to buy!")
        if not shares.isdigit():
            return apology("Invalid Shares!")
        if int(shares) < 0:
            return apology("Invalid Shares!")
        symbol = lookup(sym)
        rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
        cash = rows[0]["cash"]
        payment=symbol["price"]*float(shares)
        if cash < (payment):
            return apology("Insufficient Funds")
        cash = cash-payment
        db.execute("UPDATE users SET cash=? WHERE id=?", cash, session["user_id"])
        db.execute("INSERT INTO transactions (username, symbol, shares, time) VALUES (?, ?, ?, datetime('now'))", rows[0]["username"], symbol["symbol"], shares)
        rows2 = db.execute("SELECT * FROM stocks WHERE username=? AND symbol=?", rows[0]["username"], symbol["symbol"])
        if len(rows2) < 1:
            db.execute("INSERT INTO stocks(username, symbol, shares) VALUES(?, ?, ?)", rows[0]["username"], symbol["symbol"], shares)
        else:
            tmp=int(rows2[0]["shares"])+int(shares)
            db.execute("UPDATE stocks SET shares=? WHERE username=? AND symbol=?", tmp, rows[0]["username"], symbol["symbol"])
        return redirect("/")

@app.route("/history")
@login_required
def history():
    rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
    rows2 = db.execute("SELECT * FROM transactions WHERE username=?", rows[0]["username"])
    finlist=[]
    for row in rows2:
        sym = row["symbol"]
        symd = lookup(sym)
        shares = row["shares"]
        newdic = {
            "symbol":symd["symbol"],
            "shares":shares,
            "price":usd(symd["price"]),
            "transacted":row["time"]
        }
        finlist.append(newdic)
    finlist.reverse()
    return render_template("history.html", transactions=finlist)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
        return render_template("quote.html")
    else:
        sym = request.form.get("symbol")
        if not sym:
            return apology("Enter a symbol")
        if lookup(sym) is None:
             return apology("Not a valid symbol!")
        else:
            ans = lookup(sym)
            # return apology(ans["name"])
            priceusd = usd(ans["price"])
            return render_template("quoted.html", name=ans["name"], symbol=ans["symbol"], price=priceusd)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        user = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username=?", user)
        if not user:
            return apology("Enter a username!")
        if len(rows) != 0:
            return apology("Username already taken!")
        if not request.form.get("password"):
            return apology("Enter a password!")
        if not request.form.get("confirmation"):
            return apology("Confirm the password!")
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match!")
        pass_hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", user, pass_hash)
    return redirect("/login")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
    rows2 = db.execute("SELECT * FROM stocks WHERE username=?", rows[0]["username"])
    sharenum = db.execute("SELECT * FROM stocks WHERE username=? AND symbol=?", rows[0]["username"], request.form.get("symbol"))
    if request.method == "GET":
        return render_template("sell.html", rows=rows2)
    else:
        shares=request.form.get("shares")
        if int(shares) > int(sharenum[0]["shares"]):
            return apology("Insufficient Stocks!")
        else:
            symbol = lookup(request.form.get("symbol"))
            cash = rows[0]["cash"]
            payment=symbol["price"]*float(shares)
            cash = cash+payment
            db.execute("UPDATE users SET cash=? WHERE id=?", cash, session["user_id"])
            db.execute("INSERT INTO transactions (username, symbol, shares, time) VALUES (?, ?, ?, datetime('now'))", rows[0]["username"], symbol["symbol"], -int(shares))
            tmp=int(sharenum[0]["shares"])-int(shares)
            if tmp < 1:
                db.execute("DELETE FROM stocks WHERE username=? AND symbol=?", rows[0]["username"], request.form.get("symbol"))
            else:
                db.execute("UPDATE stocks SET shares=? WHERE username=? AND symbol=?", tmp, rows[0]["username"], symbol["symbol"])
            return redirect("/")

@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    if request.method == "GET":
        return render_template("addcash.html")
    else:
        rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
        cash = float(rows[0]["cash"])
        newcash = float(request.form.get("newcash"))
        cash = cash+newcash
        db.execute("UPDATE users SET cash=? WHERE id=?", cash, session["user_id"])
        return redirect("/")
