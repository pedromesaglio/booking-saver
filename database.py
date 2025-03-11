from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import logging
import contextlib

logger = logging.getLogger(__name__)
Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(2000), unique=True, nullable=False)
    date = Column(DateTime)
    category = Column(String(50))  # teoría/práctica/caso
    level = Column(String(20))     # básico/intermedio/experto
    chapter = Column(String(50))   # tema principal

    __table_args__ = (
        Index('ix_url', 'url'),
        Index('ix_chapter_level', 'chapter', 'level'),
    )

class DBManager:
    def __init__(self, db_name='education.db'):
        self.engine = create_engine(f'sqlite:///{db_name}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    @contextlib.contextmanager
    def session_scope(self):
        """Proporciona un contexto transaccional para operaciones de base de datos"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en DB: {str(e)}")
            raise
        finally:
            session.close()
    
    def article_exists(self, url):
        """Verifica si un artículo existe por su URL"""
        with self.session_scope() as session:
            return session.query(Article).filter_by(url=url).first() is not None
    
    def save_article(self, article_data):
        """Guarda un nuevo artículo en la base de datos"""
        with self.session_scope() as session:
            article = Article(
                title=article_data['title'][:500],
                content=article_data['content'],
                url=article_data['url'],
                date=datetime.strptime(article_data['date'], '%Y-%m-%d') if article_data['date'] else None,
                category=article_data.get('category'),
                level=article_data.get('level'),
                chapter=article_data.get('chapter')
            )
            session.add(article)
    
    def get_articles_by_chapter(self, chapter):
        """Obtiene todos los artículos de un capítulo específico"""
        with self.session_scope() as session:
            return session.query(Article).filter_by(chapter=chapter).all()
    
    def get_all_articles(self):
        """Obtiene todos los artículos de la base de datos"""
        with self.session_scope() as session:
            return session.query(Article).all()
    
    def count_articles(self):
        """Cuenta el número total de artículos almacenados"""
        with self.session_scope() as session:
            return session.query(Article).count()