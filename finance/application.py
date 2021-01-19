import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    # updating rows in owned table with current stock price
    rows = db.execute("SELECT * FROM owned WHERE user_id=?", session["user_id"])
    for row in rows:
        quote = lookup(row["symbol"])
        price = float(quote["price"])
        total = int(row["shares"]) * price
        db.execute("UPDATE owned SET price=?, total=? WHERE user_id=? AND symbol=?", price, total, session["user_id"], row["symbol"])

    # reading values and dictionary(table) in order to send to index.html
    owned = db.execute("SELECT * FROM owned WHERE user_id=?", session["user_id"])
    read = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
    cash = float(read[0]["cash"])               # reading the value of cash from read dictionary

    reader = db.execute("SELECT SUM(total) FROM owned WHERE user_id=?", session["user_id"])
    SUM = float(reader[0]['SUM(total)']) + float(cash)
    return render_template("index.html", owned=owned, cash=usd(cash), SUM=usd(SUM))



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via GET (as by clicking on Buy)
    if request.method == "GET":
        return render_template("buy.html")

    # User reached route via POST (as by submitting a form via POST)
    else:
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if not symbol or not shares:
            return apology("Enter both symbol and shares number", 403)
        elif shares < 0:
            return apology("Enter positive number", 403)

        quote = lookup(symbol)
        # checking if lookup returns a value. The lookup returns a dictionary.
        if quote == None:
            return apology("The provided stock ticker is not valid.", 403)


        price = quote["price"]
        name = quote["name"]
        symbol = quote["symbol"]

        # check if enough cash is available for transaction
        total_cost = float(price) * int(shares)
        users = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])
        cash = float(users[0]['cash'])
        if cash < total_cost:
            return apology("No enough cash for this transaction.", 403)
        else:
            # updating cash in the users table
            remaining_cash = cash - total_cost
            db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash=remaining_cash, user_id=session["user_id"])

            # inserting the new transaction into transactions table
            db.execute("INSERT INTO transactions VALUES(:user_id, :status, :symbol, :name, :shares, :price, datetime('now'))", user_id=session["user_id"], status="buy", symbol=symbol, name=name, shares=int(shares), price=float(price))

            # inserting and updating total number of shares in owned table
            rows = db.execute("SELECT * from owned WHERE user_id=? AND symbol=?", session["user_id"], symbol)

            if len(rows) != 1:
                db.execute("INSERT INTO owned VALUES(?,?,?,?,?,?)", session["user_id"], symbol, name, int(shares), float(price), int(shares) * float(price))
            else:
                cur_shares = int(rows[0]["shares"])
                shares = shares + cur_shares
                db.execute("UPDATE owned SET shares=?, total=? WHERE user_id=? and symbol=?", shares, shares * float(price), session["user_id"], symbol)

            flash("Bought!", "success")
            # Redirect user to home page
            return redirect("/")


@app.route("/history")
@login_required
def history():

    transactions = db.execute("SELECT * FROM transactions WHERE user_id=?", session["user_id"])
    return render_template("history.html", transactions=transactions)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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
    """Get stock quote."""
    # User reached route via GET (redirected from login)
    if request.method == "GET":
        return render_template("quote.html")

    # User reached route via POST (from entering a symbol)
    else:
        symbol = request.form.get("symbol")
        quote = lookup(symbol)

        # checking if lookup returns a value. The lookup returns a dictionary.
        if quote == None:
            return apology("The provided stock ticker is not valid.", 403)
        else:
            company = quote["name"]
            price = quote["price"]
            symbol = quote["symbol"]

            # sending these values to a the quoted page for display
            return render_template("quoted.html", company = company, symbol = symbol, price = usd(price))




@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via GET (redirected from login)
    if request.method == "GET":
        return render_template("register.html")

    else:
        # assigning entered values to variables
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Ensure password was entered again
        elif not confirmation:
            return apology("must retype password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists
        if len(rows) == 1:
            return apology("This username is already taken", 403)

        # Ensure both passwords are the same
        elif password != confirmation:
            return apology("Your passwords do not match", 403)

        else:
            # hashing the password to save in the db
            hashed = generate_password_hash(password)

            # insert the username, password and hash in the db
            db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, hashed)

            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = :username",
                              username=request.form.get("username"))

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            flash("Registered!", "success")
            # Redirect user to home page
            return redirect("/")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    # User reached route via GET (redirected from login)
    if request.method == "GET":
        rows = db.execute("SELECT symbol FROM owned WHERE user_id=?", session["user_id"])
        return render_template("sell.html", rows=rows)

    else:
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        if shares < 0:
            return apology("Enter a positive number", 403)

        owned = db.execute("SELECT shares FROM owned WHERE user_id=? and symbol=?", session["user_id"], symbol)
        if shares > int(owned[0]["shares"]):
            return apology ("You have less shares.", 403)

        else:
            quote = lookup(symbol)
            price = quote["price"]
            name = quote["name"]
            symbol = quote["symbol"]

            # updating transactions table
            db.execute("INSERT INTO transactions VALUES(?,?,?,?,?,?, datetime('now'))", session["user_id"], "sell", symbol, name, -1*(shares), float(price))

            # updating users table
            read = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])
            new_cash = shares * price + float(read[0]["cash"])
            db.execute("UPDATE users SET cash=? WHERE id=?", new_cash, session["user_id"])

            # updating owned table
            read = db.execute("SELECT shares from owned WHERE user_id=? AND symbol=?", session["user_id"], symbol)
            new_shares = int(read[0]["shares"]) - shares
            if new_shares == 0:
                # deleting symbol from owned if no shares left
                db.execute("DELETE FROM owned WHERE user_id=? AND symbol=?", session["user_id"], symbol)
            else:
                db.execute("UPDATE owned SET shares=? , price=?, total=? WHERE user_id=? AND symbol=?", new_shares, float(price), float(new_shares * price), session["user_id"], symbol)

            flash("Sold!", "success")
            # Redirect user to home page
            return redirect("/")




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
