from flask import Flask, render_template, request, jsonify
from scraper import ContentScraper
from generators import BookGenerator
from database import DBManager
from organizers import ContentOrganizer
import os
import uuid
import logging
from datetime import datetime, timedelta
import click
from pathlib import Path
import shutil

# Configuración inicial de la aplicación
app = Flask(__name__, 
           static_folder='../frontend/static',
           template_folder='../frontend/templates')

# Configuración desde variables de entorno
app.config.update({
    'UPLOAD_FOLDER': os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static', 'books'),
    'DATABASE_DIR': os.path.join(os.path.dirname(__file__), 'user_dbs'),
    'MAX_CONTENT_AGE': timedelta(hours=24),
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-key-123')
})

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Helper functions
def setup_directories():
    """Crear directorios necesarios si no existen"""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATABASE_DIR'], exist_ok=True)

def clean_old_files():
    """Limpiar archivos antiguos automáticamente"""
    now = datetime.now()
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if now - file_time > app.config['MAX_CONTENT_AGE']:
            os.remove(file_path)
            logger.info(f"Archivo limpiado: {filename}")

# Comando CLI para inicializar la base de datos
@app.cli.command("init-db")
@click.option('--force', is_flag=True, help='Eliminar bases de datos existentes')
def init_db_command(force=False):
    """Inicializar el sistema de bases de datos"""
    try:
        db_dir = Path(app.config['DATABASE_DIR'])
        
        if force:
            shutil.rmtree(db_dir, ignore_errors=True)
            logger.info("🗑️  Bases de datos eliminadas")
        
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directorio de bases de datos creado en: {db_dir}")
        
        # Crear base de datos de prueba
        test_db = DBManager(str(db_dir / "test.db"))
        test_db.create_tables()
        logger.info("✅ Tablas creadas en base de datos de prueba")
        
        clean_old_files()
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}", exc_info=True)
        raise

# Rutas de la aplicación
@app.route('/')
def home():
    """Página principal"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_book():
    """Endpoint para generación de libros"""
    setup_directories()
    clean_old_files()
    
    data = request.json
    blog_url = data.get('url')
    
    if not blog_url:
        return jsonify({'error': 'Se requiere URL del blog'}), 400
    
    try:
        session_id = uuid.uuid4().hex
        db_path = os.path.join(app.config['DATABASE_DIR'], f'{session_id}.db')
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], f'book_{session_id}.pdf')
        
        db = DBManager(db_path)
        scraper = ContentScraper(db)
        
        logger.info(f"Iniciando scraping para: {blog_url}")
        if not scraper.scrape_articles(blog_url, max_articles=50):
            return jsonify({'error': 'No se pudo extraer contenido del blog'}), 500
        
        logger.info("Organizando contenido...")
        articles = db.get_all_articles()
        if not articles:
            return jsonify({'error': 'No se encontró contenido válido'}), 404
            
        organizer = ContentOrganizer(articles)
        book_structure = organizer.structure_content()
        
        logger.info("Generando PDF...")
        generator = BookGenerator(output_file)
        if not generator.generate_book(book_structure):
            return jsonify({'error': 'Error generando el PDF'}), 500
        
        download_url = f"/static/books/book_{session_id}.pdf"
        return jsonify({
            'download_url': download_url,
            'filename': f'LibroEducativo_{datetime.now().strftime("%Y%m%d")}.pdf'
        })
        
    except Exception as e:
        logger.error(f"Error en generación: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'db_path' in locals() and os.path.exists(db_path):
            os.remove(db_path)

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500

# Inicialización al ejecutar directamente
if __name__ == '__main__':
    setup_directories()
    app.run(host='0.0.0.0', port=5000, debug=True)