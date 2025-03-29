import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

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
db = SQL("sqlite:///services.db")


@app.route("/")
def index():
    """Show homepage of the services"""

    # Reveal homepage after login
    try:

        # Keep track of the user
        user = session["user_id"]

        # Query database for user type
        row = db.execute("SELECT * FROM users WHERE id = ?", user)
        group = row[0]["type"]
        balance = row[0]["balance"]

        # Query database for user services
        rows1 = db.execute("SELECT * FROM services WHERE provider = ? AND service = ? ORDER BY id", user, "Accommodation")
        rows2 = db.execute("SELECT * FROM services WHERE provider = ? AND service = ? ORDER BY id", user, "Consultancy")
        rows3 = db.execute("SELECT * FROM services WHERE provider = ? AND service = ? ORDER BY id", user, "Transportation")
        rows4 = db.execute("SELECT * FROM services WHERE customer = ? ORDER BY id", user)

        # Pass parameters into template
        return render_template("index.html", group=group, balance=balance, usd=usd, rows1=rows1, rows2=rows2, rows3=rows3, rows4=rows4)

    # Reveal homepage before login
    except:
        return render_template("index.html")


@app.route("/accommodation")
def accommodation():
    """Accommodation Section"""

    # Assign service type
    service = "Accommodation"

    # Query database for accommodation
    rows = db.execute("SELECT * FROM services WHERE service = ? ORDER BY id", service)

    # Show full list of accommodation
    return render_template("accommodation.html", rows=rows, usd=usd)


@app.route("/consultancy")
def consultancy():
    """Consultancy Section"""

    # Assign service type
    service = "Consultancy"

    # Query database for consultancy
    rows = db.execute("SELECT * FROM services WHERE service = ? ORDER BY id", service)

    # Show full list of consultancy
    return render_template("consultancy.html", rows=rows, usd=usd)


@app.route("/transportation")
def transportation():
    """Transportation Section"""

    # Assign service type
    service = "Transportation"

    # Query database for transportation
    rows = db.execute("SELECT * FROM services WHERE service = ? ORDER BY id", service)

    # Show full list of transportation
    return render_template("transportation.html", rows=rows, usd=usd)


@app.route("/payment",  methods=["GET", "POST"])
@login_required
def payment():
    """Payment Section"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user balance
    balance = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["balance"]

    # User reached route via POST
    if request.method == "POST":

        # Get input from transaction form
        transaction = request.form.get("transaction")
        entity = request.form.get("entity")
        amount = int(request.form.get("amount"))
        xid = request.form.get("xid")
        status = "Pending"

        # Receive transaction request
        if transaction == "Receive":

            # Query database for unique entity
            rows = db.execute("SELECT * FROM users WHERE email = ?", entity)

            # Ensure email exists
            if len(rows) != 1:
                return apology("Invalid sender email address!", 400)

            # After checking existing email
            else:

                # Insert rows into database
                db.execute("INSERT INTO payment (user, entity, amount, type, xid, status) VALUES(?, ?, ?, ?, ?, ?)",
                           user, entity, amount, transaction, xid, status)

                # Redirect to transactions route
                flash("Request is pending!")
                return redirect("/transactions")

        # Send transaction request
        elif transaction == "Send":

            # Apology for insufficient balance
            if balance < amount:
                return apology("Insufficient balance to send!", 400)

            # Query database for unique entity
            rows = db.execute("SELECT * FROM users WHERE email = ?", entity)

            # Ensure email exists
            if len(rows) != 1:
                return apology("Invalid receiver email address!", 400)

            # After checking existing email
            else:

                # Insert rows into database
                db.execute("INSERT INTO payment (user, entity, amount, type, xid, status) VALUES(?, ?, ?, ?, ?, ?)",
                           user, entity, amount, transaction, xid, status)

                # Update balance into database
                db.execute("UPDATE users SET balance = ? WHERE id = ?", balance - amount, user)

                # Redirect to transactions route
                flash("Request is pending!")
                return redirect("/transactions")

        # Deposit transaction request
        elif transaction == "Deposit":

            # Ensure valid admin bank account
            if entity == "01721712318":

                # Insert rows into database
                db.execute("INSERT INTO payment (user, entity, amount, type, xid, status) VALUES(?, ?, ?, ?, ?, ?)",
                           user, entity, amount, transaction, xid, status)

                # Redirect to transactions route
                flash("Request is pending!")
                return redirect("/transactions")

            # Apology for invalid admin bank account
            else:
                return apology("Invalid admin bank account!", 400)

        # Withdraw transaction request
        elif transaction == "Withdraw":

            # Apology for insufficient balance
            if balance < amount:
                return apology("Insufficient balance to withdraw!", 400)

            # Ensure valid user bank account
            if len(entity) == 11 and entity != "01721712318":

                # Insert rows into database
                db.execute("INSERT INTO payment (user, entity, amount, type, xid, status) VALUES(?, ?, ?, ?, ?, ?)",
                           user, entity, amount, transaction, xid, status)

                # Update balance into database
                db.execute("UPDATE users SET balance = ? WHERE id = ?", balance - amount, user)

                # Redirect to transactions route
                flash("Request is pending!")
                return redirect("/transactions")

            # Apology for invalid user bank account
            else:
                return apology("Invalid user bank account!")

        # Apology for invalid transaction request
        else:
            return apology("Invalid transaction!", 400)

    # User reached route via GET
    else:
        return render_template("payment.html", balance=balance, usd=usd)


@app.route("/transactions")
@login_required
def transactions():
    """Transactions History"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user email
    email = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["email"]

    # Query database for payment history
    transactions = db.execute("SELECT * FROM payment WHERE user = ? OR entity = ? ORDER BY id", user, email)

    # Query database for user email list
    users = db.execute("SELECT * FROM users")

    # Show user full transactions history
    return render_template("transactions.html", transactions=transactions, usd=usd, email=email, users=users)


