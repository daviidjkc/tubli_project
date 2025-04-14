from app import create_app
from app.utils import populate_books

app = create_app()

with app.app_context():
    populate_books()