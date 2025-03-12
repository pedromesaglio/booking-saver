BASE_URL = "https://cultivoloco.com.ar/"
OUTPUT_FILENAME = "libro_educativo"
MAX_PAGES = 20

EDUCATIONAL_STRUCTURE = {
    "learning_levels": {
        "basic": {
            "icon": "🌱",
            "description": "Fundamentos Esenciales",
            "color": "#2A5D34",
            "objectives": [
                "Comprender conceptos básicos de cultivo",
                "Identificar herramientas necesarias",
                "Aprender preparación de suelos"
            ]
        },
        "intermediate": {
            "icon": "🌿",
            "description": "Técnicas Avanzadas",
            "color": "#5B8F68",
            "objectives": [
                "Dominar sistemas de riego",
                "Aplicar fertilización orgánica",
                "Control de plagas natural"
            ]
        },
        "expert": {
            "icon": "🌳",
            "description": "Métodos Expertos",
            "color": "#3A7D44",
            "objectives": [
                "Diseñar sistemas hidropónicos",
                "Optimizar producción a escala",
                "Manejo avanzado de cosechas"
            ]
        }
    },
    "chapter_sections": {
        "theory": {
            "title": "📚 Teoría Esencial",
            "elements": ["conceptos", "definiciones", "principios"]
        },
        "practice": {
            "title": "🛠️ Práctica Guiada",
            "elements": ["paso a paso", "materiales", "consejos"]
        },
        "case_study": {
            "title": "🌍 Caso Real",
            "elements": ["contexto", "implementación", "resultados"]
        }
    },
    "assessment": {
        "quiz_header": "📝 Auto-Evaluación",
        "questions_per_chapter": 3
    }
}

SELECTORS = {
    "articles": "article.post-item, article.latest-posts-list",
    "title": "h1.entry-title, h1.single-title",
    "content": "div.entry-content, div.post-content",
    "date": "time.entry-date, span.post-date",
    "next_page": "a.next.page-numbers, li.next a"
}