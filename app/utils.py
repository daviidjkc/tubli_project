import requests
from app import db
from app.models import Book

def populate_books():
    # URL base de la API de Gutendex
    url = "https://gutendex.com/books/"
    try:
        # Realizar la solicitud a la API
        response = requests.get(url)
        response.raise_for_status()  # Lanza excepción en caso de error HTTP

        # Decodificar los datos JSON
        data = response.json()
        
        # Iterar sobre los resultados y poblar la base de datos
        for item in data['results']:
            # Extraer los datos necesarios
            title = item['title']
            author = item['authors'][0]['name'] if item['authors'] else 'Desconocido'
            year = item.get('copyright_year', 0)  # Usar 0 si no se encuentra el año
            language = item['languages'][0] if 'languages' in item else 'Desconocido'
            subject = ', '.join(item.get('subjects', [])) or 'General'
            file_url = item['formats'].get('application/epub+zip', '')
            cover_url = item['formats'].get('image/jpeg', '')

            # Validar que el libro tenga los datos mínimos requeridos
            if not title or not file_url:
                continue  # Omitir libros con datos incompletos
            
            # Verificar si el libro ya existe en la base de datos
            existing_book = Book.query.filter_by(title=title, author=author).first()
            if existing_book:
                continue  # Omitir libros duplicados
            
            # Crear un nuevo objeto de libro
            book = Book(
                title=title,
                author=author,
                year=year,
                language=language,
                subject=subject,
                file_url=file_url,
                cover_url=cover_url
            )
            
            # Añadir el libro a la sesión de la base de datos
            db.session.add(book)
        
        # Confirmar los cambios en la base de datos
        db.session.commit()
        print("¡Base de datos poblada exitosamente con libros del Proyecto Gutenberg!")

    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de Gutendex: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
