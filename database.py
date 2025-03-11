from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index, Enum, func
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
    category = Column(Enum('teoría', 'práctica', 'caso_real', name='category_types'))
    level = Column(Enum('básico', 'intermedio', 'experto', name='level_types'))
    chapter = Column(String(50))

    __table_args__ = (
        Index('ix_url', 'url'),
        Index('ix_chapter_level', 'chapter', 'level'),
    )

class DBManager:
    def __init__(self, db_name='education.db'):
        self.engine = create_engine(f'sqlite:///{db_name}', connect_args={'timeout': 15})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    @contextlib.contextmanager
    def session_scope(self):
        """Manejador de contexto transaccional seguro"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en transacción: {str(e)}", exc_info=True)
            raise
        finally:
            session.close()
    
    def article_exists(self, url):
        """Verifica si una URL ya existe en la base de datos"""
        with self.session_scope() as session:
            return session.query(Article).filter_by(url=url).first() is not None
    
    def save_article(self, article_data):
        """Guarda un nuevo artículo con validación completa"""
        try:
            # Validar campos requeridos
            required_fields = ['title', 'content', 'url']
            for field in required_fields:
                if field not in article_data:
                    raise ValueError(f"Campo obligatorio faltante: {field}")

            with self.session_scope() as session:
                # Procesar título
                title = article_data['title']
                if len(title) > 500:
                    logger.warning(f"Título truncado: {title[:497]}...")
                    title = title[:500]

                # Procesar fecha
                date_obj = None
                if article_data.get('date'):
                    try:
                        date_obj = datetime.fromisoformat(article_data['date'])
                    except (ValueError, TypeError):
                        logger.warning("Formato de fecha inválido, ignorando fecha")
                
                # Crear objeto Article
                article = Article(
                    title=title,
                    content=article_data['content'],
                    url=article_data['url'],
                    date=date_obj,
                    category=article_data.get('category'),
                    level=article_data.get('level'),
                    chapter=article_data.get('chapter')
                )
                
                session.add(article)
                return True
        except Exception as e:
            logger.error(f"Error guardando artículo: {str(e)}", exc_info=True)
            return False
    
    def get_all_articles(self):
        """Obtiene todos los artículos serializados"""
        with self.session_scope() as session:
            try:
                articles = session.query(Article).all()
                return [{
                    'id': art.id,
                    'title': art.title,
                    'content': art.content,
                    'url': art.url,
                    'date': art.date.isoformat() if art.date else None,
                    'category': art.category,
                    'level': art.level,
                    'chapter': art.chapter
                } for art in articles]
            except Exception as e:
                logger.error(f"Error obteniendo artículos: {str(e)}")
                return []
    
    def count_articles(self):
        """Cuenta el total de artículos"""
        with self.session_scope() as session:
            return session.query(Article).count()
    
    def get_level_distribution(self):
        """Genera estadísticas de distribución por nivel"""
        with self.session_scope() as session:
            try:
                result = session.query(
                    Article.level,
                    func.count(Article.level)
                    .group_by(Article.level)
                    .all())
                return {level: count for level, count in result}
            except Exception as e:
                logger.error(f"Error generando estadísticas: {str(e)}")
                return {}
    
    def get_articles_by_chapter(self, chapter):
        """Obtiene artículos por capítulo"""
        with self.session_scope() as session:
            return session.query(Article).filter_by(chapter=chapter).all()