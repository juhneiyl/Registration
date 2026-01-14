from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash
import os
import sys

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'Almazan')

# Validate and get environment variables
def get_db_config():
    """Validate and retrieve database configuration from environment variables"""
    required_vars = {
        'MYSQLUSER': os.environ.get('MYSQLUSER'),
        'MYSQLPASSWORD': os.environ.get('MYSQLPASSWORD'),
        'MYSQLHOST': os.environ.get('MYSQLHOST'),
        'MYSQLDATABASE': os.environ.get('MYSQLDATABASE')
    }
    
    # Check for missing variables
    missing_vars = [key for key, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set the following environment variables:")
        print("  - MYSQLUSER: MySQL username")
        print("  - MYSQLPASSWORD: MySQL password")
        print("  - MYSQLHOST: MySQL host address")
        print("  - MYSQLPORT: MySQL port (optional, defaults to 3306)")
        print("  - MYSQLDATABASE: MySQL database name")
        sys.exit(1)
    
    db_port = os.environ.get('MYSQLPORT', '3306')
    
    # Validate port is numeric
    try:
        int(db_port)
    except ValueError:
        print(f"ERROR: MYSQLPORT must be a number, got: {db_port}")
        sys.exit(1)
    
    return {
        'user': required_vars['MYSQLUSER'],
        'password': required_vars['MYSQLPASSWORD'],
        'host': required_vars['MYSQLHOST'],
        'port': db_port,
        'database': required_vars['MYSQLDATABASE']
    }

# Get database configuration
db_config = get_db_config()

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
    f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True,
}

db = SQLAlchemy(app)

# MODEL
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    birthday = db.Column(db.Date, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ROUTES
@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return redirect(url_for('home'))
    
    # Get form data
    birthday_str = request.form.get('birthday')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate all fields are present
    if not all([birthday_str, first_name, last_name, email, password, confirm_password]):
        flash('All fields are required!', 'error')
        return redirect(url_for('home'))
    
    # Validate passwords match
    if password != confirm_password:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('home'))
    
    # Validate birthday format
    try:
        birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Invalid birthday format!', 'error')
        return redirect(url_for('home'))
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    
    if existing_user:
        flash('Email already exists!', 'error')
        return redirect(url_for('home'))
    
    # Hash the password before saving
    hashed_password = generate_password_hash(password)
    
    # Create new user
    new_user = User(
        birthday=birthday,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_password
    )
    
    # Save to database
    try:
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('success'))
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")
        flash('Database error occurred. Please try again.', 'error')
        return redirect(url_for('home'))

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/users')
def users():
    try:
        all_users = User.query.all()
        return render_template('users.html', users=all_users)
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        flash('Error loading users.', 'error')
        return redirect(url_for('home'))

# Create tables
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")

# RUN
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
