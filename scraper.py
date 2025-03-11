import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import time
import random
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from transformers import pipeline, AutoTokenizer
from config import BASE_URL, SELECTORS, EDUCATIONAL_STRUCTURE, MAX_PAGES
from database import DBManager

logger = logging.getLogger(__name__)

class ContentScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.session = self._configure_session()
        self.nlp = self._load_spacy_model()
        self.question_generator = self._init_question_generator()
        self.content_analyzer = ContentAnalyzer(self)
    
    def _configure_session(self):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9",
            "Referer": BASE_URL
        })
        session.max_redirects = 3
        session.timeout = 15
        return session
    
    def _load_spacy_model(self):
        try:
            return spacy.load("es_core_news_sm")
        except OSError:
            logger.error("Modelo español de spaCy no encontrado. Ejecuta: python -m spacy download es_core_news_sm")
            raise
    
    def _init_question_generator(self):
        try:
            model_name = "mrm8488/t5-base-finetuned-question-generation-ap"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            return pipeline(
                "text2text-generation",
                model=model_name,
                tokenizer=tokenizer,
                framework="pt",
                device=-1  # Usar CPU
            )
        except Exception as e:
            logger.error(f"Error inicializando generador de preguntas: {str(e)}")
            raise
    
    def scrape_articles(self, max_articles=100):
        try:
            article_urls = self._discover_articles()
            logger.info(f"🔍 Encontradas {len(article_urls)} URLs potenciales")
            
            success_count = 0
            for idx, url in enumerate(article_urls[:max_articles], 1):
                try:
                    if self._process_article(url):
                        success_count += 1
                    self._random_delay()
                    
                    if idx % 10 == 0:
                        logger.info(f"📊 Progreso: {idx}/{min(len(article_urls), max_articles)}")
                
                except Exception as e:
                    logger.error(f"Error procesando artículo {idx}: {str(e)}")
                    continue
            
            logger.info(f"✅ Scraping completado. Artículos nuevos: {success_count}")
            return True
        except Exception as e:
            logger.error(f"🔥 Error general en scraping: {str(e)}")
            return False
    
    def _discover_articles(self):
        urls = []
        next_page_url = BASE_URL
        page_count = 0
        
        while page_count < MAX_PAGES and next_page_url:
            try:
                soup = self._get_page_content(next_page_url)
                if not soup:
                    break
                
                urls.extend(self._extract_article_links(soup))
                next_page_url = self._find_next_page(soup)
                page_count += 1
            
            except Exception as e:
                logger.error(f"Error en página {page_count}: {str(e)}")
                break
        
        return list(set(urls))
    
    def _process_article(self, url):
        if self.db.article_exists(url):
            logger.debug(f"⏩ Saltando artículo existente: {url}")
            return False
        
        try:
            soup = self._get_page_content(url)
            if not soup:
                return False
            
            article_data = self._parse_article_content(soup, url)
            self.db.save_article(article_data)
            return True
            
        except Exception as e:
            logger.error(f"Error procesando {url}: {str(e)}")
            return False
    
    def _parse_article_content(self, soup, url):
        content_element = soup.select_one(SELECTORS['content'])
        return {
            'title': self._clean_text(soup.select_one(SELECTORS['title'])),
            'content': self._clean_text(content_element),
            'url': url,
            'date': self._extract_publish_date(soup),
            'category': self._determine_category(content_element),
            'level': self._determine_difficulty(content_element),
            'chapter': None
        }
    
    def _clean_text(self, element):
        if not element:
            return ""
        for tag in element(['script', 'style', 'nav', 'footer', 'aside']):
            tag.decompose()
        return ' '.join(element.stripped_strings).strip()
    
    def _extract_publish_date(self, soup):
        date_element = soup.select_one(SELECTORS['date'])
        return date_element.get('datetime', '')[:10] if date_element else ""
    
    def _determine_category(self, content_element):
        content = self._clean_text(content_element)
        doc = self.nlp(content)
        
        # Detectar verbos en modo imperativo
        imperative_verbs = sum(1 for token in doc 
                             if token.tag_ == 'Verb__Mood=Imp|Number=Sing|Person=2')
        
        # Detectar palabras clave de caso de estudio
        case_study_keywords = ['caso', 'estudio', 'ejemplo', 'implementación']
        has_case_study = any(keyword in content.lower() 
                           for keyword in case_study_keywords)
        
        if imperative_verbs > 3:
            return 'practice'
        elif has_case_study:
            return 'case_study'
        return 'theory'
    
    def _determine_difficulty(self, content_element):
        content = self._clean_text(content_element)
        words = content.split()
        unique_terms = len(set(words))
        complexity_score = (unique_terms / len(words)) * 100
        
        if complexity_score < 30:
            return 'basic'
        elif complexity_score < 60:
            return 'intermediate'
        return 'advanced'
    
    def _random_delay(self):
        time.sleep(random.uniform(1.5, 4.0))
    
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