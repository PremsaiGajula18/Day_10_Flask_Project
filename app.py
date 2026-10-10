"""
=============================================================================
Movie Night Planner — Netflix-Inspired Flask Web Application
=============================================================================
Application Controller: app.py

Features:
---------
- Multipage Netflix-inspired cinematic web experience.
- Full user authentication with Flask sessions and Werkzeug password hashing.
- Native MySQL relational database integration using mysql-connector-python.
- Parameterized SQL queries preventing SQL injection vulnerabilities.
- Cryptographic CSRF protection enforced across all POST endpoints.
- Server-side validation and ownership permission enforcement.
- Democratic voting system with automatic single-ballot replacement.
- Host winner finalization with voting lock safeguards.
- Filter and search mechanism for browsing events.
=============================================================================
"""

import datetime
import functools
import os
import re
import secrets
from typing import Any, Callable, Dict, List, Optional

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import database

# ---------------------------------------------------------------------------
# Flask Application Setup
# ---------------------------------------------------------------------------
app = Flask(__name__)

# Secret key used for session signing and cryptographic cookies
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "cinematic-movie-night-netflix-dark-theme-key-2026"
)

# Register database teardown to cleanly close MySQL connections
app.teardown_appcontext(database.close_db)

# Allowed category types enforced across movie night forms
ALLOWED_CATEGORIES = ("Action", "Comedy", "Animation", "Other")


# ---------------------------------------------------------------------------
# Security & CSRF Protection Layer
# ---------------------------------------------------------------------------
def generate_csrf_token() -> str:
    """
    Generate or retrieve a cryptographically secure per-session CSRF token.

    If a CSRF token does not already exist in the user's active session,
    a 48-character hexadecimal token is generated using `secrets.token_hex(24)`
    and stored in `session['csrf_token']`.

    Returns:
        str: The active session's CSRF token string.
    """
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)
    return session["csrf_token"]


@app.context_processor
def inject_csrf_and_globals() -> Dict[str, Any]:
    """
    Inject global utility variables into all Jinja2 template contexts.

    Makes `csrf_token()` function and `current_year` directly callable
    in any HTML template without requiring explicit route parameter passing.

    Returns:
        dict: Dictionary containing template-accessible utilities.
    """
    return {
        "csrf_token": generate_csrf_token,
        "current_year": datetime.datetime.now().year,
    }


@app.before_request
def verify_csrf_token() -> Optional[Any]:
    """
    Verify CSRF tokens on all state-mutating HTTP POST requests.

    Intercepts every incoming POST request before reaching the route view.
    Compares the submitted form token with the expected session token.
    If the token is missing, invalid, or mismatched, the request is halted
    and the user is redirected with an alert message.

    Returns:
        Optional[Response]: Redirect response on verification failure, or None to proceed.
    """
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token")
        expected_token = session.get("csrf_token")

        if not submitted_token or submitted_token != expected_token:
            flash(
                "Security check failed (invalid or missing CSRF token). Please try again.",
                "danger",
            )
            return redirect(request.referrer or url_for("index"))

    return None


