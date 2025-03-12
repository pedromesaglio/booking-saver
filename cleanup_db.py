from database import DBManager, Article
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_invalid_entries():
    db = DBManager()
    with db.session_scope() as session:
        # Eliminar entradas con categorías inválidas
        deleted = session.query(Article).filter(
            ~Article.category.in_(['teoría', 'práctica', 'caso_real'])
        ).delete(synchronize_session=False)
        logger.info(f"Entradas eliminadas: {deleted}")

if __name__ == "__main__":
    clean_invalid_entries()