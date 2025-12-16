from flask import Flask
from models import db, User
from flask_login import LoginManager
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hostel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes after app initialization
from routes import *
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        db.create_all()
        # Create Admin if not exists
        if not User.query.filter_by(username='admin').first():
            print("Creating Admin User (admin/admin123)")
            admin = User(
                username='admin', 
                password=generate_password_hash('admin123'),
                role='admin',
                full_name='System Administrator'
            )
            db.session.add(admin)
            
        # Create Rooms
        if Room.query.count() == 0:
            print("Creating 5 Rooms (Test Mode)")
            for i in range(1, 6):
                db.session.add(Room(room_number=100+i))
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
