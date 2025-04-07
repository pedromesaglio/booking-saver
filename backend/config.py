SELECTORS = {
    'articles': [
        'article', 'div.post', '.post', '.entry', '.blog-post', '.post-item',
        '.post-list-item', '[itemprop="blogPost"]', '.story', '.card',
        '.content-item', 'div.article', 'div.entry-content', 'li.post',
        'li.entry', 'section.content', 'div.main-content', 'div[class*="post"]',
        'div[class*="entry"]'
    ],
    'article_link': [
        'a.entry-title-link', 'a.post-title', 'h2 > a', 'h3 > a', 'a.more-link',
        'a.read-more', 'a[rel="bookmark"]', 'a.article-link', 'a.story-link',
        'a[itemprop="url"]', 'a.title-link', 'a.headline-link', 'div.post-header > a',
        'a[href*="/blog/"]', 'a[href*="/post/"]'
    ],
    'title': [
        'h1', 'h1.entry-title', 'h1.post-title', 'h1[itemprop="headline"]',
        'header h1', 'div.post-header h1', 'title', '.post-title', '.entry-title',
        '.headline', 'h1.title', 'h1.blog-title'
    ],
    'content': [
        'div.entry-content', 'div.post-content', 'div.article-body',
        'div.content-area', '[itemprop="articleBody"]', 'div.main-content',
        'section.content', 'article > div', 'div.content', 'div.body-content',
        'div.post-body', 'div.entry-text', 'div.rich-text', 'div#content'
    ],
    'date': [
        'time.entry-date', 'span.post-date', 'time[datetime]', 'time.published',
        'time.updated', 'div.date', 'span.date', 'meta[itemprop="datePublished"]',
        'div.timestamp', 'small.date', 'div.post-meta > time'
    ],
    'next_page': [
        'a.next', 'li.next > a', 'a.pagination-next', 'link[rel="next"]',
        'a[aria-label="Next"]', 'a:contains("Siguiente")', 'a:contains("Next")',
        'button.load-more'
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