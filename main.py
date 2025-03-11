import argparse
import logging
import subprocess
import sys
import platform
from database import DBManager
from scraper import ContentScraper
from generators import BookGenerator
from organizers import ContentOrganizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def _open_vscode(file_path):
    """Abre el archivo en VSCode con soporte multi-plataforma"""
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', '-a', 'Visual Studio Code', file_path], check=True)
        elif platform.system() == 'Windows':  # Windows
            subprocess.run(['code', file_path], shell=True, check=True)
        else:  # Linux
            subprocess.run(['code', file_path], check=True)
        logger.info(f"👉 Archivo abierto en VSCode: {file_path}")
    except Exception as e:
        logger.warning(f"No se pudo abrir en VSCode: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Educational Content Management System")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Harvest educational content from target website')
    scrape_parser.add_argument('--max', type=int, default=50, help='Maximum articles to process')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Compile educational materials into PDF')
    generate_parser.add_argument('-o', '--output', required=True, help='Output filename (without extension)')
    
    args = parser.parse_args()
    
    db = DBManager()
    
    try:
        if args.command == 'scrape':
            logger.info("🚀 Starting content harvesting...")
            scraper = ContentScraper(db)
            if scraper.scrape_articles(args.max):
                logger.info(f"✅ Successfully stored {db.count_articles()} articles")
            else:
                logger.error("❌ Content harvesting completed with errors")
        
        elif args.command == 'generate':
            logger.info("📚 Compiling educational book...")
            output_path = f"{args.output}.pdf"
            generator = BookGenerator(output_path)
            
            # Obtener y estructurar contenido
            articles = db.get_all_articles()
            if not articles:
                logger.error("No hay artículos en la base de datos")
                sys.exit(1)
                
            organizer = ContentOrganizer(articles)
            book_structure = organizer.structure_content()
            
            if not book_structure:
                logger.error("No se pudo organizar el contenido")
                sys.exit(1)
            
            # Generar y abrir PDF
            if generator.generate_book(book_structure):
                logger.info(f"🎉 PDF generado exitosamente: {output_path}")
                _open_vscode(output_path)  # Corrección clave aquí
            else:
                logger.error("Falló la generación del PDF")
                sys.exit(1)
            
    except Exception as e:
        logger.error(f"🔥 Critical failure: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()