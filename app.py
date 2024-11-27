from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from models import db, User, Book, Folder, PDFPosition, UserSettings
from datetime import datetime
from flask_cors import CORS



app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookshare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = upload_folder

if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)
    print(f"Created uploads folder at: {upload_folder}")

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class UserLogin(UserMixin):
    def __init__(self, user):
        self.user = user
        self.username = user.username
        self.is_admin = user.is_admin
        self.id = user.username

    def get_id(self):
        return str(self.username)

@login_manager.user_loader
def load_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return UserLogin(user)
    return None

@app.route('/')
@login_required
def index():
    folders = Folder.query.filter_by(parent_id=None).all()
    unorganized_books = Book.query.filter_by(folder_id=None).all()
    return render_template('index.html', folders=folders, books=unorganized_books)

@app.route('/folder/<int:folder_id>')
@login_required
def folder_view(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    
    # Get ancestors for breadcrumb
    ancestors = []
    current = folder.parent
    while current:
        ancestors.insert(0, current)
        current = current.parent
    
    return render_template('index.html',
                         current_folder=folder,
                         ancestors=ancestors,
                         folders=folder.subfolders,
                         books=folder.books)

@app.route('/add_folder', methods=['GET', 'POST'])
@login_required
def add_folder():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        parent_id = request.form.get('parent_id')
        
        folder = Folder(name=name)
        if parent_id:
            folder.parent_id = parent_id
            
        db.session.add(folder)
        db.session.commit()
        return redirect(url_for('index'))
        
    all_folders = Folder.query.all()
    return render_template('add_folder.html', all_folders=all_folders)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    folders = Folder.query.filter_by(parent_id=None).all()
    
    if request.method == 'POST':
        title = request.form['title']
        yearlevel = request.form['yearlevel']
        course = request.form['course']
        description = request.form['description']
        pdf = request.files['pdf']
        folder_id = request.form.get('folder')
        
        pdf_filename = None
        if pdf:
            pdf_filename = pdf.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            print(f"Saving PDF to: {save_path}")
            pdf.save(save_path)
            print(f"File saved successfully: {os.path.exists(save_path)}")

        folder = db.session.get(Folder, folder_id) if folder_id else None
        book = Book(title=title, yearlevel=yearlevel, course=course, 
                   description=description, pdf=pdf_filename)
        if folder:
            book.folder_id = folder.id
            
        db.session.add(book)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        return redirect(url_for('index'))
        
    return render_template('add_book.html', folders=folders)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

@app.route('/view/<filename>')
@login_required
def view_pdf(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash('PDF file not found')
        return redirect(url_for('index'))
    
    book = Book.query.filter_by(pdf=filename).first()
    if not book:
        flash('Book not found')
        return redirect(url_for('index'))
        
    position = PDFPosition.query.filter_by(
        user_id=current_user.user.id,
        book_id=book.id
    ).first()
    
    settings = UserSettings.query.filter_by(user_id=current_user.user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.user.id)
        db.session.add(settings)
        db.session.commit()
    
    # For now, just use the embed viewer
    return render_template('view_pdf_embed.html', filename=filename, book=book, position=position)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        print(f"Login attempt - Username: {username}")
        print(f"User found: {user is not None}")
        if user:
            print(f"Is admin: {user.is_admin}")
            print(f"Password check: {user.check_password(password)}")
        
        if user and user.check_password(password):
            if user.is_banned:
                flash('Your account has been banned')
                return redirect(url_for('login'))
                
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            userlogin = UserLogin(user)
            print(f"UserLogin created - is_admin: {userlogin.is_admin}")
            
            login_user(userlogin)
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
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        user = User(username=username, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Create default settings for new user
        settings = UserSettings(user_id=user.id, theme='light')
        db.session.add(settings)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/delete/<book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    # Delete the PDF file if it exists
    if book.pdf:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], book.pdf)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    book = Book.query.get_or_404(book_id)
    folders = Folder.query.all()

    if request.method == 'POST':
        book.title = request.form['title']
        book.yearlevel = request.form['yearlevel']
        book.course = request.form['course']
        book.description = request.form['description']
        folder_id = request.form.get('folder')
        book.folder_id = folder_id if folder_id else None
        
        pdf = request.files['pdf']
        if pdf:
            # Delete old PDF if it exists
            if book.pdf:
                old_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], book.pdf)
                if os.path.exists(old_pdf_path):
                    os.remove(old_pdf_path)
            
            # Save new PDF
            book.pdf = pdf.filename
            pdf.save(os.path.join(app.config['UPLOAD_FOLDER'], book.pdf))
            
        db.session.commit()
        return redirect(url_for('index'))
        
    return render_template('edit_book.html', book=book, folders=folders)

