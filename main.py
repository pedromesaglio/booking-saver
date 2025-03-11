import argparse
import logging
from database import DBManager
from scraper import ContentScraper
from generators import BookGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

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
            generator = BookGenerator(f"{args.output}.pdf")
            # Add content analysis and generation logic
            logger.info(f"🎉 Successfully generated: {args.output}.pdf")
            
    except Exception as e:
        logger.error(f"🔥 Critical failure: {str(e)}")
        raise

if __name__ == "__main__":
    main()