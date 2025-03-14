SELECTORS = {
    # Contenedores de artículos (50+ patrones comunes)
    'articles': [
        'article',  # HTML5 standard
        '.post', '.entry', '.blog-post',  # WordPress
        '.post-item', '.post-list-item',  # Jekyll/Ghost
        '[itemprop="blogPost"]',  # Schema.org
        '.story', '.card', '.content-item',  # CMS modernos
        'div.post', 'div.article', 'div.entry-content',  # Generic
        'li.post', 'li.entry',  # List-based blogs
        'section.content', 'div.main-content',  # Estructuras genéricas
        'div[class*="post"]', 'div[class*="entry"]'  # Patrones dinámicos
    ],
    
    # Enlaces a artículos (20+ variantes)
    'article_link': [
        'a.entry-title-link', 'a.post-title',
        'h2 > a', 'h3 > a',  # Títulos como enlace
        'a.more-link', 'a.read-more',  # Enlaces "Leer más"
        'a[rel="bookmark"]',  # WordPress
        'a.article-link', 'a.story-link',
        'a[itemprop="url"]',  # Schema.org
        'a.title-link', 'a.headline-link',
        'div.post-header > a',  # Envuelto en div
        'a[href*="/blog/"]', 'a[href*="/post/"]'  # Patrones de URL
    ],
    
    # Títulos (15+ patrones)
    'title': [
        'h1', 'h1.entry-title', 'h1.post-title',  # WordPress/Jekyll
        'h1[itemprop="headline"]',  # Schema.org
        'header h1', 'div.post-header h1',
        'title',  # Fallback extremo
        '.post-title', '.entry-title', '.headline',
        'h1.title', 'h1.blog-title'
    ],
    
    # Contenido principal (20+ selectores)
    'content': [
        'div.entry-content', 'div.post-content',  # WordPress
        'div.article-body', 'div.content-area',  # CMS
        '[itemprop="articleBody"]',  # Schema.org
        'div.main-content', 'section.content',
        'article > div',  # Estructura HTML5 común
        'div.content', 'div.body-content',
        'div.post-body', 'div.entry-text',
        'div.rich-text', 'div#content'  # IDs comunes
    ],
    
    # Fechas (15+ formatos)
    'date': [
        'time.entry-date', 'span.post-date',  # WordPress
        'time[datetime]',  # HTML5 datetime
        'time.published', 'time.updated',  # Schema.org
        'div.date', 'span.date',  # Clases genéricas
        'meta[itemprop="datePublished"]',  # Meta tags
        'div.timestamp', 'small.date',
        'div.post-meta > time'  # En sección de metadatos
    ],
    
    # Paginación (10+ patrones)
    'next_page': [
        'a.next', 'li.next > a',  # Clases comunes
        'a.pagination-next',  # Nomenclatura estándar
        'link[rel="next"]',  # HTML link header
        'a[aria-label="Next"]',  # ARIA labels
        'a:contains("Siguiente")', 'a:contains("Next")',  # Texto del enlace
        'button.load-more'  # Paginación AJAX
    ]
}

# Estructura educativa para generación de libros
EDUCATIONAL_STRUCTURE = {
    "learning_levels": {
        "básico": {
            "icon": "🌱",
            "description": "Fundamentos Esenciales",
            "color": "#2A5D34",
            "objectives": [
                "Comprender conceptos básicos",
                "Identificar componentes clave",
                "Aprender fundamentos teóricos"
            ]
        },
        "intermedio": {
            "icon": "🌿",
            "description": "Técnicas Aplicadas",
            "color": "#5B8F68",
            "objectives": [
                "Implementar soluciones prácticas",
                "Resolver problemas comunes",
                "Desarrollar habilidades técnicas"
            ]
        },
        "experto": {
            "icon": "🌳",
            "description": "Métodos Avanzados",
            "color": "#3A7D44",
            "objectives": [
                "Dominar técnicas especializadas",
                "Optimizar procesos complejos",
                "Diseñar soluciones innovadoras"
            ]
        }
    },
    "chapter_sections": {
        "teoría": {
            "title": "📚 Base Teórica",
            "elements": ["conceptos", "definiciones", "principios", "fundamentos"]
        },
        "práctica": {
            "title": "🛠️ Aplicación Práctica",
            "elements": ["paso a paso", "ejemplos", "ejercicios", "demostraciones"]
        },
        "caso_real": {
            "title": "🌍 Casos de Estudio",
            "elements": ["contexto", "implementación", "resultados", "análisis"]
        }
    },
    "assessment": {
        "quiz_header": "📝 Evaluación de Conocimientos",
        "questions_per_chapter": 3,
        "question_types": ["selección múltiple", "verdadero/falso", "relacionar columnas"]
    }
}