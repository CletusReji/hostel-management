from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    # One student per room
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True) # Added
    
    room = db.relationship('Room', backref='student', uselist=False)
    complaints = db.relationship('Complaint', backref='student', lazy=True)
    rents = db.relationship('Rent', backref='student', lazy=True)
    transactions = db.relationship('Transaction', backref='student', lazy=True) # Added

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now) # Changed to Local Time (IST)
    amount = db.Column(db.Float, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(100), nullable=True) # Added
    status = db.Column(db.String(20), default='Pending') # Pending, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Rent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(20), nullable=False) # e.g., "December 2024"
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Paid, Pending
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
