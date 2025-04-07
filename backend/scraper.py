import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging
from tqdm import tqdm
import random
import time
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from backend.config import SELECTORS
from backend.database import DBManager

logger = logging.getLogger(__name__)

class ContentScraper:
    def __init__(self, db_manager: DBManager, max_articles: int = 50):
        self.db = db_manager
        self.max_articles = max_articles
        self.session = requests.Session()
        self.driver = None  # Para Selenium
        
        # Configurar User-Agent realista
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9",
        }

    def _init_selenium(self):
        """Inicializar Selenium como fallback"""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Obtener página con 3 estrategias diferentes"""
        try:
            # Intento 1: Requests estándar
            time.sleep(random.uniform(1, 3))
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            if len(soup.find_all(SELECTORS['articles'][0])) > 0:
                return soup
                
            # Intento 2: Requests con User-Agent diferente
            self.session.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            if len(soup.find_all(SELECTORS['articles'][0])) > 0:
                return soup
                
            # Intento 3: Selenium para JavaScript
            if not self.driver:
                self._init_selenium()
                
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS['articles'][0]))
            )
            return BeautifulSoup(self.driver.page_source, 'html.parser')
            
        except Exception as e:
            logger.error(f"Error obteniendo {url}: {str(e)}")
            return None

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extraer enlaces con múltiples estrategias"""
        links = []
        
        # Probar múltiples selectores para encontrar artículos
        for selector in SELECTORS['articles']:
            articles = soup.select(selector)
            logger.info(f"🔍 Probando selector de artículos: '{selector}' - Encontrados: {len(articles)}")
            for article in articles:
                link = None
                for link_selector in SELECTORS['article_link']:
                    elem = article.select_one(link_selector)
                    if elem and (href := elem.get('href')):
                        link = urljoin(base_url, href)
                        break
                if link and link not in links:
                    links.append(link)
            if links:
                break  # Detener si se encuentran enlaces válidos
        
        # Si no se encuentran enlaces, probar selectores genéricos
        if not links:
            for link_selector in SELECTORS['article_link']:
                generic_links = [urljoin(base_url, a['href']) for a in soup.select(link_selector)]
                logger.info(f"🔍 Probando selector de enlaces genéricos: '{link_selector}' - Encontrados: {len(generic_links)}")
                links.extend(generic_links)
                if links:
                    break
        
        return list(dict.fromkeys(links))[:self.max_articles]

    def _parse_article(self, url: str) -> Optional[dict]:
        """Parsear un artículo con múltiples estrategias"""
        try:
            soup = self._get_page(url)
            if not soup:
                return None

            # Probar múltiples selectores para el título
            title = None
            for selector in SELECTORS['title']:
                if elem := soup.select_one(selector):
                    title = elem.text.strip()
                    logger.info(f"✅ Título encontrado con selector '{selector}': {title}")
                    break

            # Probar múltiples selectores para el contenido
            content = None
            for selector in SELECTORS['content']:
                if elems := soup.select(selector):
                    content = "\n".join([e.text.strip() for e in elems])
                    logger.info(f"✅ Contenido encontrado con selector '{selector}'")
                    break

            # Probar múltiples selectores para la fecha
            date = None
            for selector in SELECTORS['date']:
                if elem := soup.select_one(selector):
                    date_str = elem.text.strip()
                    date = self._parse_date(date_str)
                    logger.info(f"✅ Fecha encontrada con selector '{selector}': {date}")
                    break

            return {
                'title': title or "Título no encontrado",
                'content': content or "Contenido no disponible",
                'url': url,
                'date': date,
                'category': self._detect_category(content or ""),
                'level': self._detect_difficulty(content or "")
            }
        except Exception as e:
            logger.error(f"Error procesando {url}: {str(e)}")
            return None

    def scrape(self, base_url: str) -> bool:
        """Flujo principal de scraping mejorado"""
        parsed_url = urlparse(base_url)
        logger.info(f"🚀 Iniciando scraping en: {base_url}")
        
        try:
            logger.info("🔍 Verificando estructura del sitio web...")
            logger.info(f"Usando selectores: {SELECTORS}")
            
            soup = self._get_page(base_url)
            if not soup:
                logger.error("❌ No se pudo obtener la página inicial")
                return False

            article_urls = []
            next_page = base_url
            max_depth = 5  # Límite de páginas
            
            with tqdm(desc="🔍 Buscando artículos", unit="pág") as pbar:
                while next_page and len(article_urls) < self.max_articles and max_depth > 0:
                    current_soup = self._get_page(next_page) or soup
                    new_links = self._extract_links(current_soup, base_url)
                    article_urls.extend(new_links)
                    
                    # Paginación inteligente
                    next_page = None
                    for selector in SELECTORS['next_page']:
                        if elem := current_soup.select_one(selector):
                            next_page = urljoin(base_url, elem.get('href', ''))
                            break
                    
                    max_depth -= 1
                    pbar.update(1)
                    time.sleep(random.uniform(1, 2))

            # Procesamiento paralelo básico
            success_count = 0
            with tqdm(total=len(article_urls), desc="📥 Procesando artículos") as pbar:
                for url in article_urls:
                    if self.db.article_exists(url):
                        pbar.update(1)
                        continue
                    
                    article_data = self._parse_article(url)
                    if article_data:
                        logger.info(f"📥 Procesando artículo: {article_data['title']}")
                        if self.db.save_article(article_data):
                            success_count += 1
                    pbar.update(1)
                    time.sleep(random.uniform(0.5, 1.5))

            if not article_urls:
                logger.warning("⚠️ No se encontraron artículos en el sitio web.")

            logger.info(f"✅ Artículos nuevos guardados: {success_count}/{len(article_urls)}")
            return success_count > 0

        except Exception as e:
            logger.error(f"🔥 Error crítico: {str(e)}", exc_info=True)
            return False
        finally:
            if self.driver:
                self.driver.quit()