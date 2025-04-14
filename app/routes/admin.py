import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import Book
from app import db
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@admin_bp.before_request
def restrict_to_admin():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/dashboard')
def dashboard():
    books = Book.query.all()
    return render_template('admin_dashboard.html', books=books)

@admin_bp.route('/book/new', methods=['GET', 'POST'])
def new_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        year = request.form.get('year')
        language = request.form.get('language')
        subject = request.form.get('subject')
        
        # Gestión de subida del archivo EPUB
        epub_file = request.files.get('epub_file')
        file_url = None
        if epub_file and allowed_file(epub_file.filename):
            filename = secure_filename(epub_file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            epub_file.save(upload_path)
            file_url = url_for('static', filename=f"uploads/{filename}")
        
        # Se pueden procesar también las portadas (cover_url)
        cover_url = request.form.get('cover_url')
        
        new_book = Book(
            title=title,
            author=author,
            year=year,
            language=language,
            subject=subject,
            file_url=file_url,
            cover_url=cover_url
        )
        db.session.add(new_book)
        db.session.commit()
        flash('Libro añadido correctamente.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('book_form.html')

@admin_bp.route('/book/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.year = request.form.get('year')
        book.language = request.form.get('language')
        book.subject = request.form.get('subject')
        book.cover_url = request.form.get('cover_url')
        
        epub_file = request.files.get('epub_file')
        if epub_file and allowed_file(epub_file.filename):
            filename = secure_filename(epub_file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            epub_file.save(upload_path)
            book.file_url = url_for('static', filename=f"uploads/{filename}")
        
        db.session.commit()
        flash('Libro actualizado.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('book_form.html', book=book)