@app.route("/receive-<transaction_id>", methods=["GET", "POST"])
@login_required
def receive(transaction_id):
    """User Confirmation (Send Request)"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user email
    email = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["email"]

    # Query database for transactions
    transactions = db.execute("SELECT * FROM payment WHERE id = ? AND entity = ?", transaction_id, email)

    # Apology for wrong parameter
    if len(transactions) != 1:
        return apology("Wrong path!", 400)

    # Apology for wrong approach
    if transactions[0]["status"] != "Pending":
        return apology("Wrong approach!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from user confirmation form
        status = request.form.get("status")

        # Update database for successful
        if status == "Successful":

            # Track transaction amount
            amount = transactions[0]["amount"]

            # Query database for user balance
            balance = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["balance"]

            # Update user balance
            db.execute("UPDATE users SET balance = ? WHERE id = ?", balance + amount, user)

            # Update transaction status
            db.execute("UPDATE payment SET status = ? WHERE id = ?", status, transaction_id)

            # Redirect to default route
            flash("Send request is received!")
            return redirect("/")

        # Update database for failed
        elif status == "Failed":

            # Track transaction user and amount
            user_id = transactions[0]["user"]
            amount = transactions[0]["amount"]

            # Query database for user balance
            balance = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]["balance"]

            # Update user balance
            db.execute("UPDATE users SET balance = ? WHERE id = ?", balance + amount, user_id)

            # Update transaction status
            db.execute("UPDATE payment SET status = ? WHERE id = ?", status, transaction_id)

            # Redirect to default route
            flash("Send request is not received!")
            return redirect("/")

        # Pass for pending
        else:
            flash("Nothing is changed!")
            return redirect("/")

    # User reached route via GET
    else:
        return render_template("receive.html", transaction_id=transaction_id, transaction=transactions[0])


@app.route("/send-<transaction_id>", methods=["GET", "POST"])
@login_required
def send(transaction_id):
    """User Confirmation (Receive Request)"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user email
    email = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["email"]

    # Query database for transactions
    transactions = db.execute("SELECT * FROM payment WHERE id = ? AND entity = ?", transaction_id, email)

    # Apology for wrong parameter
    if len(transactions) != 1:
        return apology("Wrong path!", 400)

    # Apology for wrong approach
    if transactions[0]["status"] != "Pending":
        return apology("Wrong approach!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from user confirmation form
        status = request.form.get("status")

        # Update database for successful
        if status == "Successful":

            # Track transaction user and amount
            user_id = transactions[0]["user"]
            amount = transactions[0]["amount"]

            # Query database for user balance
            balance1 = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["balance"]
            balance2 = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]["balance"]

            # Apology for insufficient balance
            if balance1 < amount:
                return apology("Insufficient balance to accept!", 400)

            # Update user balance
            db.execute("UPDATE users SET balance = ? WHERE id = ?", balance1 - amount, user)
            db.execute("UPDATE users SET balance = ? WHERE id = ?", balance2 + amount, user_id)

            # Update transaction status
            db.execute("UPDATE payment SET status = ? WHERE id = ?", status, transaction_id)

            # Redirect to default route
            flash("Receive request is sent!")
            return redirect("/")

        # Update database for failed
        elif status == "Failed":

            # Update transaction status
            db.execute("UPDATE payment SET status = ? WHERE id = ?", status, transaction_id)

            # Redirect to default route
            flash("Receive request is not sent!")
            return redirect("/")

        # Pass for pending
        else:
            flash("Nothing is changed!")
            return redirect("/")

    # User reached route via GET
    else:
        return render_template("send.html", transaction_id=transaction_id, transaction=transactions[0])


