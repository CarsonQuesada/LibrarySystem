from flask import Flask, render_template, request, redirect, session, flash # type: ignore
from models import db, Book, LibraryUser, Loan
from datetime import datetime
from auth import hash_password, verify_password
import os

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

# ---------------- CONFIG ----------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "database", "library.db")

os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SECRET_KEY'] = 'secret'

db.init_app(app)

# ---------------- INIT DB ----------------
with app.app_context():
    db.create_all()

    # Dummy Users
    if not LibraryUser.query.first():
        user1 = LibraryUser(
            name="Test User",
            email="test@test.com",
            password=hash_password("1234"),
            is_librarian=False
        )

        user2 = LibraryUser(
            name="Admin",
            email="admin@test.com",
            password=hash_password("admin"),
            is_librarian=True
        )

        db.session.add_all([user1, user2])
        db.session.commit()

    # Dummy Books
    if not Book.query.first():
        books = [
            Book(title="The Great Gatsby", author="F. Scott Fitzgerald", isbn="111", copy_count=5, available_copies=5),
            Book(title="1984", author="George Orwell", isbn="222", copy_count=3, available_copies=3),
            Book(title="To Kill a Mockingbird", author="Harper Lee", isbn="333", copy_count=4, available_copies=4),
        ]
        db.session.add_all(books)
        db.session.commit()

# ---------------- CONTEXT ----------------
@app.context_processor
def inject_user():
    if "user_id" in session:
        user = LibraryUser.query.get(session["user_id"])
        return dict(current_user=user)
    return dict(current_user=None)

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    q = request.args.get("q", "").strip()

    if q:
        books = Book.query.filter(
            (Book.title.contains(q)) |
            (Book.author.contains(q))
        ).all()
    else:
        books = Book.query.all()

    return render_template("index.html", books=books)

# ---------------- ADMIN: DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user = LibraryUser.query.get(session["user_id"])
    if not user or not user.is_librarian:
        return "Unauthorized", 403

    total_books = Book.query.count()
    total_users = LibraryUser.query.count()
    active_loans = Loan.query.filter_by(returned=False).count()

    return render_template(
        "admin_dashboard.html",
        total_books=total_books,
        total_users=total_users,
        active_loans=active_loans
    )

# ---------------- ADMIN: SHOW ADD BOOK PAGE ----------------
@app.route("/admin/books/add", methods=["GET"])
def show_add_book():
    if "user_id" not in session:
        return redirect("/login")

    user = LibraryUser.query.get(session["user_id"])
    if not user or not user.is_librarian:
        return "Unauthorized", 403

    return render_template("add_book.html")

# ---------------- ADMIN: HANDLE ADD BOOK ----------------
@app.route("/admin/books/add", methods=["POST"])
def add_book_admin():
    if "user_id" not in session:
        return redirect("/login")

    user = LibraryUser.query.get(session["user_id"])
    if not user or not user.is_librarian:
        return "Unauthorized", 403

    copy_count = int(request.form["copy_count"])

    book = Book(
        title=request.form["title"],
        author=request.form["author"],
        isbn=request.form["isbn"],
        copy_count=copy_count,
        available_copies=copy_count  # auto set
    )

    db.session.add(book)
    db.session.commit()

    flash(f"Successfully added {book.title}.", "success")
    return redirect("/")

# ---------------- ADMIN: VIEW LOANS ----------------
@app.route("/admin/loans")
def admin_loans():
    if "user_id" not in session:
        return redirect("/login")

    user = LibraryUser.query.get(session["user_id"])
    if not user or not user.is_librarian:
        return "Unauthorized", 403

    q = request.args.get("q", "").strip()

    if q:
        loans = Loan.query.join(LibraryUser).join(Book).filter(
            (LibraryUser.name.contains(q)) |
            (LibraryUser.email.contains(q)) |
            (Book.title.contains(q))
        ).all()
    else:
        loans = Loan.query.all()

    return render_template("admin_loans.html", loans=loans)

# ---------------- ADMIN: EDIT BOOK ----------------
@app.route("/admin/books/<int:book_id>/edit", methods=["GET", "POST"])
def edit_book(book_id):
    if "user_id" not in session:
        return redirect("/login")

    user = LibraryUser.query.get(session["user_id"])
    if not user or not user.is_librarian:
        return "Unauthorized", 403

    book = Book.query.get(book_id)

    if request.method == "POST":
        book.title = request.form["title"]
        book.author = request.form["author"]
        book.isbn = request.form["isbn"]

        new_copy_count = int(request.form["copy_count"])
        checked_out = book.copy_count - book.available_copies

        if new_copy_count < checked_out:
            flash(f"Cannot reduce below {checked_out} (currently checked out).", "warning")
            return redirect(f"/admin/books/{book_id}/edit")

        book.copy_count = new_copy_count
        book.available_copies = new_copy_count - checked_out

        db.session.commit()
        flash(f"Successfully updated {book.title}.", "success")
        return redirect("/admin/dashboard")

    return render_template("edit_book.html", book=book)

