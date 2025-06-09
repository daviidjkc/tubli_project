from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, flash, abort
from app.models import Book, User
import requests
import tempfile
import os
import io
from sqlalchemy import case, or_
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db

main_bp = Blueprint('main', __name__)

CLOUDCONVERT_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYjFiNjg1YTBiZGRmMjVkODNiMmMzMDI2ZDQ2OGVjMzExNTFmZDY2OTAyMTQ4MzY3NDY5MWM5NjA3OGQzYmY1N2RhNTNhNmNlNWFkYzk4ZjQiLCJpYXQiOjE3NDcxMjcwNTcuODgzMDk1LCJuYmYiOjE3NDcxMjcwNTcuODgzMDk2LCJleHAiOjQ5MDI4MDA2NTcuODc5NjM1LCJzdWIiOiI3MTkxMDQ3OCIsInNjb3BlcyI6WyJ0YXNrLndyaXRlIiwidGFzay5yZWFkIl19.agMpzHyxC4Qbn3LMdCUqJ8DgqUefxNWrETqzPvnDVZxBDLnUzyGFfdySvzlldplG5ZhTx2sCR3ZeeR3J-DRpVeVQglfzZtMGfzNZaaZMwBksCsXeyrxrYsOh4-igJxcKtchcFkim0X_2ajZBUJv-hxoo7_DmIENphEkJRZmM-fLuENmE23wot16tiBbn3FrRBS9ZUzT_k5wgWQcQx0_o5FCQiW1a3lAXcBKHQe3oBHlfaTHwCecixLejlkNmFafHBS9nxj9WqLcO0Fxt-QuSbrMTq9_Jvv9UpZrhzzxgGSrEJ_OAlFmg7BvZ8_Qj9rEMs47vDXOIX1dN_E10_2gJ1zh3nf62eTtGPQ3FuAXsD-jFEdXbTbC6td3hItzveGBUC59v2TKdACnXE0DErYAaOBltEWuz4niDj4SyRv7T1lf6_p9lzAegRXfOTzrzpc7ZW2U9NOe8xFVj-bCI2yzh7nKfR24yfT4kP7P9RqSe57rDehetZ4CNZqKZ3O8iwu5kVwSx5evggLg0gJ8651Nw6foxOA2pwkh0T7qm39nS2hW6wD7rl6ZdeaOy5oDr-e-iiTJdogzq91Q7lAztjiAEpNcSd_rPaV79O8N8XfY5903VcubTxzpakWjQVBiKI8FXRJoQfHAnIN0cX0hnHcl03Se91g-_xaD9DqfUDyLX7MI"  


@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search_query = request.args.get('q', '').strip()

    query = Book.query

    if search_query:
        query = query.filter(
            or_(
                Book.title.ilike(f'%{search_query}%'),
                Book.author.ilike(f'%{search_query}%'),
                Book.subject.ilike(f'%{search_query}%')
            )
        )

    pagination = query.order_by(
        case(
            (Book.cover_url == None, 1),
            (Book.cover_url == '', 1),
            else_=0
        ),
        Book.id
    ).paginate(page=page, per_page=per_page)
    books = pagination.items

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

