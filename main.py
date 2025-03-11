import argparse
import logging
from database import DBManager
from scraper import EducationalScraper
from generators import EducationalBookGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Sistema de Generación de Libros Educativos")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Comando para scraping
    scrape_parser = subparsers.add_parser('scrape', help='Extraer contenido del blog')
    scrape_parser.add_argument('--max', type=int, default=50, help='Máximo de artículos')
    
    # Comando para generación
    book_parser = subparsers.add_parser('generate-book', help='Generar libro educativo')
    book_parser.add_argument('-o', '--output', required=True, help='Nombre del archivo de salida')
    
    args = parser.parse_args()
    
    db = DBManager()
    
    if args.command == 'scrape':
        logger.info("Iniciando extracción de contenido...")
        # (Implementar lógica de scraping aquí)
    
    elif args.command == 'generate-book':
        logger.info("Generando libro educativo...")
        scraper = EducationalScraper(db)
        articles = db.get_all()
        structure = scraper.analyze_content(articles)
        
        generator = EducationalBookGenerator(f"{args.output}.pdf")
        generator.generate_book(structure)
        logger.info(f"Libro generado: {args.output}.pdf")

if __name__ == "__main__":
    main()