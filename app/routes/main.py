from flask import Blueprint, render_template, request, jsonify
from app.models import Book

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Obtener el número de página actual desde los parámetros de la URL
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Mostrar 12 libros por página

    # Consulta con paginación
    pagination = Book.query.paginate(page=page, per_page=per_page)
    books = pagination.items  # Libros de la página actual

    return render_template('index.html', books=books, pagination=pagination)

@main_bp.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)

@main_bp.route('/count_books', methods=['GET'])
def count_books():
    try:
        book_count = Book.query.count()  # Cuenta el número de libros
        return jsonify({'total_books': book_count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

