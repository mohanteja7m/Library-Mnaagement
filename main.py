"""
===========================================================
LIBRARY MANAGEMENT SYSTEM
B.Com Computer Applications Project
Acharya Nagarjuna University
===========================================================
Author: [Your Name]
Registration No: [Your Registration Number]
Guide: [Guide's Name]
Year: 2025
===========================================================
"""

import os
import sys
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, date
import secrets
import pandas as pd
import numpy as np
from sqlalchemy import func, extract, and_, or_, desc, asc, text
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import random
import string
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import qrcode
from io import BytesIO
from werkzeug.utils import secure_filename
import tempfile
import os

# ========== APP CONFIGURATION ==========
app = Flask(__name__)
app.config['SECRET_KEY'] = 'anu-bcom-ca-project-library-system-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# Create necessary directories
for directory in ['static/uploads', 'static/qrcodes', 'static/css', 'static/js', 'static/images', 'backups', 'reports']:
    os.makedirs(directory, exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'warning'

# ========== DATABASE MODELS ==========

class Member(db.Model):
    """Library Members Database Model"""
    __tablename__ = 'members'
    
    member_id = db.Column(db.Integer, primary_key=True)
    member_code = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    membership_type = db.Column(db.String(20), default='Student')
    membership_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Active')
    total_books_issued = db.Column(db.Integer, default=0)
    fine_amount = db.Column(db.Float, default=0.0)
    photo = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Member {self.member_code}: {self.full_name}>'


class Book(db.Model):
    """Books Database Model"""
    __tablename__ = 'books'
    
    book_id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    category = db.Column(db.String(50))
    genre = db.Column(db.String(50))
    edition = db.Column(db.String(20))
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    shelf_location = db.Column(db.String(50))
    price = db.Column(db.Float)
    language = db.Column(db.String(30), default='English')
    book_condition = db.Column(db.String(20), default='Good')
    description = db.Column(db.Text)
    keywords = db.Column(db.Text)
    cover_image = db.Column(db.String(200))
    date_added = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Book {self.isbn}: {self.title}>'


class Transaction(db.Model):
    """Book Transactions Database Model"""
    __tablename__ = 'transactions'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    transaction_code = db.Column(db.String(50), unique=True, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    issue_librarian = db.Column(db.String(100))
    return_librarian = db.Column(db.String(100))
    fine_amount = db.Column(db.Float, default=0.0)
    fine_paid_amount = db.Column(db.Float, default=0.0)
    transaction_status = db.Column(db.String(20), default='Issued')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    member = db.relationship('Member', backref='transactions')
    book = db.relationship('Book', backref='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.transaction_code}>'


class Librarian(UserMixin, db.Model):
    """Library Staff Database Model"""
    __tablename__ = 'librarians'
    
    librarian_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    role = db.Column(db.String(20), default='Junior Librarian')
    shift_timing = db.Column(db.String(50))
    last_login = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.librarian_id)
    
    def __repr__(self):
        return f'<Librarian {self.username}: {self.full_name}>'


class Category(db.Model):
    """Book Categories Database Model"""
    __tablename__ = 'categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), unique=True, nullable=False)
    parent_category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    description = db.Column(db.Text)
    total_books = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.category_name}>'


class Fine(db.Model):
    """Fines Database Model"""
    __tablename__ = 'fines'
    
    fine_id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.transaction_id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id'), nullable=False)
    fine_amount = db.Column(db.Float, nullable=False)
    fine_date = db.Column(db.Date, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0)
    payment_date = db.Column(db.Date)
    payment_mode = db.Column(db.String(20), default='Cash')
    fine_status = db.Column(db.String(20), default='Pending')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transaction = db.relationship('Transaction', backref='fines')
    member = db.relationship('Member', backref='fines')
    
    def __repr__(self):
        return f'<Fine {self.fine_id}: ₹{self.fine_amount}>'


@login_manager.user_loader
def load_user(user_id):
    return Librarian.query.get(int(user_id))


# ========== UTILITY FUNCTIONS ==========

def generate_transaction_code():
    """Generate unique transaction code"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TRN{timestamp}{random_str}"


def generate_member_code():
    """Generate unique member code"""
    timestamp = date.today().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"MEM{timestamp}{random_str}"


def calculate_fine(due_date, return_date=None):
    """Calculate fine for overdue books"""
    if not return_date:
        return_date = date.today()
    
    if return_date <= due_date:
        return 0.0
    
    days_late = (return_date - due_date).days
    return days_late * 2.0  # ₹2 per day


def init_database():
    """Initialize database with sample data"""
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create admin user if not exists
            if not Librarian.query.filter_by(username='admin').first():
                admin = Librarian(
                    username='admin',
                    full_name='System Administrator',
                    email='admin@library.com',
                    phone='9876543210',
                    role='Admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                print("✅ Admin user created: username=admin, password=admin123")
            
            # Create junior librarian
            if not Librarian.query.filter_by(username='librarian').first():
                librarian = Librarian(
                    username='librarian',
                    full_name='Library Intern',
                    email='iaswaryadurga256@gmail.com',
                    phone='9876543211',
                    role='Assistant Librarian'
                )
                librarian.set_password('librarian123')
                db.session.add(librarian)
                print("✅ Librarian user created: username=librarian, password=librarian123")
            
            # Create default categories
            default_categories = [
                ('Fiction', 'Novels, short stories, poetry'),
                ('Non-Fiction', 'Biographies, history, science'),
                ('Science', 'Physics, Chemistry, Biology'),
                ('Mathematics', 'Algebra, Calculus, Statistics'),
                ('Computer Science', 'Programming, Databases, Networks'),
                ('Literature', 'Classic literature and criticism'),
                ('History', 'World history, Indian history'),
                ('Biography', 'Autobiographies and biographies'),
                ('Reference', 'Dictionaries, encyclopedias'),
                ('Children', 'Books for children and young adults'),
                ('Business', 'Management, Finance, Marketing'),
                ('Art', 'Fine arts, photography, design'),
                ('Religion', 'Religious texts and studies'),
                ('Philosophy', 'Philosophical works'),
                ('Travel', 'Travel guides and memoirs'),
                ('Cooking', 'Cookbooks and food literature'),
                ('Health', 'Health, fitness, medicine'),
                ('Sports', 'Sports and games')
            ]
            
            for cat_name, desc in default_categories:
                if not Category.query.filter_by(category_name=cat_name).first():
                    category = Category(category_name=cat_name, description=desc)
                    db.session.add(category)
            
            # Add sample books if none exist
            if Book.query.count() == 0:
                sample_books = [
                    Book(
                        isbn='978-0134685991',
                        title='Effective Python: 90 Specific Ways to Write Better Python',
                        author='Brett Slatkin',
                        publisher='Addison-Wesley',
                        publication_year=2019,
                        category='Computer Science',
                        genre='Programming',
                        edition='2nd',
                        total_copies=5,
                        available_copies=5,
                        price=45.99,
                        shelf_location='CS-A-12',
                        language='English',
                        book_condition='New',
                        description='A comprehensive guide to writing effective Python code',
                        keywords='python, programming, best practices',
                        date_added=date.today(),
                        status='Available'
                    ),
                    Book(
                        isbn='978-1492056355',
                        title='Python Crash Course: A Hands-On, Project-Based Introduction to Programming',
                        author='Eric Matthes',
                        publisher='No Starch Press',
                        publication_year=2019,
                        category='Computer Science',
                        genre='Programming',
                        edition='2nd',
                        total_copies=3,
                        available_copies=3,
                        price=39.95,
                        shelf_location='CS-B-08',
                        language='English',
                        book_condition='Good',
                        description='A fast-paced, no-nonsense guide to programming in Python',
                        keywords='python, beginner, programming',
                        date_added=date.today(),
                        status='Available'
                    ),
                    Book(
                        isbn='978-0140430721',
                        title='Pride and Prejudice',
                        author='Jane Austen',
                        publisher='Penguin Classics',
                        publication_year=1813,
                        category='Literature',
                        genre='Classic',
                        edition='Reprint',
                        total_copies=4,
                        available_copies=4,
                        price=9.99,
                        shelf_location='LIT-C-05',
                        language='English',
                        book_condition='Good',
                        description='A classic novel of manners published in 1813',
                        keywords='classic, romance, novel',
                        date_added=date.today(),
                        status='Available'
                    )
                ]
                db.session.add_all(sample_books)
                print("✅ Sample books added")
            
            # Add sample members if none exist
            if Member.query.count() == 0:
                membership_date = date(2025, 8, 5)
                sample_members = [
                    Member(
                        member_code=generate_member_code(),
                        full_name='Sai Iaswarya Durga',
                        email='iashwarydurge345@gmail.com',
                        phone='9874513245',
                        address='Atapaka Kaikaluru',
                        membership_type='Student',
                        membership_date=membership_date,
                        expiry_date=membership_date + timedelta(days=365),
                        status='Active',
                        total_books_issued=0,
                        fine_amount=0.0
                        )
                    ]
                db.session.add_all(sample_members)
                print(f"✅ Sample member added: Sai Iaswarya Durga (Member since: {membership_date})")
            
            try:
                db.session.commit()
                print("✅ Database initialized successfully!")
                
                # Get statistics
                total_books = Book.query.count()
                total_members = Member.query.filter_by(status='Active').count()
                print(f"📊 Statistics: {total_books} books, {total_members} members")
                
            except Exception as e:
                db.session.rollback()
                print(f"⚠️  Warning: Could not commit all changes: {e}")
                print("⚠️  Some data may not have been added, but system is functional.")
                
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("⚠️  Continuing with existing database...")


# ========== CONTEXT PROCESSORS ==========

@app.context_processor
def inject_globals():
    """Inject global variables into all templates"""
    try:
        stats = {
            'total_books': Book.query.count(),
            'total_members': Member.query.filter_by(status='Active').count(),
            'issued_books': Transaction.query.filter_by(transaction_status='Issued').count(),
            'overdue_books': Transaction.query.filter(
                Transaction.transaction_status == 'Issued',
                Transaction.due_date < date.today()
            ).count()
        }
    except:
        stats = {
            'total_books': 0,
            'total_members': 0,
            'issued_books': 0,
            'overdue_books': 0
        }
    
    return {
        'current_date': date.today(),
        'current_year': date.today().year,
        'current_time': datetime.now().strftime('%H:%M:%S'),
        'stats': stats,
        'system_name': 'Library Management System',
        'university': 'Sri Venketeswara University'
    }


# ========== SIMPLIFIED ROUTES ==========

@app.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Get some statistics for display
    try:
        stats = {
            'total_books': Book.query.count(),
            'total_members': Member.query.filter_by(status='Active').count(),
            'featured_books': Book.query.order_by(func.random()).limit(6).all()
        }
    except:
        stats = {
            'total_books': 0,
            'total_members': 0,
            'featured_books': []
        }
    
    return render_template('index.html', stats=stats)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        librarian = Librarian.query.filter_by(username=username).first()
        
        if librarian and librarian.check_password(password):
            if librarian.status != 'Active':
                flash('Your account has been deactivated. Contact administrator.', 'danger')
                return render_template('login.html')
            
            login_user(librarian, remember=remember)
            librarian.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {librarian.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page"""
    try:
        stats = {
            'total_books': Book.query.count(),
            'total_members': Member.query.filter_by(status='Active').count(),
            'issued_books': Transaction.query.filter_by(transaction_status='Issued').count(),
            'overdue_books': Transaction.query.filter(
                Transaction.transaction_status == 'Issued',
                Transaction.due_date < date.today()
            ).count(),
            'today_issues': Transaction.query.filter(
                Transaction.issue_date == date.today()
            ).count(),
            'today_returns': Transaction.query.filter(
                Transaction.return_date == date.today()
            ).count()
        }
        
        recent_transactions = Transaction.query.order_by(
            desc(Transaction.created_at)
        ).limit(10).all()
        
        recent_members = Member.query.order_by(desc(Member.created_at)).limit(5).all()
        recent_books = Book.query.order_by(desc(Book.created_at)).limit(5).all()
        overdue_books = Transaction.query.filter(
            Transaction.transaction_status == 'Issued',
            Transaction.due_date < date.today()
        ).order_by(Transaction.due_date).limit(10).all()
        
    except Exception as e:
        print(f"Error loading dashboard data: {e}")
        stats = {'total_books': 0, 'total_members': 0, 'issued_books': 0, 'overdue_books': 0,
                'today_issues': 0, 'today_returns': 0}
        recent_transactions = []
        recent_members = []
        recent_books = []
        overdue_books = []
    
    return render_template('dashboard.html',
                         stats=stats,
                         recent_transactions=recent_transactions,
                         recent_members=recent_members,
                         recent_books=recent_books,
                         overdue_books=overdue_books)


@app.route('/members', methods=['GET', 'POST'])
@login_required
def manage_members():
    """Manage library members"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            try:
                member = Member(
                    member_code=generate_member_code(),
                    full_name=request.form.get('full_name'),
                    email=request.form.get('email'),
                    phone=request.form.get('phone'),
                    address=request.form.get('address'),
                    membership_type=request.form.get('membership_type'),
                    membership_date=date.today(),
                    expiry_date=date.today() + timedelta(days=365)
                )
                db.session.add(member)
                db.session.commit()
                flash(f'Member added successfully! Code: {member.member_code}', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding member: {str(e)}', 'danger')
        
        elif action == 'update':
            try:
                member_id = request.form.get('member_id')
                member = Member.query.get_or_404(member_id)
                
                member.full_name = request.form.get('full_name')
                member.email = request.form.get('email')
                member.phone = request.form.get('phone')
                member.address = request.form.get('address')
                member.membership_type = request.form.get('membership_type')
                member.status = request.form.get('status')
                
                db.session.commit()
                flash('Member updated successfully!', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating member: {str(e)}', 'danger')
        
        elif action == 'delete':
            try:
                member_id = request.form.get('member_id')
                member = Member.query.get_or_404(member_id)
                
                # Check for active transactions
                active_issues = Transaction.query.filter_by(
                    member_id=member_id,
                    transaction_status='Issued'
                ).count()
                
                if active_issues > 0:
                    flash(f'Cannot delete member with {active_issues} active book issues.', 'danger')
                else:
                    db.session.delete(member)
                    db.session.commit()
                    flash('Member deleted successfully!', 'success')
                    
            except Exception as e:
                db.session.rollback()
                flash(f'Error deleting member: {str(e)}', 'danger')
    
    # Get all members
    members = Member.query.order_by(desc(Member.created_at)).all()
    return render_template('members.html', members=members)

@app.route('/api/members/<int:member_id>')
@login_required
def api_member_details(member_id):
    """API: Get member details"""
    try:
        member = Member.query.get_or_404(member_id)
        
        return jsonify({
            'success': True,
            'member': {
                'id': member.member_id,
                'member_code': member.member_code,
                'full_name': member.full_name,
                'email': member.email,
                'phone': member.phone,
                'address': member.address,
                'membership_type': member.membership_type,
                'membership_date': member.membership_date.strftime('%Y-%m-%d'),
                'expiry_date': member.expiry_date.strftime('%Y-%m-%d') if member.expiry_date else None,
                'status': member.status,
                'total_books_issued': member.total_books_issued,
                'fine_amount': float(member.fine_amount or 0)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/books', methods=['GET', 'POST'])
@login_required
def manage_books():
    """Manage library books"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            try:
                book = Book(
                    isbn=request.form.get('isbn'),
                    title=request.form.get('title'),
                    author=request.form.get('author'),
                    publisher=request.form.get('publisher'),
                    publication_year=request.form.get('publication_year'),
                    category=request.form.get('category'),
                    genre=request.form.get('genre'),
                    edition=request.form.get('edition'),
                    total_copies=int(request.form.get('total_copies', 1)),
                    available_copies=int(request.form.get('total_copies', 1)),
                    price=float(request.form.get('price', 0) or 0),
                    shelf_location=request.form.get('shelf_location'),
                    language=request.form.get('language', 'English'),
                    book_condition=request.form.get('book_condition', 'Good'),
                    description=request.form.get('description'),
                    keywords=request.form.get('keywords'),
                    date_added=date.today(),
                    status='Available'
                )
                db.session.add(book)
                db.session.commit()
                flash('Book added successfully!', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding book: {str(e)}', 'danger')
        
        elif action == 'update':
            try:
                book_id = request.form.get('book_id')
                book = Book.query.get_or_404(book_id)
                
                book.isbn = request.form.get('isbn')
                book.title = request.form.get('title')
                book.author = request.form.get('author')
                book.publisher = request.form.get('publisher')
                book.publication_year = request.form.get('publication_year')
                book.category = request.form.get('category')
                book.genre = request.form.get('genre')
                book.edition = request.form.get('edition')
                book.price = float(request.form.get('price', 0) or 0)
                book.shelf_location = request.form.get('shelf_location')
                book.language = request.form.get('language')
                book.book_condition = request.form.get('book_condition')
                book.description = request.form.get('description')
                book.keywords = request.form.get('keywords')
                book.status = request.form.get('status')
                
                db.session.commit()
                flash('Book updated successfully!', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating book: {str(e)}', 'danger')
        
        elif action == 'delete':
            try:
                book_id = request.form.get('book_id')
                book = Book.query.get_or_404(book_id)
                
                # Check for active transactions
                active_issues = Transaction.query.filter_by(
                    book_id=book_id,
                    transaction_status='Issued'
                ).count()
                
                if active_issues > 0:
                    flash(f'Cannot delete book with {active_issues} active issues.', 'danger')
                else:
                    db.session.delete(book)
                    db.session.commit()
                    flash('Book deleted successfully!', 'success')
                    
            except Exception as e:
                db.session.rollback()
                flash(f'Error deleting book: {str(e)}', 'danger')
    
    # Get all books and categories
    books = Book.query.order_by(desc(Book.created_at)).all()
    categories = Category.query.order_by(Category.category_name).all()
    
    return render_template('books.html', books=books, categories=categories)


@app.route('/issue_book', methods=['GET', 'POST'])
@login_required
def issue_book():
    """Issue books to members"""
    if request.method == 'POST':
        try:
            member_id = request.form.get('member_id')
            book_id = request.form.get('book_id')
            days = int(request.form.get('days', 14))
            
            member = Member.query.get_or_404(member_id)
            book = Book.query.get_or_404(book_id)
            
            # Validations
            if member.status != 'Active':
                flash(f'Member {member.full_name} is not active.', 'danger')
                return redirect(url_for('issue_book'))
            
            if book.available_copies <= 0:
                flash(f'Book "{book.title}" is not available.', 'danger')
                return redirect(url_for('issue_book'))
            
            # Check if member already has this book
            existing_issue = Transaction.query.filter_by(
                member_id=member_id,
                book_id=book_id,
                transaction_status='Issued'
            ).first()
            
            if existing_issue:
                flash(f'Member already has this book issued.', 'warning')
                return redirect(url_for('issue_book'))
            
            # Create transaction
            transaction = Transaction(
                transaction_code=generate_transaction_code(),
                member_id=member_id,
                book_id=book_id,
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=days),
                issue_librarian=current_user.full_name,
                transaction_status='Issued',
                notes=request.form.get('notes')
            )
            
            # Update book
            book.available_copies -= 1
            if book.available_copies == 0:
                book.status = 'Issued'
            
            # Update member
            member.total_books_issued += 1
            
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'Book issued successfully! Transaction ID: {transaction.transaction_code}', 'success')
            return redirect(url_for('issue_book'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error issuing book: {str(e)}', 'danger')
            return redirect(url_for('issue_book'))
    
    # GET request
    members = Member.query.filter_by(status='Active').order_by(Member.full_name).all()
    books = Book.query.filter(Book.available_copies > 0).order_by(Book.title).all()
    
    today_issues = Transaction.query.filter(
        Transaction.issue_date == date.today()
    ).order_by(desc(Transaction.created_at)).limit(10).all()
    
    return render_template('issue_book.html', members=members, books=books, today_issues=today_issues)


@app.route('/return_book', methods=['GET', 'POST'])
@login_required
def return_book():
    """Return issued books"""
    if request.method == 'POST':
        try:
            transaction_code = request.form.get('transaction_code')
            transaction = Transaction.query.filter_by(
                transaction_code=transaction_code,
                transaction_status='Issued'
            ).first()
            
            if not transaction:
                flash('Invalid transaction code or book already returned.', 'danger')
                return redirect(url_for('return_book'))
            
            # Calculate fine
            fine_amount = calculate_fine(transaction.due_date, date.today())
            
            # Update transaction
            transaction.return_date = date.today()
            transaction.return_librarian = current_user.full_name
            transaction.fine_amount = fine_amount
            transaction.transaction_status = 'Returned'
            
            # Update book
            book = Book.query.get(transaction.book_id)
            book.available_copies += 1
            book.status = 'Available'
            
            # Update member fine
            if fine_amount > 0:
                member = Member.query.get(transaction.member_id)
                member.fine_amount += fine_amount
                
                # Create fine record
                fine = Fine(
                    transaction_id=transaction.transaction_id,
                    member_id=transaction.member_id,
                    fine_amount=fine_amount,
                    fine_date=date.today(),
                    fine_status='Pending',
                    description=f'Late return for book: {book.title}'
                )
                db.session.add(fine)
            
            db.session.commit()
            
            message = f'Book returned successfully!'
            if fine_amount > 0:
                message += f' Fine: ₹{fine_amount:.2f}'
            flash(message, 'success')
            
            return redirect(url_for('return_book'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error returning book: {str(e)}', 'danger')
            return redirect(url_for('return_book'))
    
    # GET request - fix the queries to use proper joins
    today_returns = Transaction.query.filter(
        Transaction.return_date == date.today()
    ).order_by(desc(Transaction.created_at)).all()
    
    overdue_books = Transaction.query.filter(
        Transaction.transaction_status == 'Issued',
        Transaction.due_date < date.today()
    ).order_by(Transaction.due_date).all()
    
    return render_template('return_book.html',
                         today_returns=today_returns,
                         overdue_books=overdue_books)

@app.route('/api/transactions/<transaction_code>')
@login_required
def api_transaction_details(transaction_code):
    """API: Get transaction details by transaction code"""
    try:
        transaction = Transaction.query.filter_by(transaction_code=transaction_code).first()
        
        if not transaction:
            return jsonify({
                'success': False, 
                'error': 'Transaction not found'
            }), 404
        
        if transaction.transaction_status != 'Issued':
            return jsonify({
                'success': False, 
                'error': 'This book has already been returned'
            }), 400
        
        # Calculate overdue days and fine
        today = date.today()
        days_overdue = 0
        fine_amount = 0.0
        
        if today > transaction.due_date:
            days_overdue = (today - transaction.due_date).days
            fine_amount = days_overdue * 2.0  # ₹2 per day
        
        return jsonify({
            'success': True,
            'transaction': {
                'transaction_code': transaction.transaction_code,
                'member_name': transaction.member.full_name,
                'member_code': transaction.member.member_code,
                'book_title': transaction.book.title,
                'book_isbn': transaction.book.isbn,
                'issue_date': transaction.issue_date.strftime('%d/%m/%Y'),
                'due_date': transaction.due_date.strftime('%d/%m/%Y'),
                'status': transaction.transaction_status,
                'days_overdue': days_overdue,
                'fine_amount': fine_amount
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500




@app.route('/search')
@login_required
def search():
    """Search books"""
    query = request.args.get('q', '')
    search_by = request.args.get('search_by', 'title')
    category = request.args.get('category', '')
    available_only = request.args.get('available_only') == 'on'
    sort_by = request.args.get('sort_by', 'title')
    
    # Get categories
    categories = Category.query.order_by(Category.category_name).all()
    
    if not query:
        return render_template('search.html',
                             results=[],
                             query=query,
                             search_by=search_by,
                             categories=categories,
                             selected_category=category,
                             available_only=available_only,
                             sort_by=sort_by)
    
    # Search books
    if search_by in ['title', 'author', 'isbn', 'publisher', 'category']:
        results = Book.query
        
        if search_by == 'title':
            results = results.filter(Book.title.ilike(f'%{query}%'))
        elif search_by == 'author':
            results = results.filter(Book.author.ilike(f'%{query}%'))
        elif search_by == 'isbn':
            results = results.filter(Book.isbn.ilike(f'%{query}%'))
        elif search_by == 'publisher':
            results = results.filter(Book.publisher.ilike(f'%{query}%'))
        elif search_by == 'category':
            results = results.filter(Book.category.ilike(f'%{query}%'))
        
        # Apply filters
        if category:
            results = results.filter(Book.category == category)
        
        if available_only:
            results = results.filter(Book.available_copies > 0)
        
        # Apply sorting
        if sort_by == 'title':
            results = results.order_by(Book.title.asc())
        elif sort_by == 'title_desc':
            results = results.order_by(Book.title.desc())
        elif sort_by == 'author':
            results = results.order_by(Book.author.asc())
        elif sort_by == 'year_desc':
            results = results.order_by(desc(Book.publication_year))
        elif sort_by == 'year_asc':
            results = results.order_by(Book.publication_year.asc())
        elif sort_by == 'price_desc':
            results = results.order_by(desc(Book.price))
        elif sort_by == 'price_asc':
            results = results.order_by(Book.price.asc())
        
        results = results.all()
        
        return render_template('search.html',
                             results=results,
                             query=query,
                             search_by=search_by,
                             categories=categories,
                             selected_category=category,
                             available_only=available_only,
                             sort_by=sort_by)
    
    return render_template('search.html', results=[], query=query)


@app.route('/reports')
@login_required
def reports():
    """Generate reports"""
    try:
        # Get statistics
        total_books = Book.query.count()
        total_members = Member.query.filter_by(status='Active').count()
        total_issued = Transaction.query.filter_by(transaction_status='Issued').count()
        total_returned = Transaction.query.filter_by(transaction_status='Returned').count()
        
        # Overdue transactions
        overdue_transactions = Transaction.query.filter(
            Transaction.transaction_status == 'Issued',
            Transaction.due_date < date.today()
        ).order_by(Transaction.due_date).all()
        
        # Category distribution
        category_data = db.session.query(
            Book.category, func.count(Book.book_id).label('count')
        ).group_by(Book.category).all()
        
        # Popular books (simplified)
        popular_books = Book.query.order_by(desc(Book.total_copies)).limit(10).all()
        
        # Top members
        top_members = Member.query.order_by(desc(Member.total_books_issued)).limit(10).all()
        
        # Fines
        fines = Fine.query.order_by(desc(Fine.fine_date)).limit(20).all()
        
        stats = {
            'total_books': total_books,
            'total_members': total_members,
            'total_issued': total_issued,
            'total_returned': total_returned,
            'total_fine': db.session.query(func.sum(Fine.fine_amount)).scalar() or 0
        }
        
        return render_template('reports.html',
                             stats=stats,
                             category_data=category_data,
                             overdue_transactions=overdue_transactions,
                             popular_books=popular_books,
                             top_members=top_members,
                             fines=fines)
        
    except Exception as e:
        print(f"Error generating reports: {e}")
        stats = {'total_books': 0, 'total_members': 0, 'total_issued': 0, 'total_returned': 0, 'total_fine': 0}
        return render_template('reports.html',
                             stats=stats,
                             category_data=[],
                             overdue_transactions=[],
                             popular_books=[],
                             top_members=[],
                             fines=[])


@app.route('/export/<data_type>')
@login_required
def export_data(data_type):
    """Export data to Excel"""
    try:
        if data_type == 'books':
            books = Book.query.all()
            data = [{
                'ISBN': b.isbn,
                'Title': b.title,
                'Author': b.author,
                'Publisher': b.publisher,
                'Year': b.publication_year,
                'Category': b.category,
                'Total Copies': b.total_copies,
                'Available Copies': b.available_copies,
                'Price': b.price,
                'Status': b.status
            } for b in books]
            filename = f'books_export_{date.today()}.xlsx'
            
        elif data_type == 'members':
            members = Member.query.all()
            data = [{
                'Member Code': m.member_code,
                'Full Name': m.full_name,
                'Email': m.email,
                'Phone': m.phone,
                'Membership Type': m.membership_type,
                'Status': m.status,
                'Books Issued': m.total_books_issued,
                'Fine Amount': m.fine_amount
            } for m in members]
            filename = f'members_export_{date.today()}.xlsx'
        
        elif data_type == 'transactions':
            transactions = Transaction.query.all()
            data = [{
                'Transaction Code': t.transaction_code,
                'Member': t.member.full_name,
                'Book': t.book.title,
                'Issue Date': t.issue_date,
                'Due Date': t.due_date,
                'Return Date': t.return_date,
                'Status': t.transaction_status,
                'Fine Amount': t.fine_amount
            } for t in transactions]
            filename = f'transactions_export_{date.today()}.xlsx'
        
        else:
            flash('Invalid export type', 'danger')
            return redirect(url_for('reports'))
        
        # Create DataFrame and Excel file
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
        
        output.seek(0)
        
        return send_file(output,
                         download_name=filename,
                         as_attachment=True,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'danger')
        return redirect(url_for('reports'))


@app.route('/api/books/<int:book_id>')
@login_required
def api_book_details(book_id):
    """API: Get book details"""
    try:
        book = Book.query.get_or_404(book_id)
        
        return jsonify({
            'success': True,
            'book': {
                'id': book.book_id,
                'isbn': book.isbn,
                'title': book.title,
                'author': book.author,
                'publisher': book.publisher,
                'year': book.publication_year,
                'category': book.category,
                'total_copies': book.total_copies,
                'available_copies': book.available_copies,
                'price': book.price,
                'shelf_location': book.shelf_location,
                'status': book.status
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/import_books', methods=['GET', 'POST'])
@login_required
def import_books():
    """Bulk import books from Excel/CSV file"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})
            
            # Validate file extension
            allowed_extensions = {'csv', 'xlsx', 'xls'}
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_ext not in allowed_extensions:
                return jsonify({'success': False, 'message': 'Invalid file format. Use CSV or Excel.'})
            
            # Save uploaded file temporarily
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, filename)
            file.save(file_path)
            
            # Read file based on extension
            try:
                if file_ext == 'csv':
                    df = pd.read_csv(file_path)
                else:  # Excel files
                    df = pd.read_excel(file_path)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error reading file: {str(e)}'})
            
            # Validate required columns
            required_columns = ['isbn', 'title', 'author']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return jsonify({
                    'success': False, 
                    'message': f'Missing required columns: {", ".join(missing_columns)}'
                })
            
            # Get import options
            import_mode = request.form.get('import_mode', 'add')
            default_category = request.form.get('default_category')
            skip_errors = request.form.get('skip_errors') == 'on'
            
            # Process each row
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Prepare book data
                    isbn = str(row.get('isbn', '')).strip()
                    title = str(row.get('title', '')).strip()
                    author = str(row.get('author', '')).strip()
                    
                    # Skip if required fields are empty
                    if not all([isbn, title, author]):
                        error_count += 1
                        errors.append(f"Row {index+2}: Missing required fields")
                        if not skip_errors:
                            break
                        continue
                    
                    # Check if book already exists
                    existing_book = Book.query.filter_by(isbn=isbn).first()
                    
                    if import_mode == 'add' and existing_book:
                        error_count += 1
                        errors.append(f"Row {index+2}: ISBN {isbn} already exists")
                        if not skip_errors:
                            break
                        continue
                    
                    # Prepare book data
                    book_data = {
                        'isbn': isbn,
                        'title': title,
                        'author': author,
                        'publisher': str(row.get('publisher', '')).strip() or None,
                        'publication_year': int(row.get('publication_year')) if pd.notna(row.get('publication_year')) else None,
                        'category': str(row.get('category', '')).strip() or default_category or None,
                        'genre': str(row.get('genre', '')).strip() or None,
                        'edition': str(row.get('edition', '')).strip() or None,
                        'total_copies': int(row.get('total_copies', 1)),
                        'available_copies': int(row.get('total_copies', 1)),
                        'price': float(row.get('price', 0)) if pd.notna(row.get('price')) else 0.0,
                        'shelf_location': str(row.get('shelf_location', '')).strip() or None,
                        'language': str(row.get('language', 'English')).strip() or 'English',
                        'book_condition': str(row.get('book_condition', 'Good')).strip() or 'Good',
                        'description': str(row.get('description', '')).strip() or None,
                        'keywords': str(row.get('keywords', '')).strip() or None,
                        'date_added': date.today(),
                        'status': 'Available'
                    }
                    
                    if existing_book and import_mode in ['update', 'replace']:
                        # Update existing book
                        for key, value in book_data.items():
                            if hasattr(existing_book, key) and value is not None:
                                setattr(existing_book, key, value)
                        success_count += 1
                    else:
                        # Add new book
                        book = Book(**book_data)
                        db.session.add(book)
                        success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index+2}: {str(e)}")
                    if not skip_errors:
                        break
                    continue
            
            # Commit changes
            db.session.commit()
            
            # Clean up temp file
            try:
                os.remove(file_path)
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': f'Import completed: {success_count} books processed successfully, {error_count} errors',
                'errors': errors[:10] if errors else []  # Return first 10 errors only
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Import failed: {str(e)}'})
    
    # GET request - show import page
    categories = Category.query.order_by(Category.category_name).all()
    
    # Sample recent imports for display
    recent_imports = []  # You can implement this with a new ImportLog model if needed
    
    return render_template('import.html', 
                         categories=categories, 
                         recent_imports=recent_imports)

@app.route('/api/search')
@login_required
def api_search():
    """API: Search books"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'books')
    
    if not query or len(query) < 2:
        return jsonify({'success': True, 'results': []})
    
    if search_type == 'books':
        books = Book.query.filter(
            or_(
                Book.title.ilike(f'%{query}%'),
                Book.author.ilike(f'%{query}%'),
                Book.isbn.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        results = []
        for book in books:
            results.append({
                'id': book.book_id,
                'title': book.title,
                'author': book.author,
                'isbn': book.isbn,
                'available': book.available_copies > 0,
                'available_copies': book.available_copies,
                'category': book.category
            })
        
        return jsonify({'success': True, 'results': results})
    
    elif search_type == 'members':
        members = Member.query.filter(
            or_(
                Member.full_name.ilike(f'%{query}%'),
                Member.email.ilike(f'%{query}%'),
                Member.member_code.ilike(f'%{query}%')
            )
        ).filter_by(status='Active').limit(10).all()
        
        results = []
        for member in members:
            results.append({
                'id': member.member_id,
                'name': member.full_name,
                'email': member.email,
                'member_code': member.member_code,
                'phone': member.phone
            })
        
        return jsonify({'success': True, 'results': results})
    
    return jsonify({'success': False, 'error': 'Invalid search type'}), 400


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def page_not_found(e):
    """404 Error handler"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """500 Error handler"""
    return render_template('500.html'), 500


@app.errorhandler(403)
def forbidden(e):
    """403 Error handler"""
    return render_template('403.html'), 403


@app.errorhandler(401)
def unauthorized(e):
    """401 Error handler"""
    flash('Please login to access this page.', 'warning')
    return redirect(url_for('login'))


# ========== MAIN APPLICATION ==========

def print_banner():
    """Print application banner"""
    banner = """
    ===========================================================
    LIBRARY MANAGEMENT SYSTEM v2.0
    B.Com Computer Applications Project
    Acharya Nagarjuna University
    ===========================================================
    """
    print(banner)


if __name__ == '__main__':
    print_banner()
    
    print("🔧 Initializing database...")
    init_database()
    
    print("\n🌐 STARTING SERVER...")
    print(f"   • URL: http://localhost:5000")
    print(f"   • Admin Login: admin / admin123")
    print(f"   • Librarian Login: librarian / librarian123")
    
    print("\n" + "=" * 60)
    print("Server is running. Press Ctrl+C to stop.")
    print("=" * 60 + "\n")
    
    # Run application
    app.run(debug=True, host='0.0.0.0', port=5000)
