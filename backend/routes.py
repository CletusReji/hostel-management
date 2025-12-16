from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app
from models import db, User, Room, Complaint, Rent, Transaction
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# --- Auth ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check vacancy status for UI
    empty_room_count = Room.query.filter_by(is_occupied=False).count()
    has_vacancy = empty_room_count > 0

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
            
    return render_template('login.html', has_vacancy=has_vacancy)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone') # Added
        
        if User.query.filter_by(username=username).first():
            flash('Username taken', 'error')
            return redirect(url_for('register'))
            
        empty_room = Room.query.filter_by(is_occupied=False).first()
        if not empty_room:
            flash('No rooms available in hostel', 'error')
            return redirect(url_for('login')) # Redirect to login if full
            
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            role='student',
            full_name=full_name,
            phone=phone
        )
        db.session.add(new_user)
        db.session.flush()
        
        empty_room.is_occupied = True
        empty_room.student_id = new_user.id
        
        db.session.commit()
        flash(f'Registered! Assigned Room {empty_room.room_number}', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Student ---
@app.route('/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))
        
    # Calculate Balance
    total_rent = sum(r.amount for r in current_user.rents)
    total_paid = sum(t.amount for t in current_user.transactions)
    balance = total_rent - total_paid
    
    return render_template('student_dashboard.html', user=current_user, balance=balance, total_paid=total_paid)

from werkzeug.utils import secure_filename
import os

@app.route('/complaint/raise', methods=['POST'])
@login_required
def raise_complaint():
    title = request.form.get('title')
    description = request.form.get('description')
    file = request.files.get('image') # Get the optional file
    
    filename = None
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        # Ensure unique name to prevent overwrite could be done here, keeping simple for now
        # Or better, prepend student id or timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{filename}"
        file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))
    
    complaint = Complaint(title=title, description=description, image_file=filename, student_id=current_user.id)
    db.session.add(complaint)
    db.session.commit()
    flash('Complaint Submitted', 'success')
    return redirect(url_for('student_dashboard'))

# --- Admin ---
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
        
    total_rooms = Room.query.count()
    occupied = Room.query.filter_by(is_occupied=True).count()
    users = User.query.filter_by(role='student').all()
    complaints = Complaint.query.all()
    
    # Calculate Pending Dues
    pending_dues = []
    for s in users:
        total_rent = sum(r.amount for r in s.rents)
        total_paid = sum(t.amount for t in s.transactions)
        balance = total_rent - total_paid
        if balance > 0:
            pending_dues.append({
                'id': s.id,
                'name': s.full_name,
                'room': s.room.room_number if s.room else 'N/A',
                'amount': balance
            })
    
    return render_template('admin_dashboard.html', 
                         total=total_rooms, 
                         occupied=occupied, 
                         users=users, 
                         complaints=complaints,
                         pending_dues=pending_dues)

@app.route('/admin/complaint/<int:id>/resolve')
@login_required
def resolve_complaint(id):
    if current_user.role == 'admin':
        c = Complaint.query.get(id)
        if c:
            c.status = 'Resolved'
            db.session.commit()
            flash('Complaint Resolved', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/rent/assign', methods=['POST'])
@login_required
def assign_rent():
    if current_user.role == 'admin':
        month_val = request.form.get('month')
        year_val = request.form.get('year')
        amount = request.form.get('amount')
        
        full_month = f"{month_val} {year_val}"
        
        students = User.query.filter_by(role='student').all()
        for s in students:
            r = Rent(month=full_month, amount=float(amount), student_id=s.id)
            db.session.add(r)
        db.session.commit()
        flash(f'Rent assigned to {len(students)} students for {full_month}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/student/<int:id>')
@login_required
def student_details(id):
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    
    student = User.query.get_or_404(id)
    
    # Calculate Balance
    total_rent = sum(r.amount for r in student.rents)
    total_paid = sum(t.amount for t in student.transactions)
    balance = total_rent - total_paid
    
    return render_template('student_details.html', student=student, balance=balance, total_rent=total_rent, total_paid=total_paid)

@app.route('/admin/student/<int:id>/pay', methods=['POST'])
@login_required
def add_payment(id):
    if current_user.role == 'admin':
        amount = request.form.get('amount')
        student = User.query.get(id)
        
        if student and amount:
            t = Transaction(amount=float(amount), student_id=student.id)
            db.session.add(t)
            db.session.commit()
            flash(f'Payment of Rs. {amount} added', 'success')
            return redirect(url_for('student_details', id=student.id))
@app.route('/student/vacate', methods=['POST'])
@login_required
def vacate_room():
    if current_user.role != 'student':
        return redirect(url_for('index'))
        
    # Check Balance
    total_rent = sum(r.amount for r in current_user.rents)
    total_paid = sum(t.amount for t in current_user.transactions)
    balance = total_rent - total_paid
    
    if balance > 0:
        flash(f'Cannot vacate. You have pending dues of Rs. {balance}', 'error')
        return redirect(url_for('student_dashboard'))
        
    # Process Vacate
    room = current_user.room
    if room:
        room.is_occupied = False
        room.student_id = None
        db.session.commit()
        
    logout_user()
    flash('Vacated successfully. Thank you!', 'success')
    return redirect(url_for('login'))
