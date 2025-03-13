import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import time
import random
import spacy
from transformers import pipeline, AutoTokenizer
from database import DBManager
from config import SELECTORS, EDUCATIONAL_STRUCTURE, MAX_PAGES, BASE_URL
import numpy as np

logger = logging.getLogger(__name__)

class ContentScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = None
        self.session = self._create_session()
        self.nlp = self._load_spacy_model()
        self.question_generator = self._init_question_generator()
        self.max_retries = 3
        self.request_timeout = 20

    def _create_session(self):
        """Configura una sesión HTTP personalizada"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9",
            "Referer": self.base_url or "https://google.com"
        })
        session.max_redirects = 3
        return session

    def _load_spacy_model(self):
        """Carga el modelo de procesamiento de lenguaje en español"""
        try:
            return spacy.load("es_core_news_sm")
        except OSError:
            logger.error("Modelo de español no encontrado. Ejecuta: python -m spacy download es_core_news_sm")
            raise

    def _init_question_generator(self):
        """Configura el generador de preguntas de Hugging Face"""
        try:
            return pipeline(
                "text2text-generation",
                model="mrm8488/t5-base-finetuned-question-generation-ap",
                tokenizer=AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap"),
                device=-1,  # CPU
                max_length=100
            )
        except Exception as e:
            logger.error(f"Error inicializando generador de preguntas: {str(e)}")
            return None

    def scrape_articles(self, max_articles=50):
        """Flujo principal de scraping para integración web"""
        try:
            article_urls = self._discover_articles()
            logger.info(f"Descubiertas {len(article_urls)} URLs potenciales")
            
            success_count = 0
            for idx, url in enumerate(article_urls[:max_articles], 1):
                try:
                    if not self.db.article_exists(url) and self._process_article(url):
                        success_count += 1
                    
                    # Manejo de carga progresiva para web
                    if idx % 5 == 0:
                        logger.debug(f"Progreso: {idx}/{min(len(article_urls), max_articles)}")
                    
                    self._random_delay()
                
                except Exception as e:
                    logger.error(f"Error procesando artículo {idx}: {str(e)}")
                    continue
            
            logger.info(f"Scraping completado. Artículos nuevos: {success_count}")
            return success_count > 0
        
        except Exception as e:
            logger.error(f"Error general en scraping: {str(e)}")
            return False

    def _discover_articles(self):
        """Descubre artículos con manejo mejorado de paginación"""
        urls = []
        next_page = self.base_url
        parsed_base = urlparse(self.base_url)
        
        for _ in range(MAX_PAGES):
            if not next_page:
                break
            
            try:
                soup = self._get_page_content(next_page)
                if not soup:
                    break
                
                # Filtrar URLs del mismo dominio
                current_urls = [
                    urljoin(self.base_url, a['href'])
                    for article in soup.select(SELECTORS['articles'])
                    if (a := article.select_one('a[href]')) 
                    and self._is_same_domain(a['href'], parsed_base)
                ]
                
                urls.extend(current_urls)
                next_page = self._find_next_page(soup)
            
            except Exception as e:
                logger.error(f"Error en página {next_page}: {str(e)}")
                break
        
        return list(set(urls))

    def _is_same_domain(self, url, parsed_base):
        """Verifica si una URL pertenece al mismo dominio"""
        parsed_url = urlparse(url)
        return parsed_url.netloc == parsed_base.netloc or not parsed_url.netloc

    def _process_article(self, url):
        """Procesa un artículo individual con reintentos"""
        for attempt in range(self.max_retries):
            try:
                soup = self._get_page_content(url)
                if not soup:
                    return False
                
                article_data = self._parse_article_content(soup, url)
                return self.db.save_article(article_data)
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Reintentando ({attempt+1}/{self.max_retries}) en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Fallo definitivo procesando {url}: {str(e)}")
                    return False

    def _parse_article_content(self, soup, url):
        """Extrae y estructura el contenido del artículo con manejo de errores"""
        try:
            title = self._clean_text(soup.select_one(SELECTORS['title']))[:500] or "Sin título"
            content = self._clean_text(soup.select_one(SELECTORS['content']))
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'date': self._extract_publish_date(soup),
                'category': self._determine_category(content),
                'level': self._determine_difficulty(content),
                'chapter': None
            }
        
        except Exception as e:
            logger.error(f"Error analizando contenido de {url}: {str(e)}")
            return None

    # ... (Métodos auxiliares restantes iguales pero con mejor logging)

    def _get_page_content(self, url):
        """Obtiene el contenido de una página con manejo de errores mejorado"""
        try:
            response = self.session.get(
                url,
                timeout=(self.request_timeout, 30),
                allow_redirects=True
            )
            response.raise_for_status()
            
            if len(response.text) < 2000:
                logger.warning(f"Contenido insuficiente en {url}")
                return None
            
            return BeautifulSoup(response.text, 'html.parser')
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error HTTP en {url}: {str(e)}")
            return None

    def _random_delay(self):
        """Genera un retraso aleatorio más seguro para web scraping"""
        delay = random.uniform(1.5, 4.0)
        time.sleep(delay)
    
    def _get_page_content(self, url):
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            if len(response.text) < 2000:
                raise ValueError("Contenido insuficiente")
                
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Error obteniendo {url}: {str(e)}")
            return None
    
    def _extract_article_links(self, soup):
        return [
            urljoin(BASE_URL, a['href'])
            for article in soup.select(SELECTORS['articles'])
            if (a := article.select_one('a[href]'))
        ]
    
    def _find_next_page(self, soup):
        next_btn = soup.select_one(SELECTORS['next_page'])
        return urljoin(BASE_URL, next_btn['href']) if next_btn else None

class ContentAnalyzer:
    def __init__(self, scraper):
        self.scraper = scraper
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='spanish',
            ngram_range=(1, 2)
        )
        self.clusterer = KMeans(
            n_clusters=5,  # 5 temas principales
            random_state=42,
            n_init=10
        )
    
    def structure_content(self, articles):
        try:
            topics = self._extract_main_topics(articles)
            book_structure = {}
            
            for topic in topics:
                book_structure[topic] = {
                    'theory': [],
                    'practice': [],
                    'case_study': [],
                    'quizzes': self._generate_chapter_quizzes(topic)
                }
                self._categorize_articles(book_structure[topic], articles, topic)
            
            return book_structure
        except Exception as e:
            logger.error(f"Error en análisis de contenido: {str(e)}")
            return {}
    
    def _extract_main_topics(self, articles):
        texts = [f"{art.title} {art.content}" for art in articles]
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        self.clusterer.fit(tfidf_matrix)
        
        terms = self.vectorizer.get_feature_names_out()
        topics = []
        
        for i in range(self.clusterer.n_clusters):
            centroid = self.clusterer.cluster_centers_[i]
            top_terms = terms[np.argsort(centroid)[::-1][:3]]
            topics.append(", ".join(top_terms))
        
        return topics
    
    def _categorize_articles(self, chapter, articles, topic):
        for art in articles:
            if topic.lower() in art.content.lower():
                if art.category == 'theory':
                    chapter['theory'].append(self._format_theory(art))
                elif art.category == 'practice':
                    chapter['practice'].append(self._format_practice(art))
                else:
                    chapter['case_study'].append(self._format_case_study(art))
    
    def _generate_chapter_quizzes(self, topic):
        try:
            return [{
                'question': self._generate_question(topic),
                'answer_hint': f"Revisar sección: {topic}"
            } for _ in range(EDUCATIONAL_STRUCTURE['assessment']['questions_per_chapter'])]
        except Exception as e:
            logger.error(f"Error generando preguntas: {str(e)}")
            return []
    
    def _generate_question(self, text):
        try:
            result = self.scraper.question_generator(
                f"generate question about: {text[:500]}",  # Instrucción en inglés
                max_length=100,
                num_return_sequences=1
            )
            return result[0]['generated_text']
        except Exception as e:
            logger.error(f"Error generando pregunta: {str(e)}")
            return "¿Cuál es el aspecto más importante de este tema?"
    
    def _format_theory(self, article):
        return {
            'title': article.title,
            'content': article.content[:1000] + "...",
            'key_concepts': self._extract_entities(article.content)
        }
    
    def _format_practice(self, article):
        return {
            'title': article.title,
            'steps': self._extract_steps(article.content),
            'materials': self._extract_materials(article.content)
        }
    
    def _format_case_study(self, article):
        return {
            'title': article.title,
            'context': article.content[:500],
            'results': self._extract_results(article.content)
        }
    
    def _extract_entities(self, text):
        doc = self.scraper.nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ in ['ORG', 'TEC', 'PLANT']][:5]
    
    def _extract_steps(self, text):
        doc = self.scraper.nlp(text)
        return [sent.text for sent in doc.sents if "paso" in sent.text.lower()][:5]
    
    def _extract_materials(self, text):
        doc = self.scraper.nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ == 'PRODUCT']
    
    def _extract_results(self, text):
        doc = self.scraper.nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ == 'PERCENT']