def login_required(view: Callable) -> Callable:
    """
    Decorator to restrict access to authenticated users only.

    Checks if `user_id` exists in the Flask session. If not, flashes an
    informative warning and redirects the unauthenticated visitor to the
    login page, appending a `next` query parameter to return after signing in.

    Args:
        view (Callable): The route handler function to protect.

    Returns:
        Callable: The decorated, access-controlled route handler.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return view(**kwargs)

    return wrapped_view


# ---------------------------------------------------------------------------
# Authentication Routes (Register, Login, Logout)
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration with form validation and password hashing.

    GET:
        Renders the user registration form (`register.html`).

    POST:
        1. Collects and trims full name, username, password, and confirmation.
        2. Validates non-empty fields, username format, and minimum password lengths.
        3. Queries MySQL to ensure the requested username is not already taken.
        4. Hashes the password securely via `generate_password_hash()`.
        5. Inserts the new user into the MySQL `users` table.
        6. Logs the user in directly by writing credentials to the session.
        7. Redirects to the homepage with a welcome message.
    """
    # Redirect already authenticated users away from registration
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        errors = []

        # Server-side validation rules
        if not name:
            errors.append("Full name is required.")
        if not username:
            errors.append("Username is required.")
        elif len(username) < 3 or len(username) > 30:
            errors.append("Username must be between 3 and 30 characters.")
        elif not re.match(r"^[a-zA-Z0-9_]+$", username):
            errors.append("Username can only contain letters, numbers, and underscores.")

        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        elif password != password_confirm:
            errors.append("Passwords do not match.")

        # Render errors if validation failed
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html")

        db = database.get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # Check for existing username in MySQL
            cursor.execute(
                "SELECT id FROM users WHERE username = %s LIMIT 1",
                (username,)
            )
            existing_user = cursor.fetchone()

            if existing_user:
                flash(
                    f"The username '{username}' is already taken. Please choose another.",
                    "danger",
                )
                return render_template("register.html")

            # Securely hash password and persist user
            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, username, password_hash) VALUES (%s, %s, %s)",
                (name, username, password_hash),
            )
            db.commit()

            new_user_id = cursor.lastrowid

            # Initialize user session
            session.clear()
            session["user_id"] = new_user_id
            session["username"] = username
            session["name"] = name
            generate_csrf_token()

            flash(
                f"Welcome to Movie Night Planner, {name}! Your account has been created.",
                "success",
            )
            return redirect(url_for("index"))

        finally:
            cursor.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Authenticate existing users using username and hashed password.

    GET:
        Renders the login form (`login.html`).

    POST:
        1. Reads username and plaintext password from form submission.
        2. Queries MySQL for a user matching the provided username.
        3. Verifies password hash using `werkzeug.security.check_password_hash()`.
        4. If verified, sets session variables (`user_id`, `username`, `name`).
        5. Validates `next` redirect target to prevent open redirect vulnerabilities.
        6. If verification fails, flashes a security-generic error message.
    """
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        db = database.get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s LIMIT 1",
                (username,)
            )
            user = cursor.fetchone()

            # Step 1: Check if username exists in database
            if user is None:
                flash("Username not found. Please check your username or register an account.", "danger")
                return render_template("login.html")

            # Step 2: Check if password matches
            if not check_password_hash(user["password_hash"], password):
                flash("Incorrect password. Please try again.", "danger")
                return render_template("login.html")

            # Successful login: initialize session
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]
            generate_csrf_token()

            flash(f"Welcome back, {user['name']}!", "success")

            # Safe redirect: prevent external open redirects
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("index"))

        finally:
            cursor.close()

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    """
    Log out the current user and destroy active session state.

    Clears the session dictionary, invalidates the CSRF token,
    and redirects the user to the public homepage with a confirmation alert.
    """
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Home & Browse Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """
    Browse upcoming and past movie nights with combined search and filtering.

    Query Parameters:
        q (str): Case-insensitive keyword to search within movie night titles.
        category (str): Genre filter (Action, Comedy, Animation, Other).

    Database Operation:
        Performs a dynamic SQL SELECT query joining `movie_nights` and `users`
        to display host information. Applies parameterized `WHERE` clauses
        for title matching and category selection. Results are sorted by
        finalization status and event date.
    """
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    db = database.get_db()
    cursor = db.cursor(dictionary=True)

    try:
        sql = """
            SELECT m.*, u.name AS creator_name
            FROM movie_nights m
            JOIN users u ON m.creator_id = u.id
            WHERE 1=1
        """
        params = []

        # Filter by title keyword
        if query:
            sql += " AND m.title LIKE %s"
            params.append(f"%{query}%")

        # Filter by category
        if category and category in ALLOWED_CATEGORIES:
            sql += " AND m.category = %s"
            params.append(category)

        # Ordering: active events first, then by date ascending
        sql += " ORDER BY m.is_finalized ASC, m.date ASC, m.id DESC"

        cursor.execute(sql, tuple(params))
        movie_nights = cursor.fetchall()

        return render_template(
            "index.html",
            movie_nights=movie_nights,
            query=query,
            current_category=category if category in ALLOWED_CATEGORIES else "",
        )

    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Movie Night CRUD Routes
# ---------------------------------------------------------------------------
@app.route("/night/create", methods=["GET", "POST"])
@login_required
def create_night():
    """
    Host a new movie night event.

    GET:
        Renders the event creation form (`create_night.html`).

    POST:
        1. Validates title (1..100 chars), valid ISO date (YYYY-MM-DD),
           allowed category, and description (1..1000 chars).
        2. Inserts record into MySQL `movie_nights` with `creator_id` set to
           the logged-in user's ID and `is_finalized` set to 0.
        3. Commits transaction and redirects to the newly created night's detail page.
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        date_str = request.form.get("date", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")
        elif len(title) > 100:
            errors.append("Title must be 100 characters or fewer.")

        if not date_str:
            errors.append("Date is required.")
        else:
            try:
                datetime.date.fromisoformat(date_str)
            except ValueError:
                errors.append("Invalid date format. Please use YYYY-MM-DD.")

        if category not in ALLOWED_CATEGORIES:
            errors.append(f"Invalid category. Must be one of: {', '.join(ALLOWED_CATEGORIES)}.")

        if not description:
            errors.append("Description is required.")
        elif len(description) > 1000:
            errors.append("Description must be 1000 characters or fewer.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("create_night.html")

        db = database.get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                INSERT INTO movie_nights (title, date, category, description, creator_id, is_finalized)
                VALUES (%s, %s, %s, %s, %s, 0)
                """,
                (title, date_str, category, description, session["user_id"]),
            )
            db.commit()

            new_night_id = cursor.lastrowid
            flash(
                f"Movie night '{title}' published successfully! Now add some movie choices.",
                "success",
            )
            return redirect(url_for("detail", night_id=new_night_id))

        finally:
            cursor.close()

    return render_template("create_night.html")


@app.route("/night/<int:night_id>")
def detail(night_id: int):
    """
    Display movie night details, nominated film choices, vote counts, and winner.

    Args:
        night_id (int): Primary key ID of the movie night.

    Features:
        - Retrieves event metadata and host name from MySQL.
        - Calculates real-time vote totals and percentages for each choice.
        - Identifies whether the logged-in attendee has already cast a vote.
        - Surfaces winner spotlight if the event has been finalized.
        - Renders host management controls if current user is the creator.
    """
    db = database.get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Fetch event details and host name
        cursor.execute(
            """
            SELECT m.*, u.name AS creator_name
            FROM movie_nights m
            JOIN users u ON m.creator_id = u.id
            WHERE m.id = %s
            LIMIT 1
            """,
            (night_id,),
        )
        night = cursor.fetchone()

        if night is None:
            abort(404)

        # Fetch candidate movie choices with aggregate vote counts
        cursor.execute(
            """
            SELECT c.*, COUNT(v.id) AS vote_count
            FROM movie_choices c
            LEFT JOIN votes v ON c.id = v.choice_id
            WHERE c.movie_night_id = %s
            GROUP BY c.id
            ORDER BY vote_count DESC, c.id ASC
            """,
            (night_id,),
        )
        choices_rows = cursor.fetchall()

        total_votes = sum(c["vote_count"] for c in choices_rows)

        # Calculate vote percentages for progress bars
        choices = []
        for c in choices_rows:
            choice_dict = dict(c)
            pct = (
                int(round((choice_dict["vote_count"] / total_votes * 100)))
                if total_votes > 0
                else 0
            )
            choice_dict["vote_pct"] = pct
            choices.append(choice_dict)

        # Check which choice the logged-in user previously voted for
        user_voted_choice_id = None
        if session.get("user_id"):
            cursor.execute(
                "SELECT choice_id FROM votes WHERE user_id = %s AND movie_night_id = %s LIMIT 1",
                (session["user_id"], night_id),
            )
            user_vote = cursor.fetchone()
            if user_vote:
                user_voted_choice_id = user_vote["choice_id"]

        # Fetch winning film choice if finalized
        final_choice = None
        if night["is_finalized"] and night["final_choice_id"]:
            for c in choices:
                if c["id"] == night["final_choice_id"]:
                    final_choice = c
                    break

        is_creator = session.get("user_id") == night["creator_id"]

        return render_template(
            "detail.html",
            night=night,
            choices=choices,
            total_votes=total_votes,
            user_voted_choice_id=user_voted_choice_id,
            final_choice=final_choice,
            is_creator=is_creator,
        )

    finally:
        cursor.close()


@app.route("/night/<int:night_id>/edit", methods=["GET", "POST"])
@login_required
def edit_night(night_id: int):
    """
    Edit details of an existing movie night.

    Permissions:
        - Only the event host (creator_id == session['user_id']) may edit.
        - Finalized movie nights cannot be edited.

    Args:
        night_id (int): Primary key ID of the movie night to update.
    """
    db = database.get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM movie_nights WHERE id = %s LIMIT 1", (night_id,))
        night = cursor.fetchone()

        if night is None:
            abort(404)

        # Ownership authorization check
        if night["creator_id"] != session["user_id"]:
            flash("You are not authorized to edit this movie night.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        # Immutability check for finalized events
        if night["is_finalized"]:
            flash("Cannot edit a finalized movie night.", "warning")
            return redirect(url_for("detail", night_id=night_id))

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            date_str = request.form.get("date", "").strip()
            category = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()

            errors = []
            if not title:
                errors.append("Title is required.")
            elif len(title) > 100:
                errors.append("Title must be 100 characters or fewer.")

            if not date_str:
                errors.append("Date is required.")
            else:
                try:
                    datetime.date.fromisoformat(date_str)
                except ValueError:
                    errors.append("Invalid date format. Please use YYYY-MM-DD.")

            if category not in ALLOWED_CATEGORIES:
                errors.append(f"Invalid category. Must be one of: {', '.join(ALLOWED_CATEGORIES)}.")

            if not description:
                errors.append("Description is required.")
            elif len(description) > 1000:
                errors.append("Description must be 1000 characters or fewer.")

            if errors:
                for error in errors:
                    flash(error, "danger")
                return render_template("edit_night.html", night=night)

            # Update MySQL record
            cursor.execute(
                """
                UPDATE movie_nights
                SET title = %s, date = %s, category = %s, description = %s
                WHERE id = %s
                """,
                (title, date_str, category, description, night_id),
            )
            db.commit()

            flash("Movie night details successfully updated!", "success")
            return redirect(url_for("detail", night_id=night_id))

        return render_template("edit_night.html", night=night)

    finally:
        cursor.close()


@app.route("/night/<int:night_id>/delete", methods=["POST"])
@login_required
def delete_night(night_id: int):
    """
    Cancel and permanently delete a movie night.

    Permissions:
        - Only the host can delete their own event.
        - Finalized events cannot be deleted.

    Cascade:
        Associated choices and votes are purged via MySQL foreign key CASCADE constraints.
    """
    db = database.get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM movie_nights WHERE id = %s LIMIT 1", (night_id,))
        night = cursor.fetchone()

        if night is None:
            abort(404)

        # Ownership authorization check
        if night["creator_id"] != session["user_id"]:
            flash("You are not authorized to delete this movie night.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        # Disallow deleting locked/finalized events
        if night["is_finalized"]:
            flash("Cannot delete a finalized movie night.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        cursor.execute("DELETE FROM movie_nights WHERE id = %s", (night_id,))
        db.commit()

        flash(f"Movie night '{night['title']}' was canceled and deleted.", "info")
        return redirect(url_for("index"))

    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Choices, Voting & Finalization Routes
# ---------------------------------------------------------------------------
@app.route("/night/<int:night_id>/choices", methods=["POST"])
@login_required
def add_choice(night_id: int):
    """
    Add a candidate film choice to the movie night ballot.

    Permissions:
        - Only the creator/host can add choices.
        - Choices cannot be added once the movie night is finalized.

    Args:
        night_id (int): Target movie night ID.
    """
    db = database.get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM movie_nights WHERE id = %s LIMIT 1", (night_id,))
        night = cursor.fetchone()

        if night is None:
            abort(404)

        # Only the creator may nominate films
        if night["creator_id"] != session["user_id"]:
            flash("Only the host can add movie choices to this event.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        if night["is_finalized"]:
            flash("Cannot add choices to a finalized movie night.", "warning")
            return redirect(url_for("detail", night_id=night_id))

        title = request.form.get("title", "").strip()
        genre = request.form.get("genre", "").strip()
        reason = request.form.get("reason", "").strip()

        if not title or not genre or not reason:
            flash("All fields (title, genre, and reason) are required to add a movie.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        if len(title) > 100 or len(genre) > 50 or len(reason) > 300:
            flash("Input exceeds allowed length limits.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        cursor.execute(
            """
            INSERT INTO movie_choices (movie_night_id, title, genre, reason)
            VALUES (%s, %s, %s, %s)
            """,
            (night_id, title, genre, reason),
        )
        db.commit()

        flash(f"Movie choice '{title}' added to the ballot!", "success")
        return redirect(url_for("detail", night_id=night_id))

    finally:
        cursor.close()


@app.route("/night/<int:night_id>/vote", methods=["POST"])
@login_required
def vote(night_id: int):
    """
    Cast or replace a vote for a candidate film choice.

    Guarantees:
        - Exactly 1 vote per attendee per movie night.
        - Re-voting replaces the previous choice using MySQL's `ON DUPLICATE KEY UPDATE`.
        - Verifies that the voted choice belongs strictly to the target movie night.
        - Rejects vote submissions if the night has been finalized.
    """
    db = database.get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM movie_nights WHERE id = %s LIMIT 1", (night_id,))
        night = cursor.fetchone()

        if night is None:
            abort(404)

        if night["is_finalized"]:
            flash("Voting has closed because this movie night has been finalized.", "warning")
            return redirect(url_for("detail", night_id=night_id))

        choice_id_raw = request.form.get("choice_id")
        try:
            choice_id = int(choice_id_raw)
        except (ValueError, TypeError):
            flash("Invalid movie choice selected.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        # Verification: Ensure choice belongs to this specific movie night
        cursor.execute(
            "SELECT * FROM movie_choices WHERE id = %s AND movie_night_id = %s LIMIT 1",
            (choice_id, night_id),
        )
        choice = cursor.fetchone()

        if choice is None:
            flash("Selected choice does not belong to this movie night.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        user_id = session["user_id"]

        # MySQL Upsert: Insert or replace vote atomically
        cursor.execute(
            """
            INSERT INTO votes (user_id, movie_night_id, choice_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE choice_id = VALUES(choice_id)
            """,
            (user_id, night_id, choice_id),
        )
        db.commit()

        flash(f"Your vote for '{choice['title']}' has been recorded!", "success")
        return redirect(url_for("detail", night_id=night_id))

    finally:
        cursor.close()


@app.route("/night/<int:night_id>/finalize", methods=["POST"])
@login_required
def finalize_night(night_id: int):
    """
    Finalize and crown the winning movie selection.

    Business Rules:
        - Host only (creator_id == session['user_id']).
        - At least 2 candidate choices must exist on the ballot.
        - Selected winning choice must belong to this movie night.
        - Sets `is_finalized = 1` and locks voting permanently.
    """
    db = database.get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM movie_nights WHERE id = %s LIMIT 1", (night_id,))
        night = cursor.fetchone()

        if night is None:
            abort(404)

        # Host ownership check
        if night["creator_id"] != session["user_id"]:
            flash("Only the host can finalize this movie night.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        if night["is_finalized"]:
            flash("This movie night has already been finalized.", "info")
            return redirect(url_for("detail", night_id=night_id))

        # Enforce minimum of 2 choices for democratic validity
        cursor.execute(
            "SELECT COUNT(*) AS choice_count FROM movie_choices WHERE movie_night_id = %s",
            (night_id,),
        )
        choices_count = cursor.fetchone()["choice_count"]

        if choices_count < 2:
            flash("Cannot finalize a movie night with fewer than two choices.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        final_choice_id_raw = request.form.get("final_choice_id")
        try:
            final_choice_id = int(final_choice_id_raw)
        except (ValueError, TypeError):
            flash("Please select a valid winning movie choice.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        # Validate that winning choice belongs to this night
        cursor.execute(
            "SELECT * FROM movie_choices WHERE id = %s AND movie_night_id = %s LIMIT 1",
            (final_choice_id, night_id),
        )
        winning_choice = cursor.fetchone()

        if winning_choice is None:
            flash("Selected winning choice does not belong to this movie night.", "danger")
            return redirect(url_for("detail", night_id=night_id))

        # Finalize and lock the movie night
        cursor.execute(
            """
            UPDATE movie_nights
            SET is_finalized = 1, final_choice_id = %s
            WHERE id = %s
            """,
            (final_choice_id, night_id),
        )
        db.commit()

        flash(
            f"🏆 '{winning_choice['title']}' is crowned the winner! Voting is now closed.",
            "success",
        )
        return redirect(url_for("detail", night_id=night_id))

    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# User Activity: My Nights Route
# ---------------------------------------------------------------------------
@app.route("/my-nights")
@login_required
def my_nights():
    """
    Display events hosted by the logged-in user and events they participated in.

    Queries:
        1. Hosted nights: Filtered by `creator_id = user_id`.
        2. Voted nights: Joined across `votes`, `movie_nights`, and `movie_choices`
           to display the exact film the user voted for.
    """
    user_id = session["user_id"]
    db = database.get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Nights hosted by user
        cursor.execute(
            """
            SELECT m.*, u.name AS creator_name
            FROM movie_nights m
            JOIN users u ON m.creator_id = u.id
            WHERE m.creator_id = %s
            ORDER BY m.date DESC, m.id DESC
            """,
            (user_id,),
        )
        hosted_nights = cursor.fetchall()

        # Nights the user has voted in
        cursor.execute(
            """
            SELECT m.*, u.name AS creator_name, c.title AS choice_voted_title
            FROM votes v
            JOIN movie_nights m ON v.movie_night_id = m.id
            JOIN users u ON m.creator_id = u.id
            JOIN movie_choices c ON v.choice_id = c.id
            WHERE v.user_id = %s
            ORDER BY m.date DESC, m.id DESC
            """,
            (user_id,),
        )
        voted_nights = cursor.fetchall()

        return render_template(
            "my_nights.html",
            hosted_nights=hosted_nights,
            voted_nights=voted_nights,
        )

    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    """
    Render custom cinematic 404 Not Found error page.

    Args:
        error: The HTTPException instance.

    Returns:
        tuple: Rendered template and HTTP 404 status code.
    """
    return render_template("404.html"), 404


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Start the Flask development server
    # Note: Table creation is NOT performed here. Tables are managed in MySQL.
    app.run(debug=True, host="127.0.0.1", port=5000)
