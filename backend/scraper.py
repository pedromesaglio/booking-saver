import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import time
import random
import spacy
from transformers import pipeline, AutoTokenizer
from backend.config import BASE_URL, SELECTORS, MAX_PAGES
from backend.database import DBManager

logger = logging.getLogger(__name__)

class ContentScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.session = self._configure_session()
        self.nlp = self._load_spacy_model()
        self.question_generator = self._init_question_generator()
    
    def _configure_session(self):
        """Configura la sesión HTTP con headers y parámetros de seguridad"""
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
        """Carga el modelo de procesamiento de lenguaje en español"""
        try:
            return spacy.load("es_core_news_sm")
        except OSError:
            logger.error("Modelo de español no instalado. Ejecuta: python -m spacy download es_core_news_sm")
            raise
    
    def _init_question_generator(self):
        """Configura el generador de preguntas de Hugging Face"""
        try:
            tokenizer = AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")
            return pipeline(
                "text2text-generation",
                model="mrm8488/t5-base-finetuned-question-generation-ap",
                tokenizer=tokenizer,
                device=-1  # Usar CPU
            )
        except Exception as e:
            logger.error(f"Error inicializando generador de preguntas: {str(e)}")
            raise
    
    def scrape_articles(self, max_articles=100):
        """Flujo principal de extracción de artículos"""
        try:
            article_urls = self._discover_articles()
            logger.info(f"🔍 Artículos descubiertos: {len(article_urls)}")
            
            success_count = 0
            for idx, url in enumerate(article_urls[:max_articles], 1):
                try:
                    if not self.db.article_exists(url):
                        if self._process_article(url):
                            success_count += 1
                        self._random_delay()
                    
                    if idx % 10 == 0:
                        logger.info(f"📊 Progreso: {idx}/{min(len(article_urls), max_articles)}")
                
                except Exception as e:
                    logger.error(f"Error procesando artículo {idx}: {str(e)}", exc_info=True)
                    continue
            
            logger.info(f"✅ Extracción completada. Artículos nuevos: {success_count}")
            return True
        except Exception as e:
            logger.error(f"🔥 Error crítico en el scraping: {str(e)}")
            return False
    
    def _discover_articles(self):
        """Descubre URLs de artículos mediante paginación"""
        urls = []
        next_page_url = BASE_URL
        page_count = 0
        
        while page_count < MAX_PAGES and next_page_url:
            try:
                soup = self._get_page_content(next_page_url)
                if not soup:
                    break
                
                # Extraer URLs de artículos
                new_urls = [
                    urljoin(BASE_URL, a['href'])
                    for article in soup.select(SELECTORS['articles'])
                    if (a := article.select_one('a[href]')) and a.has_attr('href')
                ]
                urls.extend(new_urls)
                
                # Encontrar siguiente página
                next_page_url = self._find_next_page(soup)
                page_count += 1
            
            except Exception as e:
                logger.error(f"Error en página {page_count}: {str(e)}")
                break
        
        return list(set(urls))  # Eliminar duplicados
    
    def _process_article(self, url):
        """Procesa un artículo individual"""
        try:
            soup = self._get_page_content(url)
            if not soup:
                return False
            
            article_data = self._parse_article_content(soup, url)
            return self.db.save_article(article_data)
        
        except Exception as e:
            logger.error(f"Error procesando {url}: {str(e)}")
            return False
    
    def _parse_article_content(self, soup, url):
        """Extrae y estructura el contenido del artículo"""
        content_element = soup.select_one(SELECTORS['content'])
        clean_content = self._clean_text(content_element)
        
        return {
            'title': self._clean_text(soup.select_one(SELECTORS['title']))[:500],  # Asegurar longitud máxima
            'content': clean_content,
            'url': url,
            'date': self._extract_publish_date(soup),
            'category': self._determine_category(clean_content),
            'level': self._determine_difficulty(clean_content),
            'chapter': None  # Asignar capítulo posteriormente
        }
    
    def _clean_text(self, element):
        """Limpia el texto HTML de elementos no deseados"""
        if not element:
            return ""
        
        # Eliminar elementos no relevantes
        for tag in element(['script', 'style', 'nav', 'footer', 'aside', 'header', 'iframe']):
            tag.decompose()
        
        return ' '.join(element.stripped_strings).strip()
    
    def _extract_publish_date(self, soup):
        """Extrae la fecha de publicación del artículo"""
        date_element = soup.select_one(SELECTORS['date'])
        if date_element and date_element.has_attr('datetime'):
            return date_element['datetime'][:10]  # Formato YYYY-MM-DD
        return ""
    
    def _determine_category(self, content):
        """Determina la categoría usando análisis de texto"""
        doc = self.nlp(content)
        
        # Contar verbos en modo imperativo
        imperative_verbs = sum(1 for token in doc if token.tag_ == 'Verb__Mood=Imp')
        
        # Buscar palabras clave de caso práctico
        case_keywords = ['caso real', 'ejemplo práctico', 'implementación']
        has_case = any(keyword in content.lower() for keyword in case_keywords)
        
        if imperative_verbs > 3:
            return 'práctica'
        elif has_case:
            return 'caso_real'  # Clave alineada con database.py
        return 'teoría'
    
    def _determine_difficulty(self, content):
        """Calcula el nivel de dificultad basado en complejidad léxica"""
        words = content.split()
        if not words:
            return 'básico'
        
        unique_words = len(set(words))
        complexity_ratio = (unique_words / len(words)) * 100
        
        if complexity_ratio < 30:
            return 'básico'
        elif complexity_ratio < 60:
            return 'intermedio'
        return 'experto'
    
    def _find_next_page(self, soup):
        """Encuentra el enlace a la siguiente página de artículos"""
        next_button = soup.select_one(SELECTORS['next_page'])
        if next_button and next_button.has_attr('href'):
            return urljoin(BASE_URL, next_button['href'])
        return None
    
    def _get_page_content(self, url):
        """Obtiene el contenido HTML de una URL"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            if len(response.text) < 2000:
                logger.warning(f"Contenido insuficiente en {url}")
                return None
            
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Error obteniendo {url}: {str(e)}")
            return None
    
    def _random_delay(self):
        """Genera un retraso aleatorio entre solicitudes"""
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