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
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en transacción: {str(e)}")
            raise
        finally:
            session.close()
    
    def article_exists(self, url):
        with self.session_scope() as session:
            return session.query(Article).filter_by(url=url).first() is not None
    
    def save_article(self, article_data):
        try:
            with self.session_scope() as session:
                title = article_data['title'][:500]
                date = datetime.fromisoformat(article_data['date']) if article_data.get('date') else None
                
                article = Article(
                    title=title,
                    content=article_data['content'],
                    url=article_data['url'],
                    date=date,
                    category=article_data.get('category'),
                    level=article_data.get('level'),
                    chapter=article_data.get('chapter')
                )
                session.add(article)
                return True
        except Exception as e:
            logger.error(f"Error guardando artículo: {str(e)}")
            return False
    
    def get_all_articles(self):
        with self.session_scope() as session:
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
    
    def count_articles(self):
        with self.session_scope() as session:
            return session.query(Article).count()

    def get_level_distribution(self):
        with self.session_scope() as session:
            result = session.query(Article.level, func.count(Article.level)).group_by(Article.level).all()
            return {level: count for level, count in result}