@app.route('/folder/<int:folder_id>')
@login_required
def folder_books(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    return render_template('folder_books.html', folder=folder, books=folder.books)

@app.route('/admin')
@login_required
def admin_dashboard():
    print(f"Admin access attempt by {current_user.username}")
    print(f"Is admin: {current_user.is_admin}")
    
    if not current_user.is_admin:
        flash('You do not have admin privileges')
        return redirect(url_for('index'))
    
    stats = {
        'total_users': User.query.count(),
        'total_books': Book.query.count(),
        'total_folders': Folder.query.count(),
        'banned_users': User.query.filter_by(is_banned=True).count()
    }
    
    users = User.query.all()
    return render_template('admin/dashboard.html', stats=stats, users=users)

@app.route('/admin/user/add', methods=['POST'])
@login_required
def admin_add_user():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    username = request.form['username']
    password = request.form['password']
    is_admin = request.form.get('is_admin') == 'on'
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('admin_dashboard'))
    
    user = User(username=username, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash('User added successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
def admin_toggle_admin(user_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/toggle_ban', methods=['POST'])
@login_required
def admin_toggle_ban(user_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/api/pdf/position/<book_id>', methods=['POST'])
@login_required
def save_pdf_position(book_id):
    try:
        data = request.get_json()
        page = data.get('page', 1)
        
        # Get or create position record
        position = PDFPosition.query.filter_by(
            user_id=current_user.user.id,
            book_id=book_id
        ).first()
        
        if position:
            if position.page != page:  # Only update if page changed
                position.page = page
                db.session.commit()
                print(f"Saved position for user {current_user.username}: page {page}")
        else:
            position = PDFPosition(
                user_id=current_user.user.id,
                book_id=book_id,
                page=page
            )
            db.session.add(position)
            db.session.commit()
            print(f"Created new position for user {current_user.username}: page {page}")
            
        return jsonify({'success': True, 'page': page})
        
    except Exception as e:
        print(f"Error saving position: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_default_admin():
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        try:
            admin = User(username='admin', is_admin=True)
            admin.set_password('adiyogi1')
            db.session.add(admin)
            db.session.commit()
            
            # Create default settings for admin
            settings = UserSettings(user_id=admin.id, theme='light')
            db.session.add(settings)
            db.session.commit()
            
            print("Default admin user created successfully!")
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()
    else:
        # Ensure admin has settings
        if not UserSettings.query.filter_by(user_id=admin.id).first():
            settings = UserSettings(user_id=admin.id, theme='light')
            db.session.add(settings)
            db.session.commit()
        print("Admin user already exists")

@app.route('/settings')
@login_required
def settings():
    user_settings = UserSettings.query.filter_by(user_id=current_user.user.id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.user.id)
        db.session.add(user_settings)
        db.session.commit()
    return render_template('settings.html', settings=user_settings)

@app.route('/settings/save', methods=['POST'])
@login_required
def save_settings():
    user_settings = UserSettings.query.filter_by(user_id=current_user.user.id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.user.id)
        db.session.add(user_settings)
    
    user_settings.theme = request.form.get('theme', 'light')
    db.session.commit()
    flash('Settings saved successfully')
    return redirect(url_for('settings'))

@app.context_processor
def inject_user_settings():
    return {
        'UserSettings': UserSettings
    }

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Drop all tables
        db.create_all()  # Create new tables
        create_default_admin()  # Create default admin user with settings
    app.run(debug=True, port=5001, host="0.0.0.0")
