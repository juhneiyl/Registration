from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)
app.secret_key = 'Almazan'

db_user = os.environ.get("root")
db_password = os.environ.get("MYSQLPASSWORD")
db_host = os.environ.get("MYSQLHOST")
db_port = os.environ.get("MYSQLPORT", "3306")
db_name = os.environ.get("MYSQL_DATABASE")

# Remove placeholder text from port
if db_port and '<from' in db_port.lower():
    db_port = "3306"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MODEL
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    birthday = db.Column(db.Date, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ROUTES
@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return redirect(url_for('home'))
    
    birthday_str = request.form.get('birthday')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if password != confirm_password:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('home'))
    
    try:
        birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid birthday format!', 'error')
        return redirect(url_for('home'))
    
    existing_user = User.query.filter(
        (User.email == email)
    ).first()
    
    if existing_user:
        flash('Email already exists!', 'error')
        return redirect(url_for('home'))
    
    # Hash the password before saving
    hashed_password = generate_password_hash(password)
    
    new_user = User(
        birthday=birthday,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_password
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('success'))
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        flash('Database error occurred!', 'error')
        return redirect(url_for('home'))

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/users')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

# RUN
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