@app.route("/ensure-<transaction_id>", methods=["GET", "POST"])
@login_required
def ensure(transaction_id):
    """User Confirmation (Withdraw Request)"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for transactions
    transactions = db.execute("SELECT * FROM payment WHERE id = ? AND user = ?", transaction_id, user)

    # Apology for wrong parameter
    if len(transactions) != 1:
        return apology("Wrong path!", 400)

    # Apology for wrong approach
    if transactions[0]["status"] != "Pending":
        return apology("Wrong approach!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from user confirmation form
        status = request.form.get("status")

        # Update database for successful
        if status == "Successful":

            # Update transaction status
            db.execute("UPDATE payment SET status = ? WHERE id = ?", status, transaction_id)

            # Redirect to default route
            flash("Withdraw becomes successful!")
            return redirect("/")

        # Update database for failed
        elif status == "Failed":

            # Track transaction amount
            amount = transactions[0]["amount"]

            # Query database for user balance
            balance = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["balance"]

            # Update user balance
            db.execute("UPDATE users SET balance = ? WHERE id = ?", balance + amount, user)

            # Update transaction status
            db.execute("UPDATE payment SET status = ? WHERE id = ?", status, transaction_id)

            # Redirect to default route
            flash("Withdraw becomes failed!")
            return redirect("/")

        # Pass for pending
        else:
            flash("Nothing is changed!")
            return redirect("/")

    # User reached route via GET
    else:
        return render_template("ensure.html", transaction_id=transaction_id, transaction=transactions[0])


@app.route("/admin")
@login_required
def admin():
    """Admin Section"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for admin username
    admin = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["username"]

    # Apology for other users
    if admin != "orsonline":
        return apology("Only admin can access!", 400)

    # Query database for deposit and withdraw transactions
    Deposit = "Deposit"
    Withdraw = "Withdraw"
    transactions = db.execute("SELECT * FROM payment WHERE type = ? OR type = ? ORDER BY id", Deposit, Withdraw)

    # Show full list of transactions
    return render_template("admin.html", transactions=transactions, usd=usd)


