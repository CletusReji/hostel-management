@echo off

echo Starting Hostel Management System...
echo Open your browser to http://127.0.0.1:5000/
start http://127.0.0.1:5000/

cd backend
python app.py
pause
