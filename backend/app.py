from flask import Flask, render_template, request, redirect, session # type: ignore
from models import db, Book, LibraryUser, Loan
from datetime import datetime

app = Flask(__name__, 
            template_folder="../frontend/templates", 
            static_folder="../frontend/static"
            )
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "database", "library.db")

os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SECRET_KEY'] = 'secret'


db.init_app(app)

with app.app_context():
    db.create_all()

    # ---------------- DUMMY USERS ----------------
    if not LibraryUser.query.first():
        user1 = LibraryUser(
            name="Test User",
            email="test@test.com",
            password="1234",
            is_librarian=False
        )

        user2 = LibraryUser(
            name="Admin",
            email="admin@test.com",
            password="admin",
            is_librarian=True
        )

        db.session.add_all([user1, user2])
        db.session.commit()

    # ---------------- DUMMY BOOKS ----------------
    if not Book.query.first():
        book1 = Book(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            isbn="111",
            copy_count=5,
            available_copies=5
        )

        book2 = Book(
            title="1984",
            author="George Orwell",
            isbn="222",
            copy_count=3,
            available_copies=3
        )

        book3 = Book(
            title="To Kill a Mockingbird",
            author="Harper Lee",
            isbn="333",
            copy_count=4,
            available_copies=4
        )

        db.session.add_all([book1, book2, book3])
        db.session.commit()

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

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if user already exists
        existing_user = LibraryUser.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists!"

        new_user = LibraryUser(
            name=name,
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id
        return redirect("/")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = LibraryUser.query.filter_by(email=request.form["email"]).first()
        if user and user.password == request.form["password"]:
            session["user_id"] = user.id
            return redirect("/")
    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

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