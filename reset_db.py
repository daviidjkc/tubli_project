from app import create_app, db
from app.models import Book
from app.utils import populate_books

app = create_app()
with app.app_context():
    print("Borrando libros...")
    Book.query.delete()
    db.session.commit()
    print("Repoblando libros...")
    populate_books()
    print("¡Listo!")