@main_bp.route('/convert_epub_to_pdf/<int:book_id>', methods=['POST'])
def convert_epub_to_pdf(book_id):
    book = Book.query.get_or_404(book_id)
    epub_url = book.file_url

    # Descarga el archivo EPUB temporalmente
    epub_response = requests.get(epub_url)
    if epub_response.status_code != 200:
        flash('No se pudo descargar el archivo EPUB.', 'danger')
        return redirect(url_for('main.book_detail', book_id=book_id))

    with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as epub_file:
        epub_file.write(epub_response.content)
        epub_file_path = epub_file.name

    headers = {"Authorization": f"Bearer {CLOUDCONVERT_API_KEY}"}

    # 1. Crear el job con import/upload, convert y export/url
    job_payload = {
        "tasks": {
            "import-1": {
                "operation": "import/upload"
            },
            "convert-1": {
                "operation": "convert",
                "input": "import-1",
                "input_format": "epub",
                "output_format": "pdf"
            },
            "export-1": {
                "operation": "export/url",
                "input": "convert-1"
            }
        }
    }
    job_response = requests.post("https://api.cloudconvert.com/v2/jobs", headers=headers, json=job_payload)
    job_data = job_response.json()
    import_task = next(task for task in job_data["data"]["tasks"] if task["name"] == "import-1")
    upload_url = import_task["result"]["form"]["url"]
    upload_params = import_task["result"]["form"]["parameters"]

    # 2. Subir el archivo EPUB a la URL proporcionada
    with open(epub_file_path, "rb") as f:
        files = {'file': (os.path.basename(epub_file_path), f)}
        requests.post(upload_url, data=upload_params, files=files)

    os.remove(epub_file_path)

    # 3. Esperar a que el job termine y obtener el enlace al PDF
    import time
    job_id = job_data["data"]["id"]
    pdf_url = None
    for _ in range(30):  # Espera hasta 30 segundos
        status_response = requests.get(f"https://api.cloudconvert.com/v2/jobs/{job_id}", headers=headers)
        status_data = status_response.json()
        if status_data["data"]["status"] == "finished":
            for task in status_data["data"]["tasks"]:
                if task["name"] == "export-1" and "result" in task and "files" in task["result"]:
                    pdf_url = task["result"]["files"][0]["url"]
                    break
            break
        time.sleep(1)

    if pdf_url:
        pdf_response = requests.get(pdf_url)
        return send_file(
            io.BytesIO(pdf_response.content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{book.title}.pdf"
        )
    else:
        flash('No se pudo convertir el archivo a PDF.', 'danger')
        return redirect(url_for('main.book_detail', book_id=book_id))

@main_bp.route('/add_book', methods=['POST'])
@login_required
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    year = request.form.get('year')
    language = request.form.get('language')
    subject = request.form.get('subject')
    summary = request.form.get('summary')
    cover_url = request.form.get('cover_url')
    cover_file = request.files.get('cover_file')
    epub_file = request.files.get('epub_file')

    # Crear carpeta uploads si no existe
    upload_folder = os.path.join(os.getcwd(), 'static', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Guardar portada si es archivo
    if cover_file and cover_file.filename:
        filename = secure_filename(cover_file.filename)
        cover_path = os.path.join('static', 'uploads', filename)
        cover_file.save(os.path.join(os.getcwd(), cover_path))
        cover_url = url_for('static', filename=f'uploads/{filename}')

    # Guardar EPUB
    epub_url = None
    if epub_file and epub_file.filename:
        epub_filename = secure_filename(epub_file.filename)
        epub_path = os.path.join('static', 'uploads', epub_filename)
        epub_file.save(os.path.join(os.getcwd(), epub_path))
        epub_url = url_for('static', filename=f'uploads/{epub_filename}')

    new_book = Book(
        title=title,
        author=author,
        year=year if year else None,
        language=language,
        subject=subject,
        summary=summary,
        cover_url=cover_url,
        file_url=epub_url,
        user_id=current_user.id   # <-- ¡AQUÍ!
    )
    from app import db
    db.session.add(new_book)
    db.session.commit()
    flash('Libro agregado correctamente.', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/mis-libros')
@login_required
def mis_libros():
    libros = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('mis_libros.html', libros=libros)

@main_bp.route('/configuracion')
@login_required
def configuracion():
    return render_template('configuracion.html')

@main_bp.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    user = User.query.filter_by(username=username).first()
    exists = user is not None
    return jsonify({'exists': exists})

@main_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('nombre')
    foto = request.files.get('fotoPerfil')
    # Verifica si el nombre ya existe y no es el del usuario actual
    if username != current_user.username:
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'El nombre de usuario ya existe.'})
    current_user.username = username

    # Guardar la foto de perfil si se subió una nueva
    if foto and foto.filename:
        filename = secure_filename(foto.filename)
        upload_folder = os.path.join('app', 'static', 'uploads', 'profile_pics')
        os.makedirs(upload_folder, exist_ok=True)
        foto_path = os.path.join(upload_folder, filename)
        foto.save(foto_path)
        current_user.profile_pic = f'uploads/profile_pics/{filename}'

    db.session.commit()
    return jsonify({'success': True, 'message': '¡Perfil actualizado!'})

@main_bp.route('/favoritos')
@login_required
def favoritos():
    return render_template('favoritos.html', favoritos=current_user.favorites)

@main_bp.route('/toggle_favorito/<int:book_id>', methods=['POST'])
@login_required
def toggle_favorito(book_id):
    book = Book.query.get_or_404(book_id)
    if book in current_user.favorites:
        current_user.favorites.remove(book)
        db.session.commit()
        status = 'removed'
    else:
        current_user.favorites.append(book)
        db.session.commit()
        status = 'added'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': status})
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/help', methods=['GET', 'POST'])
def help():
    return render_template('help.html')

@main_bp.route('/send_help_email', methods=['POST'])
def send_help_email():
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    # Aquí deberías enviar el correo usando tu sistema preferido (Flask-Mail, SMTP, etc.)
    # Por ahora solo mostramos un mensaje de éxito
    flash('Tu mensaje ha sido enviado. Nos pondremos en contacto contigo pronto.', 'success')
    return redirect(url_for('main.help'))

@main_bp.route('/editar_libro/<int:book_id>', methods=['GET', 'POST'])
@login_required
def editar_libro(book_id):
    libro = Book.query.get_or_404(book_id)
    if libro.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        libro.title = request.form.get('title')
        libro.summary = request.form.get('summary')
        libro.author = request.form.get('author')
        libro.year = request.form.get('year')
        libro.language = request.form.get('language')
        libro.subject = request.form.get('subject')
        db.session.commit()
        flash('Libro actualizado correctamente.', 'success')
        return redirect(url_for('main.mis_libros'))
    return render_template('editar_libro.html', libro=libro)

@main_bp.route('/eliminar_libro/<int:book_id>', methods=['POST'])
@login_required
def eliminar_libro(book_id):
    libro = Book.query.get_or_404(book_id)
    if libro.user_id != current_user.id:
        abort(403)
    db.session.delete(libro)
    db.session.commit()
    flash('Libro eliminado correctamente.', 'success')
    return redirect(url_for('main.mis_libros'))

