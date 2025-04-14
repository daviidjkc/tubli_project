from flask import Blueprint, render_template, request
from app.models import Book

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Se puede agregar paginación y lógica de búsqueda
    search_query = request.args.get('q', '')
    if search_query:
        books = Book.query.filter(
            Book.title.ilike(f'%{search_query}%') |
            Book.author.ilike(f'%{search_query}%') |
            Book.subject.ilike(f'%{search_query}%')
        ).all()
    else:
        books = Book.query.all()
    print(f"Libros encontrados: {books}")  # Depuración
    return render_template('index.html', books=books)

@main_bp.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)
from flask import render_template, request
from app.models import Book  # Asegúrate de importar el modelo Book

