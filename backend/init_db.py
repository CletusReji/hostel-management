from app import app, db
from models import User, Room
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Create Tables
        db.create_all()
        
        # Create Admin
        if not User.query.filter_by(username='admin').first():
            print("Creating admin user...")
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin',
                full_name='System Administrator'
            )
            db.session.add(admin)
        
        # Create Rooms
        if Room.query.count() == 0:
            print("Creating 50 rooms...")
            for i in range(1, 51):
                room = Room(room_number=100 + i) # 101 to 150
                db.session.add(room)
        
        db.session.commit()
        print("Database initialized locally!")

if __name__ == '__main__':
    init_db()
