import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class ContentOrganizer:
    def __init__(self, articles_data):
        self.articles_data = articles_data
    
    def structure_content(self):
        try:
            chapters = defaultdict(lambda: {
                'theory': [],
                'practice': [],
                'case_study': [],
                'quizzes': []
            })
            
            for article in self.articles_data:
                chapter_key = article['chapter'] if article['chapter'] else "General"
                category = article['category'].lower() if article['category'] else 'theory'
                
                if category == 'teoría':
                    chapters[chapter_key]['theory'].append({
                        'title': article['title'],
                        'content': article['content']
                    })
                elif category == 'práctica':
                    chapters[chapter_key]['practice'].append({
                        'title': article['title'],
                        'content': article['content']
                    })
                else:
                    chapters[chapter_key]['case_study'].append({
                        'title': article['title'],
                        'content': article['content']
                    })
            
            # Generar quizzes básicos
            for chapter_key, content in chapters.items():
                content['quizzes'] = [{
                    'question': f"¿Qué has aprendido sobre {chapter_key}?",
                    'answer_hint': "Revisa las secciones correspondientes"
                } for _ in range(3)]
            
            return dict(chapters)
            
        except Exception as e:
            logger.error(f"Error organizando contenido: {str(e)}")
            return {}