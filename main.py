from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import json
from models import User, Book, load_users, save_users, load_books, save_books

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

users = load_users()
books = load_books()

class UserLogin(UserMixin):
    def __init__(self, user):
        self.username = user.username
        self.is_admin = user.is_admin
        self.id = user.username

@login_manager.user_loader
def load_user(username):
    for user in users:
        if user.username == username:
            return UserLogin(user)
    return None

@app.route('/')
@login_required
def index():
    return render_template('index.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        yearlevel = request.form['yearlevel']
        course = request.form['course']
        description = request.form['description']
        pdf = request.files['pdf']

        pdf_filename = None
        if pdf:
            pdf_filename = pdf.filename
            pdf.save(os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename))

        book = Book(title, yearlevel, course, description, pdf_filename)
        books.append(book)
        save_books(books)
        return redirect(url_for('index'))
    return render_template('add_book.html')

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/view/<filename>')
@login_required
def view_pdf(filename):
    return render_template('view_pdf.html', filename=filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for user in users:
            if user.username == username and user.check_password(password):
                login_user(UserLogin(user))
                return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'
        user = User(username, password, is_admin)
        users.append(user)
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/delete/<int:book_index>', methods=['POST'])
@login_required
def delete_book(book_index):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if 0 <= book_index < len(books):
        books.pop(book_index)
        save_books(books)
    return redirect(url_for('index'))

@app.route('/edit/<int:book_index>', methods=['GET', 'POST'])
@login_required
def edit_book(book_index):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    book = books[book_index]
    if request.method == 'POST':
        book.title = request.form['title']
        book.yearlevel = request.form['yearlevel']
        book.course = request.form['course']
        book.description = request.form['description']
        pdf = request.files['pdf']
        if pdf:
            book.pdf = pdf.filename
            pdf.save(os.path.join(app.config['UPLOAD_FOLDER'], book.pdf))
        save_books(books)
        return redirect(url_for('index'))
    return render_template('edit_book.html', book=book)

if __name__ == '__main__':
    app.run(debug=True)
