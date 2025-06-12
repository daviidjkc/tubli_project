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

PALABRAS_PROHIBIDAS = [
    'insulto', 'palabrota', 'violencia', 'sexo', 'pornografía', 'racismo', 'drogas', 'asesinato', 'puta', 'puto', 'gilipollas', 'imbécil', 'idiota', 'cabrona', 'cabron', 'pendejo', 'mierda', 'joder', 'coño', 'cabrón', 'zorra', 'maricón', 'marica', 'estupido', 'estupida', 'tonto', 'tonta', 'baboso', 'babosa', 'chingar', 'chingada', 'chingado', 'culero', 'culera', 'verga', 'polla', 'huevos', 'cojones', 'pelotas', 'putilla', 'mamón', 'mamona', 'pendeja', 'culito', 'culazo', 'nalgas', 'trasero', 'culo', 'tetona', 'tetas', 'pechos', 'chichi', 'chichis', 'puta madre', 'vete a la mierda', 'maldito', 'maldita', 'perra', 'perro', 'malparido', 'malparida', 'hijo de puta', 'hija de puta', 'mierdoso', 'asqueroso', 'asquerosa', 'lameculos', 'lamebotas', 'pelotudo', 'pelotuda', 'imbéciles', 'imbecil', 'idiotas', 'zorras', 'estúpidos', 'estupidas', 'gorda', 'gordo', 'fea', 'feo', 'asco', 'asquerosidad', 'desgraciado', 'desgraciada', 'degenerado', 'degenerada', 'nazi', 'terrorista', 'asesino', 'asesina', 'violador', 'violadora', 'racista', 'homófobo', 'homofóbico', 'homofóbica', 'xenófobo', 'xenofóbico', 'xenofóbica', 'pedófilo', 'pedófila', 'zoofilia', 'necrofilia', 'sádico', 'sádica', 'masoquista', 'suicidio', 'suicida', 'autolesión', 'sexo', 'pornografía', 'porno', 'pornografico', 'pornografica', 'orgasmo', 'masturbación', 'masturbar', 'correrse', 'eyacular', 'erección', 'penetración', 'anal', 'oral', 'chupar', 'mamadas', 'felación', 'coito', 'fornicar', 'prostituta', 'prostituto', 'burdel', 'droga', 'drogas', 'narcotráfico', 'narco', 'traficante', 'metanfetamina', 'cocaína', 'heroína', 'crack', 'opio', 'marihuana', 'porro', 'alucinógeno', 'alcohólico', 'borracho', 'ebrio', 'intoxicado', 'puticlub', 'violencia', 'golpear', 'matar', 'asesinar', 'arma', 'disparo', 'puñalada', 'matón', 'delincuente', 'criminal', 'delito', 'crimen', 'secuestrar', 'secuestro', 'extorsión', 'chantaje', 'tortura', 'maltrato', 'abuso', 'abusar', 'agresión', 'agresor', 'agresora', 'vandalismo', 'terrorismo', 'terrorista', 'bomba', 'explosivo', 'atentado', 'asesinato en masa', 'genocidio', 'holocausto', 'racismo', 'discriminación', 'xenofobia', 'homofobia', 'machismo', 'misoginia', 'misógino', 'misógina', 'sexismo', 'sexista', 'feminicidio', 'feminicida', 'feminista radical', 'feminismo radical', 'machista radical', 'machismo radical', 'pervertido', 'pervertida', 'depravado', 'depravada', 'cochina', 'cochino', 'cornudo', 'cornuda', 'imbecilazo', 'malnacido', 'malnacida', 'muerto de hambre', 'muerta de hambre', 'muérete', 'mátate', 'te odio', 'desgracia', 'puta asquerosa', 'cerda', 'cerdo', 'bestia', 'mongolo', 'mongólica', 'retrasado', 'retrasada', 'atrasado', 'atrasada', 'subnormal', 'loca', 'loco', 'deforme', 'abortado', 'abortada', 'bastardo', 'bastarda', 'pichula', 'concha', 'conchuda', 'conchudo', 'conchatumadre', 'pendejazo', 'pendejita', 'putarraca', 'putona', 'tortillera', 'machorra', 'culiado', 'culiada', 'culiando', 'coje', 'coger', 'te cojo', 'me cogió', 'te cogí', 'fornicador', 'fornicadora', 'sexo anal', 'sexo oral', 'tragar', 'corrida', 'me corrí', 'te corriste', 'eyaculación', 'venirse', 'me vine', 'paja', 'hacerse la paja', 'manosear', 'manoseado', 'manoseada', 'calentón', 'calentona', 'provocativa', 'provocador', 'nalgona', 'culo grande', 'reventar', 'reventado', 'reventada', 'marihuanero', 'marihuanera', 'cocainómano', 'cocainómana', 'drogadicto', 'drogadicta', 'pasado', 'fumado', 'fumón', 'fumona', 'traficar', 'dealer', 'crimen', 'delito', 'violento', 'violenta', 'asesinato', 'matador', 'matadora', 'degollar', 'apuñalar', 'linchar', 'linchamiento', 'sangre', 'desmembrar', 'ahorcar', 'asfixiar', 'descuartizar', 'esclavizar', 'torturar', 'secuestrar', 'secuestrador', 'pedazo de mierda', 'basura humana', 'escoria', 'escoria humana', 'bicho', 'apestoso', 'muerto', 'apestosa', 'mierdero', 'mierdera', 'putrefacto', 'sucio', 'sucia', 'inútil', 'fracasado', 'fracasada', 'malco', 'huevón de mierda', 'caremierda', 'cara de nalga', 'maldito imbécil', 'chupaverga', 'chupapollas', 'idiota con patas', 'pobre diablo', 'gusano', 'cabrón de mierda', 'chucho', 'tontolaba', 'inútil de mierda', 'jodido', 'chingadera', 'babosada de mierda', 'animal de monte', 'cara de rata', 'feo culiao', 'cerebro de mosquito', 'tonto de remate', 'pedazo de inútil', 'cara de vergüenza', 'mamaguevo', 'mamabicho', 'cara de chimba', 'culicagado', 'cara de culo infectado', 'zángano asqueroso', 'pelagatos', 'cascajo', 'muerto en vida', 'sinvergüenza', 'basofia', 'escupitajo', 'trapo sucio', 'muerto de risa', 'cabeza de rodilla', 'chamuco', 'peludo hediondo', 'cagón', 'hediondo', 'mocoso', 'lengua larga', 'tragón', 'muerto de miedo', 'mal nacido', 'pelo de escoba', 'manteco', 'sin oficio', 'culebrero', 'pata rajada', 'apestoso inútil', 'retrasado de porquería', 'maldito gusano', 'hijo de perra', 'hija de perra', 'puerco asqueroso', 'pobre imbécil', 'engendro', 'engendro del demonio', 'demonio', 'desgracia ambulante', 'rata de cloaca', 'tarado mental', 'shithead', 'motherfucking', 'cockface', 'twatface', 'dickface', 'cumface', 'shittard', 'assclown', 'asslicker', 'fucknugget', 'cumstain', 'fuckhole', 'dickless', 'ballless', 'shitlicker', 'assbreath', 'fartface', 'cumface', 'shitstain', 'fuckbrain', 'pissbrain', 'shitbrain', 'assbrain', 'douche', 'douchelord', 'shitlord', 'buttmunch', 'dickbreath', 'titlicker', 'cockgobbler', 'ballsucker', 'fuckwad', 'knobgobbler', 'fuckpuppet', 'shitweasel', 'splooge', 'nutlicker', 'pissflap', 'fucked', 'fuckery', 'wankstain', 'fucktard', 'turd', 'jerkwad', 'jerkwater', 'shitcunt', 'cumdrinker', 'whorefucker', 'cumguzzler', 'fuckrag', 'cockmuncher', 'tithead', 'assnugget', 'analqueen', 'ballsack', 'dicknose', 'shitwhistle', 'assburger', 'fuckshit', 'cuntface', 'hellspawn', 'pigfucker', 'fuckbag', 'cockwad', 'arsewipe', 'shitspreader', 'twatwaffle', 'dickcheese', 'fucko', 'motherfuckin', 'sucker', 'nutjob', 'pussylicker', 'assrammer', 'cockpusher', 'shitlick', 'cuntmunch', 'fuckhole', 'p3rr4', 'p3rra', 'p3rro', 'p3nd3jo', 'p3ndejo', 'pndjo', 'pndja', 'm1erd4', 'mierd@', 'm13rd4', 'mrd4', 'hpt', 'hdp', 'h1j0 d3 put4', 'h1jo d3 p', 'hjdp', 'cabron', 'c4bron', 'c4br0n', 'kbron', 'cabro0n', 'j0der', 'j0d3r', 'joderte', 'j0d3rt3', 'jodete', 'c0ñ0', 'coñ0', 'c0n0', 'z0rr4', 'zorra', 'z0rra', 'm4m0n', 'mam0n', 'mam4n', 'm4man', 'm4mada', 'mamad@', 'ch1ng4r', 'ching@r', 'ch1ngada', 'chingada', 'ching@d@', 'c0l3r0', 'cul3r0', 'culer@', 'cvl3r0', 'cvlero', 'ver9a', 'v3rg4', 'verg@', 'vrg4', 'v3rga', 'vrg4', 'cul0', 'kulo', 'qlo', 'ql0', 'n4lg4s', 'nal9as', 'n@lg@s', 't3t4s', 't3tas', 'tet4s', 'ch1ch1s', 'chich1s', 'ch1chis', 'porn0', 'p0rn0', 'p0rn', 'sx0', 's3x0', 's3xo', 's3x', 'm4sturb4r', 'masturb@r', 'm4stvrb4r', 'suc1d10', 'su1c1d10', 'su1cidio', 'suc1d1o', 'v10l4r', 'v1ol4r', 'v10lador', 'v1olador', 't0rtur4', 't0rtvr4', 'fck', 'f**k', 'f@ck', 'fck', 'fuk', 'fuxk', 'fook', 'f_ck', 'f.ck', 'fucc', 'fuk', 'sht', 's**t', 'sh1t', 'sht', 'sh!t', 's.h.i.t', 'b1tch', 'b!tch', 'btch', 'bi7ch', 'b17ch', 'b!7ch', 'cnt', 'c@nt', 'cntface', 'cu**', 'pussy', 'pu$$y', 'pssy', 'p@ssy', 'pus$y', 'd1ck', 'd!ck', 'dck', 'd@ck', 'd!ckhead', 'd1ckhead', 'dckhead', 'd@mn', 'd@mn', 'dam!', 'h3ll', 'h311', 'hll', 'h@ll', 'c0ck', 'cck', 'c@ck', 'co(k', 'f@g', 'fa66ot', 'f@gg0t', 'f4gg0t', 'f@g', 'fa9', 'd0uche', 'doucheb@g', 'd0uch3', 'cumdump', 'cm', 'cmshot', 'cmface', 's3x', 's3xy', 'sx', 's@x', 'or4l', '4nal', 'assfck', 'assfk', 'fcked', 'fcking', 'f*ing', 'f**ked'
]

def contiene_palabras_prohibidas(texto):
    if not texto:
        return False
    texto = texto.lower()
    return any(palabra in texto for palabra in PALABRAS_PROHIBIDAS)