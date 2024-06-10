import json
import uuid

class User:
    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password = password
        self.is_admin = is_admin

    def check_password(self, password):
        return self.password == password

class Book:
    def __init__(self, title, yearlevel, course, description, pdf, folder=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.yearlevel = yearlevel
        self.course = course
        self.description = description
        self.pdf = pdf
        self.folder = folder

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'yearlevel': self.yearlevel,
            'course': self.course,
            'description': self.description,
            'pdf': self.pdf,
            'folder': self.folder
        }

class Folder:
    def __init__(self, name):
        self.name = name
        self.books = []

    def to_dict(self):
        return {
            'name': self.name,
            'books': [book.to_dict() for book in self.books]
        }

def load_users():
    try:
        with open('users.json', 'r') as f:
            return [User(**user) for user in json.load(f)]
    except FileNotFoundError:
        return []

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump([user.__dict__ for user in users], f)

def load_books():
    try:
        with open('books.json', 'r') as f:
            return [Book(**book) for book in json.load(f)]
    except FileNotFoundError:
        return []

def save_books(books):
    with open('books.json', 'w') as f:
        json.dump([book.to_dict() for book in books], f)

def load_folders():
    try:
        with open('folders.json', 'r') as f:
            return [Folder(**folder) for folder in json.load(f)]
    except FileNotFoundError:
        return []

def save_folders(folders):
    with open('folders.json', 'w') as f:
        json.dump([folder.to_dict() for folder in folders], f)
