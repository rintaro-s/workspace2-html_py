@echo off
echo Starting Circle Management Platform...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Initializing database...
python -c "from app import init_database; init_database(); print('Database initialized successfully')"
echo.
echo Starting server on http://localhost:8060
echo Press Ctrl+C to stop the server
echo.
python app.py
