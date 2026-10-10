# Movie Night Planner — Netflix-Inspired Cinematic Web Application

A full-stack, multipage Flask web application designed with a modern Netflix-inspired dark cinematic aesthetic, powered by Python, Flask, Jinja2, and MySQL.

---

## 1. Project Overview & Features

* **Cinematic Netflix Dark UI**: High-contrast dark palette (`#141414`), Netflix red accents (`#E50914`), hero banners, responsive cards with poster art, smooth hover animations, and subtle glow effects.
* **Pure MySQL Relational Database**: Direct database connectivity using `mysql.connector`. No runtime table creation in Python code — database tables are managed directly in MySQL.
* **Robust Authentication**: Secure user registration, login, and logout powered by Flask sessions and Werkzeug cryptographic password hashing.
* **Home & Browse Page**: Hero banner with Call-To-Action, combined title search and genre filtering (Action, Comedy, Animation, Other), and instant filter reset.
* **Democratic Voting System**: Registered attendees can cast a single vote per movie night. Selecting a different movie automatically updates/replaces their vote.
* **Creator Permissions & Controls**: Event hosts can add movie candidates, edit event details, delete their movie night, or crown the winning movie when at least 2 candidates exist.
* **Locked Finalization**: Once finalized, voting is permanently closed and a highlighted "Official Winner" spotlight banner is presented.
* **Enterprise Security**: Strict CSRF token validation on all POST requests, parameterized SQL queries preventing SQL injection, and server-side authorization checks.

---

## 2. Directory Structure

```text
C:\Flask\DAY-10_PROJECT/
├── app.py              # Main Flask application and controllers with full Docstrings
├── database.py         # MySQL connection management (no DDL/table creation)
├── requirements.txt    # Python dependencies (Flask, mysql-connector-python)
├── schema.sql          # MySQL database schema script
├── seeds.sql           # Optional sample data and sample user accounts
├── .env.example        # Example environment variables template
├── README.md           # Project documentation and setup guide
├── templates/          # Jinja2 templates
│   ├── base.html       # Shared navigation, flash messages, and footer
│   ├── index.html      # Browse, search, category filter, and hero banner
│   ├── detail.html     # Movie candidates, voting, winner banner, host tools
│   ├── register.html   # Registration form
│   ├── login.html      # Authentication form
│   ├── create_night.html# Event creation form
│   ├── edit_night.html # Event update form
│   ├── my_nights.html  # User dashboard (hosted nights and voted events)
│   └── 404.html        # Custom cinematic 404 page
└── static/
    ├── style.css       # Netflix dark design system stylesheet
    └── images/         # Cinematic SVG posters and hero backgrounds
        ├── hero_bg.svg
        ├── poster_action.svg
        ├── poster_comedy.svg
        ├── poster_animation.svg
        ├── poster_other.svg
        └── default_poster.svg
```

---

## 3. Database Setup (MySQL)

### Step 1: Create Database & Tables in MySQL
Run the provided `schema.sql` script inside your MySQL client (MySQL Workbench, phpMyAdmin, or MySQL CLI):

```bash
mysql -u root -p < schema.sql
```

### Step 2 (Optional): Load Sample Data
To populate the application with sample movie nights and test users (`alex`, `sarah`, `marcus` with password `password123`):

```bash
mysql -u root -p < seeds.sql
```

---

## 4. Configuration

The application reads MySQL credentials from environment variables, falling back to local defaults:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `MYSQL_HOST` | `localhost` | MySQL Server host |
| `MYSQL_PORT` | `3306` | MySQL Server port |
| `MYSQL_USER` | `root` | Database username |
| `MYSQL_PASSWORD` | `""` | Database password |
| `MYSQL_DATABASE` | `movie_night_db` | Target database name |
| `SECRET_KEY` | *(Built-in default)* | Flask session secret key |

### Setting Environment Variables (PowerShell):
```powershell
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_mysql_password"
$env:MYSQL_DATABASE="movie_night_db"
```

---

## 5. How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Flask Server
```bash
python app.py
```

### 3. Open in Browser
Visit **`http://127.0.0.1:5000`** in your browser to experience the application.
"# Day_10_Flask_Project" 
