import os
import sys
import logging
import tempfile  # Importar módulo para directorios temporales
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request

# Configuración de paths
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'backend'))

# Importaciones del backend
from backend.database import DBManager, Article
from backend.scraper import ContentScraper
from backend.organizers import ContentOrganizer
from backend.generators import BookGenerator
from backend.config import EDUCATIONAL_STRUCTURE, SELECTORS

# Inicialización de Flask
app = Flask(__name__,
            static_folder=str(BASE_DIR / 'frontend/static'),
            template_folder=str(BASE_DIR / 'frontend/templates'))

# Configuración de la aplicación
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-key-123'),
    'DATABASE_DIR': str(BASE_DIR / 'backend/user_dbs'),
    'UPLOAD_FOLDER': str(BASE_DIR / 'frontend/static/books'),
    'MAX_CONTENT_AGE': timedelta(hours=24),
    'MAX_CONTENT_LENGTH': 15 * 1024 * 1024  # 15MB
})

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Crear directorios necesarios"""
    required_dirs = [
        app.config['DATABASE_DIR'],
        app.config['UPLOAD_FOLDER'],
        BASE_DIR / 'frontend/static/css',
        BASE_DIR / 'frontend/templates'
    ]
    
    for directory in required_dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directorio creado: {directory}")
        except PermissionError as e:
            if directory == Path(app.config['UPLOAD_FOLDER']):
                # Usar un directorio temporal si no se puede crear el directorio de subida
                temp_dir = tempfile.mkdtemp()
                app.config['UPLOAD_FOLDER'] = temp_dir
                logger.warning(f"Permiso denegado para {directory}. Usando directorio temporal: {temp_dir}")
            else:
                logger.critical(f"Permiso denegado al crear el directorio {directory}: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error creando directorio {directory}: {str(e)}")
            raise

def clean_old_files():
    """Limpiar archivos antiguos"""
    now = datetime.now()
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = Path(app.config['UPLOAD_FOLDER']) / filename
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if (now - file_time) > app.config['MAX_CONTENT_AGE']:
                    file_path.unlink()
                    logger.info(f"Archivo eliminado: {filename}")
    except Exception as e:
        logger.error(f"Error limpiando archivos: {str(e)}")

# Rutas principales
@app.route('/')
def home():
    # Renderizar el archivo index.html desde la carpeta templates
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/generate', methods=['POST'])
def generate_book():
    setup_directories()
    clean_old_files()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
            
        blog_url = data.get('url')
        if not blog_url or not isinstance(blog_url, str):
            return jsonify({'error': 'URL inválida'}), 400

        session_id = os.urandom(16).hex()
        db_path = Path(app.config['DATABASE_DIR']) / f'{session_id}.db'
        output_file = Path(app.config['UPLOAD_FOLDER']) / f'book_{session_id}.pdf'

        # Proceso de generación
        with DBManager(str(db_path)) as db:
            scraper = ContentScraper(db)
            
            if not scraper.scrape(blog_url):
                return jsonify({'error': 'Error obteniendo contenido'}), 500

            articles = db.get_all_articles()
            if not articles:
                return jsonify({'error': 'No se encontró contenido'}), 404

            organizer = ContentOrganizer(articles)
            book_structure = organizer.structure_content()

            generator = BookGenerator(str(output_file))
            if generator.generate_book(book_structure):
                return jsonify({
                    'download_url': f"/static/books/book_{session_id}.pdf",
                    'filename': f'Libro_{datetime.now().strftime("%Y%m%d")}.pdf'
                })

        return jsonify({'error': 'Error generando PDF'}), 500

    except Exception as e:
        logger.error(f"Error en generación: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500

# Manejo de errores
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Solicitud inválida'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    try:
        setup_directories()
        
        # Archivos para recarga automática
        extra_files = [
            str(BASE_DIR / 'frontend/static/css/styles.css'),
            str(BASE_DIR / 'frontend/templates/index.html'),
            str(BASE_DIR / 'backend/config.py')
        ]
        
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True,
            use_reloader=True,
            extra_files=extra_files
        )
    except Exception as e:
        logger.critical(f"Error iniciando la aplicación: {str(e)}")
        raise