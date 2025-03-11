from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
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

class DBManager:
    def __init__(self, db_name='educacion.db'):
        self.engine = create_engine(f'sqlite:///{db_name}')
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
            logger.error(f"Error DB: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_by_url(self, url):
        with self.session_scope() as session:
            return session.query(Article).filter_by(url=url).first() is not None
    
    def save_article(self, data):
        with self.session_scope() as session:
            article = Article(
                title=data['title'][:500],
                content=data['content'],
                url=data['url'],
                date=datetime.strptime(data['date'], '%Y-%m-%d') if data['date'] else None,
                category=data.get('category'),
                level=data.get('level'),
                chapter=data.get('chapter')
            )
            session.add(article)
    
    def get_for_chapter(self, chapter):
        with self.session_scope() as session:
            return session.query(Article).filter_by(chapter=chapter).all()