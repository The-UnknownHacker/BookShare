import json
import os
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class User:
    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.is_admin = is_admin

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'username': self.username,
            'password': self.password,
            'is_admin': self.is_admin
        }

class Book:
    def __init__(self, title, yearlevel, course, description, pdf):
        self.title = title
        self.yearlevel = yearlevel
        self.course = course
        self.description = description
        self.pdf = pdf

    def to_dict(self):
        return {
            'title': self.title,
            'yearlevel': self.yearlevel,
            'course': self.course,
            'description': self.description,
            'pdf': self.pdf
        }

# Load users from JSON file
def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            users_data = json.load(f)
            return [User(**user) for user in users_data]
    return []

# Save users to JSON file
def save_users(users):
    with open('users.json', 'w') as f:
        json.dump([user.to_dict() for user in users], f)

# Load books from JSON file
def load_books():
    if os.path.exists('books.json'):
        with open('books.json', 'r') as f:
            books_data = json.load(f)
            return [Book(**book) for book in books_data]
    return []

# Save books to JSON file
def save_books(books):
    with open('books.json', 'w') as f:
        json.dump([book.to_dict() for book in books], f)
