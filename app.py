from flask import Flask, render_template, request, redirect, session
from models import db, Book, LibraryUser, Loan
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SECRET_KEY'] = 'secret'

db.init_app(app)

with app.app_context():
    db.create_all()

# ---------------- HOME ----------------
@app.route("/")
def home():
    books = Book.query.all()
    return render_template("index.html", books=books)

# ---------------- ADD BOOK ----------------
@app.route("/add_book", methods=["POST"])
def add_book():
    book = Book(
        title=request.form["title"],
        author=request.form["author"],
        isbn=request.form["isbn"],
        copy_count=int(request.form["copies"]),
        available_copies=int(request.form["copies"])
    )
    db.session.add(book)
    db.session.commit()
    return redirect("/")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = LibraryUser.query.filter_by(email=request.form["email"]).first()
        if user and user.password == request.form["password"]:
            session["user_id"] = user.id
            return redirect("/")
    return render_template("login.html")

# ---------------- BORROW ----------------
@app.route("/borrow/<int:book_id>")
def borrow(book_id):
    if "user_id" not in session:
        return redirect("/login")

    book = Book.query.get(book_id)

    if book.available_copies > 0:
        loan = Loan(user_id=session["user_id"], book_id=book_id)
        book.available_copies -= 1
        db.session.add(loan)
        db.session.commit()

    return redirect("/")

# ---------------- RETURN ----------------
@app.route("/return/<int:loan_id>")
def return_book(loan_id):
    loan = Loan.query.get(loan_id)
    book = Book.query.get(loan.book_id)

    loan.returned = True
    book.available_copies += 1

    db.session.commit()
    return redirect("/account")

# ---------------- ACCOUNT ----------------
@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect("/login")

    loans = Loan.query.filter_by(user_id=session["user_id"], returned=False).all()
    return render_template("account.html", loans=loans)

app.run(debug=True)