# ---------------- ADMIN: DELETE BOOK ----------------
@app.route("/admin/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    if "user_id" not in session:
        return redirect("/login")

    user = LibraryUser.query.get(session["user_id"])
    if not user or not user.is_librarian:
        return "Unauthorized", 403

    book = Book.query.get(book_id)

    if not book:
        return "Book not found", 404

    # 🔥 Prevent deleting if copies are borrowed
    if book.available_copies < book.copy_count:
        flash("Cannot delete book: copies are currently borrowed.", "danger")
        return redirect("/")

    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully.", "success")
    return redirect("/")

# ---------------- ADMIN: MANAGE USERS ----------------
@app.route("/admin/users")
def admin_users():
    if "user_id" not in session:
        return redirect("/login")

    current_user = LibraryUser.query.get(session["user_id"])
    if not current_user or not current_user.is_librarian:
        return "Unauthorized", 403

    q = request.args.get("q", "").strip()

    if q:
        users = LibraryUser.query.filter(
            (LibraryUser.name.contains(q)) |
            (LibraryUser.email.contains(q))
        ).all()
    else:
        users = LibraryUser.query.all()

    return render_template("manage_users.html", users=users)

# ---------------- ADMIN: PROMOTE USER ----------------
@app.route("/admin/users/<int:user_id>/promote", methods=["POST"])
def promote_user(user_id):
    if "user_id" not in session:
        return redirect("/login")

    current_user = LibraryUser.query.get(session["user_id"])
    if not current_user or not current_user.is_librarian:
        return "Unauthorized", 403

    user = LibraryUser.query.get(user_id)
    if not user:
        return "User not found", 404

    user.is_librarian = True
    db.session.commit()
    flash("User promoted to librarian.", "success")

    return redirect("/admin/users")

# ---------------- ADMIN: DEMOTE USER ----------------
@app.route("/admin/users/<int:user_id>/demote", methods=["POST"])
def demote_user(user_id):
    if "user_id" not in session:
        return redirect("/login")

    current_user = LibraryUser.query.get(session["user_id"])
    if not current_user or not current_user.is_librarian:
        return "Unauthorized", 403

    # prevent self-demotion
    if user_id == current_user.id:
        flash("You cannot demote yourself.", "warning")
        return redirect("/admin/users")

    user = LibraryUser.query.get(user_id)
    if not user:
        return "User not found", 404

    user.is_librarian = False
    db.session.commit()
    flash("User demoted.", "info")

    return redirect("/admin/users")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        existing_user = LibraryUser.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists!"

        hashed_password = hash_password(password)

        new_user = LibraryUser(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id
        flash("Registration successful! Welcome to the library.", "success")
        return redirect("/")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = LibraryUser.query.filter_by(email=request.form["email"]).first()

        if user and verify_password(user.password, request.form["password"]):
            session["user_id"] = user.id
            return redirect("/")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- BORROW ----------------
@app.route("/borrow/<int:book_id>")
def borrow(book_id):
    if "user_id" not in session:
        return redirect("/login")

    book = Book.query.get(book_id)

    if book and book.available_copies > 0:
        loan = Loan(user_id=session["user_id"], book_id=book_id)
        book.available_copies -= 1

        db.session.add(loan)
        db.session.commit()
        flash(f"Successfully borrowed {book.title}.", "success")

    return redirect("/")

# ---------------- RETURN BOOK (ADMIN) ----------------
@app.route("/admin/loans/<int:loan_id>/return", methods=["POST"])
def admin_return_loan(loan_id):
    if "user_id" not in session:
        return redirect("/login")

    current_user = LibraryUser.query.get(session["user_id"])
    if not current_user or not current_user.is_librarian:
        return "Unauthorized", 403

    loan = Loan.query.get(loan_id)
    if not loan:
        flash("Loan not found.", "danger")
        return redirect("/admin/loans")

    if loan.returned:
        flash("This loan is already marked as returned.", "info")
        return redirect("/admin/loans")

    book = Book.query.get(loan.book_id)
    loan.returned = True

    if book.available_copies < book.copy_count:
        book.available_copies += 1

    db.session.commit()
    flash(f'"{book.title}" was returned successfully.', "success")
    return redirect("/admin/loans")

# ---------------- ACCOUNT ----------------
@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect("/login")

    user = LibraryUser.query.get(session["user_id"])

    loans = Loan.query.filter_by(
        user_id=session["user_id"],
        returned=False
    ).all()

    return render_template(
        "account.html",
        user=user,
        loans=loans
    )


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)