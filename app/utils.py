import requests
import json
from app import db
from app.models import Book



def populate_books():
    # URL base de la API de Gutendex
    base_url = "https://gutendex.com/books/"
    page = 1  # Comenzar desde la primera página
    total_books_loaded = 0  # Contador de libros cargados

    # Límite opcional de páginas o libros
    max_pages = 10  # Por ejemplo, cargar solo 10 páginas

    try:
        while page <= max_pages:
            print(f"Procesando página {page}...")
            response = requests.get(base_url, params={'page': page})
            response.raise_for_status()

            # Decodificar los datos JSON
            data = response.json()
            results = data.get('results', [])
            print(f"Resultados encontrados: {len(results)}")

            if not results:  # Si no hay más resultados, salir del bucle
                break

            # Iterar sobre los resultados y poblar la base de datos
            for item in results:
                print(item)  # <-- Esto mostrará toda la información de cada libro en la terminal
                # Extraer los datos necesarios
                title = item['title']
                author = item['authors'][0]['name'] if item['authors'] else 'Desconocido'
                author_birth_year = item['authors'][0].get('birth_year') if item['authors'] else None
                author_death_year = item['authors'][0].get('death_year') if item['authors'] else None

                # Intenta obtener el año de publicación de diferentes campos
                year = None
                if 'first_publish_year' in item and item['first_publish_year']:
                    year = item['first_publish_year']
                elif 'copyright_year' in item and item['copyright_year']:
                    year = item['copyright_year']
                elif 'publish_year' in item and item['publish_year']:
                    year = item['publish_year'][0]

                # NUEVO: guardar todos los idiomas como string separado por coma
                languages = ','.join(item.get('languages', [])) if 'languages' in item else ''
                language = item['languages'][0] if 'languages' in item and item['languages'] else 'Desconocido'
                subject = ', '.join(item.get('subjects', [])) or 'General'
                file_url = item['formats'].get('application/epub+zip', '')
                cover_url = item['formats'].get('image/jpeg', '')
                summary = item['summaries'][0] if 'summaries' in item and item['summaries'] else None
                download_count = item.get('download_count', 0)
                formats = json.dumps(item.get('formats', {}))  # NUEVO: guarda todos los formatos

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
                    languages=languages,
                    author_birth_year=author_birth_year,
                    author_death_year=author_death_year,
                    subject=subject,
                    file_url=file_url,
                    cover_url=cover_url,
                    summary=summary,
                    download_count=download_count,
                    formats=formats
                )

                # Añadir el libro a la sesión de la base de datos
                db.session.add(book)
                total_books_loaded += 1

            # Confirmar los cambios en la base de datos después de cada página
            db.session.commit()
            print(f"Página {page} procesada. Libros cargados hasta ahora: {total_books_loaded}")

            page += 1  # Pasar a la siguiente página

        print(f"¡Base de datos poblada exitosamente con {total_books_loaded} libros del Proyecto Gutenberg!")

    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de Gutendex: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
