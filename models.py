import json

class User:
    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password = password
        self.is_admin = is_admin

    def check_password(self, password):
        return self.password == password

class Book:
    def __init__(self, title, yearlevel, course, description, pdf, folder=None):
        self.title = title
        self.yearlevel = yearlevel
        self.course = course
        self.description = description
        self.pdf = pdf
        self.folder = folder

class Folder:
    def __init__(self, name, books=None):
        self.name = name
        self.books = books if books is not None else []

    def __str__(self):
        return self.name

def load_users():
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
            return [User(**user) for user in users]
    except FileNotFoundError:
        return []

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump([user.__dict__ for user in users], f)

def load_books():
    try:
        with open('books.json', 'r') as f:
            books_data = json.load(f)
            return [Book(**book) for book in books_data]
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_books(books):
    with open('books.json', 'w') as f:
        json.dump([book.__dict__ for book in books], f)

def load_folders():
    try:
        with open('folders.json', 'r') as f:
            folders_data = json.load(f)
            return [Folder(**folder) for folder in folders_data]
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_folders(folders):
    with open('folders.json', 'w') as f:
        json.dump([folder.__dict__ for folder in folders], f)