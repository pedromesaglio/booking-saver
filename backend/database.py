from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index, Enum
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
import contextlib
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(2000), unique=True, nullable=False)
    date = Column(DateTime)
    category = Column(Enum('teoría', 'práctica', 'caso_real', name='category_types'))
    level = Column(Enum('básico', 'intermedio', 'experto', name='level_types'))
    chapter = Column(String(50))

    __table_args__ = (
        Index('ix_url', 'url'),
        Index('ix_chapter_level', 'chapter', 'level'),
    )

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', connect_args={'timeout': 15})
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self._create_tables()
    
    def _create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Tablas creadas exitosamente")
        except SQLAlchemyError as e:
            logger.error(f"Error creando tablas: {str(e)}")
            raise
    
    def __enter__(self):
        self.session = self.Session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error en transacción: {str(e)}")
            self.session.rollback()
        finally:
            self.session.close()
            self.Session.remove()
    
    def article_exists(self, url):
        return self.session.query(Article).filter_by(url=url).first() is not None
    
    def save_article(self, article_data):
        try:
            article = Article(
                title=article_data['title'][:500],
                content=article_data['content'],
                url=article_data['url'],
                date=article_data.get('date'),
                category=article_data.get('category'),
                level=article_data.get('level'),
                chapter=article_data.get('chapter')
            )
            self.session.add(article)
            return True
        except Exception as e:
            logger.error(f"Error guardando artículo: {str(e)}")
            return False
    
    def get_all_articles(self):
        try:
            return self.session.query(Article).all()
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo artículos: {str(e)}")
            return []
    
    def count_articles(self):
        return self.session.query(Article).count()