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
        self.content_analyzer = ContentAnalyzer()

    def _configure_session(self):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9"
        })
        return session

    def _load_spacy_model(self):
        try:
            return spacy.load("es_core_news_sm")
        except OSError:
            logger.error("Spanish language model not found. Run: python -m spacy download es_core_news_sm")
            raise

    def _init_question_generator(self):
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                "MarcBrun/questgen_es",
                use_fast=False
            )
            return pipeline(
                "text2text-generation",
                model="MarcBrun/questgen_es",
                tokenizer=tokenizer,
                framework="pt"
            )
        except Exception as e:
            logger.error(f"Failed to initialize question generator: {str(e)}")
            raise

    def scrape_articles(self, max_articles=100):
        try:
            article_urls = self._discover_articles()
            logger.info(f"Found {len(article_urls)} potential articles")
            
            success_count = 0
            for idx, url in enumerate(article_urls[:max_articles], 1):
                if self._process_article(url):
                    success_count += 1
                self._random_delay()
                
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{min(len(article_urls), max_articles)}")
            
            logger.info(f"Scraping complete. Saved {success_count} new articles")
            return True
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return False

    def analyze_content(self):
        """Analyze and structure scraped content for book generation"""
        articles = self.db.get_all_articles()
        return self.content_analyzer.structure_content(articles)

    def _discover_articles(self):
        urls = []
        next_page_url = BASE_URL
        pages_crawled = 0
        
        while pages_crawled < MAX_PAGES and next_page_url:
            try:
                soup = self._get_page_content(next_page_url)
                if not soup:
                    break
                
                urls.extend(self._extract_article_links(soup))
                next_page_url = self._find_next_page(soup)
                pages_crawled += 1
            
            except Exception as e:
                logger.error(f"Error crawling page {pages_crawled}: {str(e)}")
                break
        
        return list(set(urls))

    def _process_article(self, url):
        if self.db.article_exists(url):
            logger.debug(f"Skipping existing article: {url}")
            return False
        
        try:
            soup = self._get_page_content(url)
            if not soup:
                return False
            
            article_data = self._parse_article_content(soup, url)
            self.db.save_article(article_data)
            return True
            
        except Exception as e:
            logger.error(f"Error processing article: {url} - {str(e)}")
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
        for tag in element(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        return ' '.join(element.stripped_strings).strip()

    def _extract_publish_date(self, soup):
        date_element = soup.select_one(SELECTORS['date'])
        return date_element.get('datetime', '')[:10] if date_element else ""

    def _determine_category(self, content_element):
        content = self._clean_text(content_element)
        doc = self.nlp(content)
        imperative_verbs = sum(1 for token in doc if token.tag_ == 'Verb__Mood=Imp|Number=Sing|Person=2')
        return 'practice' if imperative_verbs > 3 else 'theory'

    def _determine_difficulty(self, content_element):
        content = self._clean_text(content_element)
        words = content.split()
        unique_terms = len(set(words))
        complexity_score = (unique_terms / len(words)) * 100
        return 'basic' if complexity_score < 30 else 'intermediate' if complexity_score < 60 else 'expert'

    def _random_delay(self):
        time.sleep(random.uniform(1.5, 4.0))

    def _get_page_content(self, url):
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to retrieve {url}: {str(e)}")
            return None

    def _extract_article_links(self, soup):
        return [urljoin(BASE_URL, a['href']) for article in soup.select(SELECTORS['articles']) 
                if (a := article.select_one('a[href]'))]

    def _find_next_page(self, soup):
        next_btn = soup.select_one(SELECTORS['next_page'])
        return urljoin(BASE_URL, next_btn['href']) if next_btn else None

class ContentAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='spanish',
            ngram_range=(1, 2)
        )
        self.clusterer = KMeans(
            n_clusters=5,  # 5 main topics
            random_state=42,
            n_init=10
        )

    def structure_content(self, articles):
        """Organize content into educational structure"""
        try:
            # Cluster articles into main topics
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
            logger.error(f"Content analysis failed: {str(e)}")
            return {}

    def _extract_main_topics(self, articles):
        """Identify main topics using TF-IDF and clustering"""
        texts = [f"{art.title} {art.content}" for art in articles]
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        self.clusterer.fit(tfidf_matrix)
        
        # Get top terms for each cluster
        terms = self.vectorizer.get_feature_names_out()
        topics = []
        for i in range(self.clusterer.n_clusters):
            centroid = self.clusterer.cluster_centers_[i]
            top_terms = terms[np.argsort(centroid)[::-1][:3]]
            topics.append(", ".join(top_terms))
        
        return topics

    def _categorize_articles(self, chapter, articles, topic):
        """Categorize articles into chapter sections"""
        for art in articles:
            if topic.lower() in art.content.lower():
                if art.category == 'theory':
                    chapter['theory'].append(self._format_theory(art))
                elif art.category == 'practice':
                    chapter['practice'].append(self._format_practice(art))
                else:
                    chapter['case_study'].append(self._format_case_study(art))

    def _generate_chapter_quizzes(self, topic):
        """Generate assessment questions for each chapter"""
        try:
            return [{
                'question': self._generate_question(topic),
                'answer_hint': f"Review section: {topic}"
            } for _ in range(EDUCATIONAL_STRUCTURE['assessment']['questions_per_chapter'])]
        except Exception as e:
            logger.error(f"Quiz generation failed: {str(e)}")
            return []

    def _generate_question(self, text):
        """Generate educational question using AI"""
        return self.question_generator(
            f"generar pregunta sobre: {text[:500]}",
            max_length=100,
            num_return_sequences=1
        )[0]['generated_text']

    def _format_theory(self, article):
        """Format theoretical content"""
        return {
            'title': article.title,
            'content': article.content[:1000] + "...",
            'key_concepts': self._extract_entities(article.content)
        }

    def _format_practice(self, article):
        """Format practical content"""
        return {
            'title': article.title,
            'steps': self._extract_steps(article.content),
            'materials': self._extract_materials(article.content)
        }

    def _format_case_study(self, article):
        """Format case study content"""
        return {
            'title': article.title,
            'context': article.content[:500],
            'results': self._extract_results(article.content)
        }

    def _extract_entities(self, text):
        """Extract key entities from text"""
        doc = self.nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ in ['ORG', 'TEC', 'PLANT']][:5]

    def _extract_steps(self, text):
        """Extract procedural steps"""
        doc = self.nlp(text)
        return [sent.text for sent in doc.sents if "paso" in sent.text.lower()][:5]

    def _extract_materials(self, text):
        """Extract mentioned materials"""
        doc = self.nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ == 'PRODUCT']

    def _extract_results(self, text):
        """Extract numerical results"""
        doc = self.nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ == 'PERCENT']