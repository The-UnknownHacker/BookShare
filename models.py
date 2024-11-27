from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    yearlevel = db.Column(db.String(50))
    course = db.Column(db.String(100))
    description = db.Column(db.Text)
    pdf = db.Column(db.String(200))
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, title, yearlevel, course, description, pdf, folder=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.yearlevel = yearlevel
        self.course = course
        self.description = description
        self.pdf = pdf
        if folder:
            self.folder_id = folder.id

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    books = db.relationship('Book', backref='folder', lazy=True)
    subfolders = db.relationship(
        'Folder',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )

    def get_all_books(self):
        """Get all books from this folder and its subfolders"""
        all_books = self.books[:]
        for subfolder in self.subfolders:
            all_books.extend(subfolder.get_all_books())
        return all_books

class PDFPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.String(36), db.ForeignKey('book.id'), nullable=False)
    page = db.Column(db.Integer, default=1)
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_user_book'),)

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    theme = db.Column(db.String(10), default='light')  # 'light' or 'dark'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    __table_args__ = (db.UniqueConstraint('user_id', name='unique_user_settings'),)
