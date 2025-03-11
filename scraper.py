import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import time
import random
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
from transformers import pipeline
from config import BASE_URL, SELECTORS, EDUCATIONAL_STRUCTURE, MAX_PAGES
from database import DBManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Cargar modelos NLP
try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    logger.error("Modelo español de spaCy no encontrado. Ejecuta: python -m spacy download es_core_news_sm")
    raise

class BlogScraper:
    def __init__(self, db: DBManager):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9"
        })
        self.qg_pipeline = pipeline(
            "text2text-generation",
            model="mrm8488/t5-base-finetuned-question-generation-ap",
            framework="pt"
        )

    def extract_articles(self, max_articles=100):
        """Extrae artículos del blog y los guarda en la base de datos"""
        try:
            urls = self._get_article_urls()
            logger.info(f"Encontradas {len(urls)} URLs de artículos")

            for i, url in enumerate(urls[:max_articles], 1):
                if not self.db.get_by_url(url):
                    article_data = self._process_article(url)
                    if article_data:
                        self.db.save_article(article_data)
                        logger.debug(f"Artículo guardado: {article_data['title'][:50]}...")
                    time.sleep(random.uniform(1, 3))  # Evitar bloqueos
                logger.info(f"Progreso: {i}/{min(len(urls), max_articles)} artículos procesados")
            return True
        except Exception as e:
            logger.error(f"Error en la extracción: {str(e)}")
            return False

    def _get_article_urls(self):
        """Obtiene URLs de todos los artículos paginados"""
        urls = []
        next_page_url = BASE_URL
        page_count = 0

        while page_count < MAX_PAGES and next_page_url:
            try:
                soup = self._get_soup(next_page_url)
                if not soup:
                    break

                # Extraer enlaces de artículos
                article_links = soup.select(SELECTORS['articles'])
                for article in article_links:
                    link = article.select_one('a[href]')
                    if link:
                        absolute_url = urljoin(next_page_url, link['href'])
                        urls.append(absolute_url)

                # Manejar paginación
                next_button = soup.select_one(SELECTORS['next_page'])
                next_page_url = urljoin(next_page_url, next_button['href']) if next_button else None
                page_count += 1

            except Exception as e:
                logger.error(f"Error en página {page_count}: {str(e)}")
                break

        return list(set(urls))  # Eliminar duplicados

    def _process_article(self, url):
        """Procesa un artículo individual y devuelve datos estructurados"""
        try:
            soup = self._get_soup(url)
            if not soup:
                return None

            # Extraer metadatos
            title = self._clean_text(soup.select_one(SELECTORS['title']))
            content = self._clean_text(soup.select_one(SELECTORS['content']))
            date = soup.select_one(SELECTORS['date']).get('datetime', '')[:10] if soup.select_one(SELECTORS['date']) else ""

            # Análisis semántico
            doc = nlp(content)
            entities = [ent.text for ent in doc.ents if ent.label_ in ['ORG', 'TEC', 'PLANT']]
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'date': date,
                'entities': entities,
                'category': self._determine_category(content),
                'difficulty': self._determine_difficulty(content)
            }
        except Exception as e:
            logger.error(f"Error procesando {url}: {str(e)}")
            return None

    def _determine_category(self, content):
        """Clasifica el artículo en teoría/práctica/caso usando NLP"""
        doc = nlp(content)
        verb_counts = sum(1 for token in doc if token.pos_ == 'VERB')
        if verb_counts > 10:
            return 'practice'
        elif any(sentiment in content.lower() for sentiment in ['recomendamos', 'sugerencia']):
            return 'case_study'
        return 'theory'

    def _determine_difficulty(self, content):
        """Determina el nivel de dificultad del contenido"""
        word_count = len(content.split())
        unique_terms = len(set(content.split()))
        complexity_score = (unique_terms / word_count) * 100

        if complexity_score < 30:
            return 'basic'
        elif complexity_score < 60:
            return 'intermediate'
        return 'advanced'

    def _clean_text(self, element):
        """Limpia y normaliza el texto HTML"""
        if element:
            # Eliminar scripts y estilos
            for tag in element(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            return ' '.join(element.stripped_strings)
        return ""

    def _get_soup(self, url):
        """Obtiene el objeto BeautifulSoup con manejo de errores"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error HTTP en {url}: {type(e).__name__}")
            return None

class ContentAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='spanish',
            ngram_range=(1, 2)
        )
        self.kmeans = KMeans(
            n_clusters=len(EDUCATIONAL_STRUCTURE['learning_levels']),
            random_state=42,
            n_init=10
        )

    def analyze_content(self, articles):
        """Organiza el contenido para estructura educativa"""
        try:
            # 1. Análisis de temas principales
            main_topics = self._extract_main_topics(articles)
            
            # 2. Organización del contenido
            book_structure = {}
            for topic in main_topics:
                book_structure[topic] = {
                    'theory': [],
                    'practice': [],
                    'case_studies': [],
                    'quizzes': self._generate_quizzes(topic)
                }
                self._fill_chapter_content(book_structure[topic], articles, topic)
            
            return book_structure
        except Exception as e:
            logger.error(f"Error en análisis de contenido: {str(e)}")
            return {}

    def _extract_main_topics(self, articles):
        """Identifica los 5 temas principales usando TF-IDF"""
        texts = [f"{art['title']} {art['content']}" for art in articles]
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        self.kmeans.fit(tfidf_matrix)
        
        # Obtener términos más importantes por cluster
        terms = self.vectorizer.get_feature_names_out()
        topics = []
        for i in range(self.kmeans.n_clusters):
            centroid = self.kmeans.cluster_centers_[i]
            top_terms = terms[np.argsort(centroid)[::-1][:5]]
            topics.append(", ".join(top_terms))
        
        return list(set(topics))[:5]

    def _fill_chapter_content(self, chapter, articles, topic):
        """Clasifica el contenido en secciones del capítulo"""
        for art in articles:
            if topic.lower() in art['content'].lower():
                if art['category'] == 'theory':
                    chapter['theory'].append(self._format_theory(art))
                elif art['category'] == 'practice':
                    chapter['practice'].append(self._format_practice(art))
                else:
                    chapter['case_studies'].append(self._format_case_study(art))

    def _generate_quizzes(self, topic):
        """Genera preguntas de autoevaluación usando IA"""
        try:
            return [{
                'question': self._generate_question(topic),
                'answer_hint': f"Revisar sección de {topic} en el capítulo 3"
            } for _ in range(EDUCATIONAL_STRUCTURE['assessment']['questions_per_chapter'])]
        except Exception as e:
            logger.error(f"Error generando preguntas: {str(e)}")
            return []

    def _generate_question(self, text):
        """Genera una pregunta educativa usando transformers"""
        return self.qg_pipeline(
            f"generar pregunta sobre: {text[:500]}",
            max_length=100,
            num_return_sequences=1
        )[0]['generated_text']

    def _format_theory(self, article):
        """Da formato al contenido teórico"""
        return {
            'title': article['title'],
            'content': article['content'][:1000] + "...",
            'key_concepts': article['entities'][:5]
        }

    def _format_practice(self, article):
        """Da formato al contenido práctico"""
        return {
            'title': article['title'],
            'steps': self._extract_steps(article['content']),
            'materials': self._extract_materials(article['content'])
        }

    def _format_case_study(self, article):
        """Da formato a casos de estudio"""
        return {
            'title': article['title'],
            'context': article['content'][:500],
            'results': self._extract_results(article['content'])
        }

    def _extract_steps(self, content):
        """Extrae pasos de un artículo práctico"""
        doc = nlp(content)
        return [sent.text for sent in doc.sents if "paso" in sent.text.lower()][:5]

    def _extract_materials(self, content):
        """Extrae materiales mencionados"""
        doc = nlp(content)
        return [ent.text for ent in doc.ents if ent.label_ == 'PRODUCT']

    def _extract_results(self, content):
        """Extrae resultados numéricos de casos"""
        doc = nlp(content)
        return [ent.text for ent in doc.ents if ent.label_ == 'PERCENT']