@app.route("/tid-<transaction_id>", methods=["GET", "POST"])
@login_required
def tid(transaction_id):
    """Admin Sub-Section (Deposit)"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for admin username
    admin = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["username"]

    # Apology for other users
    if admin != "orsonline":
        return apology("Only admin can access!", 400)

    # Query database for transaction information
    Deposit = "Deposit"
    rows = db.execute("SELECT * FROM payment WHERE id = ? AND type = ?", transaction_id, Deposit)

    # Apology for wrong parameter
    if len(rows) != 1:
        return apology("Wrong path!", 400)

    # Apology for wrong approach
    if rows[0]["status"] != "Pending":
        return apology("Wrong approach!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from admin confirmation form
        status = request.form.get("status")

        # Update database for successful
        if status == "Successful":

            # Track user id and amount
            user_id = rows[0]["user"]
            amount = rows[0]["amount"]

            # Query database for user balance
            balance = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]["balance"]

            # Update user balance
            db.execute("UPDATE users SET balance = ? WHERE id = ?", balance + amount, user_id)

            # Update transaction status
            db.execute("UPDATE payment SET status = ? WHERE id = ?", status, transaction_id)

            # Redirect to admin route
            flash("Deposit becomes successful!")
            return redirect("/admin")

        # Update database for failed
        elif status == "Failed":

            # Update transaction status
            db.execute("UPDATE payment SET status = ? WHERE id = ?", status, transaction_id)

            # Redirect to admin route
            flash("Deposit becomes failed!")
            return redirect("/admin")

        # Pass for pending
        else:
            flash("Nothing is changed!")
            return redirect("/admin")

    # User reached route via GET
    else:
        return render_template("tid.html", transaction_id=transaction_id, row=rows[0])


@app.route("/xid-<transaction_id>", methods=["GET", "POST"])
@login_required
def xid(transaction_id):
    """Admin Sub-Section (Withdraw)"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for admin username
    admin = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["username"]

    # Apology for other users
    if admin != "orsonline":
        return apology("Only admin can access!", 400)

    # Query database for transaction information
    Withdraw = "Withdraw"
    rows = db.execute("SELECT * FROM payment WHERE id = ? AND type = ?", transaction_id, Withdraw)

    # Apology for wrong parameter
    if len(rows) != 1:
        return apology("Wrong path!", 400)

    # Apology for wrong approach
    if rows[0]["status"] != "Pending":
        return apology("Wrong approach!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from admin input form
        xid = request.form.get("xid")

        # Update transaction xid
        db.execute("UPDATE payment SET xid = ? WHERE id = ?", xid, transaction_id)

        # Redirect to admin route
        flash("Admin input is done!")
        return redirect("/admin")

    # User reached route via GET
    else:
        return render_template("xid.html", transaction_id=transaction_id, row=rows[0])


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add Service"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user type
    group = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["type"]

    # User reached route via POST
    if request.method == "POST":

        # Get input from service form
        service = request.form.get("service")
        category = request.form.get("category")
        location = request.form.get("location")
        title = request.form.get("title")
        revenue = request.form.get("revenue")
        details = request.form.get("details")
        image = request.form.get("image")

        # Add service to Accommodation Section
        if service == "Accommodation":

            # Ensure valid category
            if category == "House" or category == "Warehouse" or category == "Resort" or category == "Hotel":

                # Insert rows into database
                db.execute("INSERT INTO services (service, title, location, category, revenue, details, image, provider) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                           service, title, location, category, revenue, details, image, user)

                # Redirect to accommodation route
                flash("Service is added to Accommodation!")
                return redirect("/accommodation")

            # Apology for invalid category
            else:
                return apology("Invalid category!", 400)

        # Add service to Consultancy Section
        elif service == "Consultancy":

            # Ensure valid category
            if category == "Education" or category == "Health" or category == "Business" or category == "Innovation":

                # Insert rows into database
                db.execute("INSERT INTO services (service, title, location, category, revenue, details, image, provider) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                           service, title, location, category, revenue, details, image, user)

                # Redirect to consultancy route
                flash("Service is added to Consultancy!")
                return redirect("/consultancy")

            # Apology for invalid category
            else:
                return apology("Invalid category!", 400)

        # Add service to Transportation Section
        elif service == "Transportation":

            # Ensure valid category
            if category == "Taxi" or category == "Car" or category == "Bus" or category == "Truck":

                # Insert rows into database
                db.execute("INSERT INTO services (service, title, location, category, revenue, details, image, provider) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                           service, title, location, category, revenue, details, image, user)

                # Redirect to transportation route
                flash("Service is added to Transportation!")
                return redirect("/transportation")

            # Apology for invalid category
            else:
                return apology("Invalid category!", 400)

        # Apology for invalid service
        else:
            return apology("Invalid service!", 400)

    # User reached route via GET
    else:

        # Ensure only provider to add service
        if group == "provider":
            return render_template("add.html")

        # Apology for other case
        else:
            return apology("Only provider can add service!", 400)


@app.route("/edit-<service_id>", methods=["GET", "POST"])
@login_required
def edit(service_id):
    """Edit Service"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user type
    group = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["type"]

    # Query database for service information
    rows = db.execute("SELECT * FROM services WHERE id = ? AND provider = ?", service_id, user)

    # Apology for wrong parameter
    if len(rows) != 1:
        return apology("Wrong path!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from service form
        service = request.form.get("service")
        category = request.form.get("category")
        location = request.form.get("location")
        title = request.form.get("title")
        revenue = request.form.get("revenue")
        details = request.form.get("details")
        image = request.form.get("image")

        # Edit service to Accommodation Section
        if service == "Accommodation":

            # Ensure valid category
            if category == "House" or category == "Warehouse" or category == "Resort" or category == "Hotel":

                # Update rows into database
                db.execute("UPDATE services SET service = ?, title = ?, location = ?, category = ?, revenue = ?, details = ?, image = ? WHERE id = ?",
                           service, title, location, category, revenue, details, image, service_id)

                # Redirect to accommodation route
                flash("Service is updated to Accommodation!")
                return redirect("/accommodation")

            # Apology for invalid category
            else:
                return apology("Invalid category!", 400)

        # Edit service to Consultancy Section
        elif service == "Consultancy":

            # Ensure valid category
            if category == "Education" or category == "Health" or category == "Business" or category == "Innovation":

                # Update rows into database
                db.execute("UPDATE services SET service = ?, title = ?, location = ?, category = ?, revenue = ?, details = ?, image = ? WHERE id = ?",
                           service, title, location, category, revenue, details, image, service_id)

                # Redirect to consultancy route
                flash("Service is updated to Consultancy!")
                return redirect("/consultancy")

            # Apology for invalid category
            else:
                return apology("Invalid category!", 400)

        # Edit service to Transportation Section
        elif service == "Transportation":

            # Ensure valid category
            if category == "Taxi" or category == "Car" or category == "Bus" or category == "Truck":

                # Update rows into database
                db.execute("UPDATE services SET service = ?, title = ?, location = ?, category = ?, revenue = ?, details = ?, image = ? WHERE id = ?",
                           service, title, location, category, revenue, details, image, service_id)

                # Redirect to transportation route
                flash("Service is updated to Transportation!")
                return redirect("/transportation")

            # Apology for invalid category
            else:
                return apology("Invalid category!", 400)

        # Apology for invalid service
        else:
            return apology("Invalid service!", 400)

    # User reached route via GET
    else:

        # Ensure only provider to edit service
        if group == "provider":
            return render_template("edit.html", service_id=service_id, row=rows[0])

        # Apology for other case
        else:
            return apology("Only provider can edit service!", 400)


@app.route("/empty-<service_id>", methods=["GET", "POST"])
@login_required
def empty(service_id):
    """Empty Service"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user type
    group = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["type"]

    # Query database for service information
    rows = db.execute("SELECT * FROM services WHERE id = ? AND provider = ?", service_id, user)

    # Apology for wrong parameter
    if len(rows) != 1:
        return apology("Wrong path!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from service form
        confirm = request.form.get("confirm")

        # Confirm empty service
        if confirm == "Yes":

            # Set no customer in database
            db.execute("UPDATE services SET customer = NULL WHERE id = ?", service_id)

            # Redirect to default route
            flash("Service is disengaged!")
            return redirect("/")

        # Don't confirm empty service
        else:
            return redirect("/")

    # User reached route via GET
    else:

        # Ensure only provider to empty service
        if group == "provider":
            return render_template("empty.html", service_id=service_id, row=rows[0])

        # Apology for other case
        else:
            return apology("Only provider can empty service!", 400)


@app.route("/delete-<service_id>", methods=["GET", "POST"])
@login_required
def delete(service_id):
    """Delete Service"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user type
    group = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["type"]

    # Query database for service information
    rows = db.execute("SELECT * FROM services WHERE id = ? AND provider = ?", service_id, user)

    # Apology for wrong parameter
    if len(rows) != 1:
        return apology("Wrong path!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from service form
        confirm = request.form.get("confirm")

        # Confirm delete service
        if confirm == "Yes":

            # Delete rows from database
            db.execute("DELETE FROM services WHERE id = ?", service_id)

            # Redirect to default route
            flash("Service is deleted!")
            return redirect("/")

        # Don't confirm delete service
        else:
            return redirect("/")

    # User reached route via GET
    else:

        # Ensure only provider to delete service
        if group == "provider":
            return render_template("delete.html", service_id=service_id, row=rows[0])

        # Apology for other case
        else:
            return apology("Only provider can delete service!", 400)


@app.route("/engage-<service_id>", methods=["GET", "POST"])
@login_required
def engage(service_id):
    """Engage Service"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user type
    group = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["type"]

    # Query database for service information
    rows = db.execute("SELECT * FROM services WHERE id = ?", service_id)

    # Apology for wrong parameter
    if len(rows) != 1:
        return apology("Wrong path!", 400)

    # Apology for booked service
    if rows[0]["customer"] != None:
        return apology("Service is already engaged!", 400)

    # User reached route via POST
    if request.method == "POST":

        # Get input from engage confirmation form
        confirm = request.form.get("confirm")

        # Confirm engage service
        if confirm == "Yes":

            # Track service cost
            cost = rows[0]["revenue"]

            # Query database for customer balance
            balance = db.execute("SELECT * FROM users WHERE id = ?", user)[0]["balance"]

            # Apology for insufficient customer balance
            if balance < cost:
                return apology("Insufficient balance to engage!", 400)

            # Query database for provider
            provider = db.execute("SELECT * FROM services WHERE id = ?", service_id)[0]["provider"]

            # Query database for provider balance
            provider_balance = db.execute("SELECT * FROM users WHERE id = ?", provider)[0]["balance"]

            # Update service information
            db.execute("UPDATE services SET customer = ? WHERE id = ?", user, service_id)

            # Update customer and provider balances
            db.execute("UPDATE users SET balance = ? WHERE id = ?", balance - cost, user)
            db.execute("UPDATE users SET balance = ? WHERE id = ?", provider_balance + cost, provider)

            # Insert send request into payment
            email = db.execute("SELECT * FROM users WHERE id = ?", provider)[0]["email"]
            kind = "Send"
            status = "Successful"
            db.execute("INSERT INTO payment (user, entity, amount, type, status) VALUES(?, ?, ?, ?, ?)", user, email, cost, kind, status)

            # Redirect to default route
            flash("Service is engaged!")
            return redirect("/")

        # Don't confirm engage service
        else:
            return redirect("/")

    # User reached route via GET
    else:

        # Ensure only customer to engage service
        if group == "customer":
            return render_template("engage.html", service_id=service_id, row=rows[0])

        # Apology for other case
        else:
            return apology("Only customer can engage service!", 400)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Get input from registration form
        group = request.form.get("type")
        email = request.form.get("email")
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Query database for email and username
        email_list = db.execute("SELECT * FROM users WHERE email = ?", email)
        username_list = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Apology for existing email
        if len(email_list) != 0:
            return apology("Email is already registered!", 400)

        # Apology for existing username
        elif len(username_list) != 0:
            return apology("Username is already taken!", 400)

        # After ensuring unique email and username
        else:

            # Ensure passwords are matched
            if (password != confirmation):
                return apology("Passwords don't match!", 400)

            # Insert rows into database with new users
            db.execute("INSERT INTO users (username, hash, email, type, name) VALUES(?, ?, ?, ?, ?)", username,
                       generate_password_hash(password, method='pbkdf2:sha256', salt_length=8), email, group, name)

            # Query database for username
            users = db.execute("SELECT * FROM users WHERE username = ?", username)

            # Remember which user has registered in
            session["user_id"] = users[0]["id"]

            # Redirecting to security route
            flash("You are registered!")
            return redirect("/security")

    # User reached route via GET
    else:
        return render_template("register.html")


@app.route("/security", methods=["GET", "POST"])
@login_required
def security():
    """Secure user"""

    # Keep track of the user
    user = session["user_id"]

    # User reached route via POST
    if request.method == "POST":

        # Get input from security form
        code = request.form.get("code")
        one = request.form.get("one")
        two = request.form.get("two")
        three = request.form.get("three")

        # Insert rows into database with new users
        db.execute("INSERT INTO security (user, code, one, two, three) VALUES(?, ?, ?, ?, ?)", user, code, one, two, three)

        # Redirecting to default route
        flash("Welcome to ORS!")
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("security.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Get input from login form
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid username and/or password!", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/recover", methods=["GET", "POST"])
def recover():
    """Recover password"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Get input from recovery form
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        code = request.form.get("code")
        one = request.form.get("one")
        two = request.form.get("two")
        three = request.form.get("three")

        # Query database for security questions
        users = db.execute("SELECT * FROM users WHERE email = ?", email)
        check = db.execute("SELECT * FROM security WHERE user IN (SELECT id FROM users WHERE email = ?)", email)

        # Ensure email exists
        if len(check) != 1:
            return apology("Email is not registered!", 403)

        # After checking existing email
        else:

            # Access database for existing email
            check_code = check[0]["code"]
            check_one = check[0]["one"]
            check_two = check[0]["two"]
            check_three = check[0]["three"]

            # Apology for wrong code
            if code != check_code:
                return apology("Wrong code!", 403)

            # Apology for wrong birthplace
            elif one != check_one:
                return apology("Wrong birthplace!", 403)

            # Apology for wrong school
            elif two != check_two:
                return apology("Wrong school!", 403)

            # Apology for wrong nickname
            elif three != check_three:
                return apology("Wrong nickname!", 403)

            # Ensure passwords are matched
            elif (password != confirmation):
                return apology("Passwords don't match!", 403)

            # Update password after checking
            else:

                # Set new password into users
                db.execute("UPDATE users SET hash = ? WHERE email = ?",
                           generate_password_hash(password, method='pbkdf2:sha256', salt_length=8), email)

                # Remember which user has logged in
                session["user_id"] = users[0]["id"]

                # Redirect to default route
                flash("Password is recovered!")
                return redirect("/")

    # User reached route via GET
    else:
        return render_template("recover.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/profile")
@login_required
def profile():
    """User Profile"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user information
    info = db.execute("SELECT * FROM users WHERE id = ?", user)[0]
    security = db.execute("SELECT * FROM security WHERE user = ?", user)[0]

    # Pass user information
    return render_template("profile.html", info=info, security=security)


@app.route("/info", methods=["GET", "POST"])
@login_required
def info():
    """Edit Profile"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for user information
    info = db.execute("SELECT * FROM users WHERE id = ?", user)[0]

    # User reached route via POST
    if request.method == "POST":

        # Get input from info form
        name = request.form.get("name")
        father = request.form.get("father")
        mother = request.form.get("mother")
        profession = request.form.get("profession")
        nid = request.form.get("nid")
        line = request.form.get("line")
        no = request.form.get("no")
        area = request.form.get("area")
        code = request.form.get("code")
        city = request.form.get("city")
        region = request.form.get("region")
        country = request.form.get("country")
        about = request.form.get("about")
        image = request.form.get("image")

        # Update profile information
        db.execute("UPDATE users SET name = ?, father = ?, mother = ?, profession = ?, nid = ?, line = ?, no = ?, area = ?, code = ?, city = ?, region = ?, country = ?, about = ?, image = ? WHERE id = ?",
                   name, father, mother, profession, nid, line, no, area, code, city, region, country, about, image, user)

        # Redirect to profile route
        flash("Profile is updated!")
        return redirect("/profile")

    # User reached route via GET
    else:
        return render_template("info.html", info=info)


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change Password"""

    # Keep track of the user
    user = session["user_id"]

    # User reached route via POST
    if request.method == "POST":

        # Get input from password form
        old = request.form.get("old")
        new = request.form.get("new")
        confirm = request.form.get("confirm")

        # Ensure new passwords are matched
        if (new != confirm):
            return apology("New passwords don't match!", 400)

        # Fetch old password from database to check
        password = db.execute("SELECT hash FROM users WHERE id = ?", user)[0]["hash"]

        # Check old password with database's password for security
        if not check_password_hash(password, old):
            return apology("Old password is incorrect!", 400)

        # Update database with new password
        else:

            # Set new password into users table's hash
            db.execute("UPDATE users SET hash = ? WHERE id = ?",
                       generate_password_hash(new, method='pbkdf2:sha256', salt_length=8), user)

            # Redirect to profile route
            flash("Password is changed!")
            return redirect("/profile")

    # User reached route via GET
    else:
        return render_template("password.html")


@app.route("/questions", methods=["GET", "POST"])
@login_required
def questions():
    """Update Security Questions"""

    # Keep track of the user
    user = session["user_id"]

    # Query database for security questions
    security = db.execute("SELECT * FROM security WHERE user = ?", user)[0]

    # User reached route via POST
    if request.method == "POST":

        # Get input from questions form
        code = request.form.get("code")
        one = request.form.get("one")
        two = request.form.get("two")
        three = request.form.get("three")

        # Update security questions
        db.execute("UPDATE security SET code = ?, one = ?, two = ?, three = ? WHERE user = ?",
                   code, one, two, three, user)

        # Redirect to profile route
        flash("Security questions are updated!")
        return redirect("/profile")

    # User reached route via GET
    else:
        return render_template("questions.html", security=security)


@app.route("/search", methods=["POST"])
def search():
    """Search Service"""

    # Get input from search field
    q = request.form.get("q")

    # Query database
    rows = db.execute("SELECT * FROM services WHERE category = ? OR location = ?", q, q)

    # Apology for not reaching
    if len(rows) == 0:
        return apology("Search couldn't reach!", 400)

    # Pass parameter to render
    return render_template("search.html", rows=rows, usd=usd)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)