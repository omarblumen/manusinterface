#!/bin/bash
# This is a simple deployment script for the Assistant App
# For production use, consider using a proper deployment tool

cd "$(dirname "$0")"

echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setting up the database..."
python -c "from app import db; db.create_all()"

echo "Starting the application..."
gunicorn -w 4 -b 0.0.0.0:8000 app:app
