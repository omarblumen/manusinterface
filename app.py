from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///assistant_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de OAuth
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['APPLE_CLIENT_ID'] = os.getenv('APPLE_CLIENT_ID')
app.config['APPLE_CLIENT_SECRET'] = os.getenv('APPLE_CLIENT_SECRET')

# Inicializar la base de datos
db = SQLAlchemy(app)

# Configurar el sistema de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Definir modelos de base de datos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=True)
    oauth_provider = db.Column(db.String(20), nullable=True)  # 'google', 'apple', o None
    oauth_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    conversations = db.relationship('Conversation', backref='user', lazy=True)
    todos = db.relationship('Todo', backref='user', lazy=True)
    calendar_events = db.relationship('CalendarEvent', backref='user', lazy=True)
    reminders = db.relationship('Reminder', backref='user', lazy=True)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.Integer, default=0)  # 0=normal, 1=important, 2=urgent
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    reminder_time = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rutas básicas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent conversations
    recent_conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).limit(5).all()
    
    # Get active todos
    active_todos = Todo.query.filter_by(user_id=current_user.id, completed=False).order_by(Todo.due_date).limit(5).all()
    
    # Get upcoming calendar events
    upcoming_events = CalendarEvent.query.filter_by(user_id=current_user.id).filter(CalendarEvent.start_time >= datetime.utcnow()).order_by(CalendarEvent.start_time).limit(5).all()
    
    # Get active reminders
    active_reminders = Reminder.query.filter_by(user_id=current_user.id, completed=False).order_by(Reminder.reminder_time).limit(5).all()
    
    return render_template('dashboard.html', 
                          recent_conversations=recent_conversations,
                          active_todos=active_todos,
                          upcoming_events=upcoming_events,
                          active_reminders=active_reminders)

# Rutas de OAuth
@app.route('/login/google')
def login_google():
    # En una implementación real, esto usaría la biblioteca Authlib para OAuth
    # Para simplificar, simulamos una redirección a Google
    return redirect(url_for('google_callback'))

@app.route('/login/google/callback')
def google_callback():
    # Simulación de callback de Google
    # En una implementación real, esto verificaría el token y obtendría información del usuario
    
    # Crear un usuario simulado para demostración
    email = "demo_google@example.com"
    oauth_id = "google_123456789"
    
    user = User.query.filter_by(oauth_id=oauth_id, oauth_provider='google').first()
    
    if not user:
        # Crear un nuevo usuario
        username = email.split('@')[0]
        user = User(
            username=username,
            email=email,
            oauth_provider='google',
            oauth_id=oauth_id
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('dashboard'))

@app.route('/login/apple')
def login_apple():
    # Simulación similar a Google
    return redirect(url_for('apple_callback'))

@app.route('/login/apple/callback')
def apple_callback():
    # Simulación de callback de Apple
    email = "demo_apple@example.com"
    oauth_id = "apple_123456789"
    
    user = User.query.filter_by(oauth_id=oauth_id, oauth_provider='apple').first()
    
    if not user:
        username = email.split('@')[0]
        user = User(
            username=username,
            email=email,
            oauth_provider='apple',
            oauth_id=oauth_id
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('dashboard'))

# Import routes from other files
from conversation_routes import *
from todo_routes import *
from calendar_reminder_routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
