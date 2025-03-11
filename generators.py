from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from config import EDUCATIONAL_STRUCTURE

styles = getSampleStyleSheet()

class EducationalBookGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.styles = self._create_styles()
    
    def _create_styles(self):
        estilos = styles.copy()
        estilos.add(ParagraphStyle(
            name='LearningObjective',
            fontSize=12,
            textColor=colors.HexColor("#3A7D44"),
            spaceAfter=15
        ))
        return estilos
    
    def generate_book(self, structure):
        doc = SimpleDocTemplate(self.filename, pagesize=A4)
        elements = []
        
        # Portada Educativa
        elements += self._create_cover()
        
        # Contenido por Capítulo
        for chapter, sections in structure.items():
            elements += self._create_chapter(chapter, sections)
        
        doc.build(elements)
    
    def _create_cover(self):
        elements = [
            Paragraph("Libro Educativo de Cultivo", self.styles['Title']),
            Spacer(1, 40),
            self._create_learning_objectives(),
            PageBreak()
        ]
        return elements
    
    def _create_learning_objectives(self):
        table_data = []
        for level in ['basic', 'intermediate', 'expert']:
            config = EDUCATIONAL_STRUCTURE['learning_levels'][level]
            table_data.append([
                config['icon'],
                Paragraph(f"<b>{config['description']}</b>\n" + "\n".join(config['objectives']), self.styles['BodyText'])
            ])
        return Table(table_data, colWidths=[20*mm, 150*mm])
    
    def _create_chapter(self, chapter, sections):
        elements = [
            Paragraph(chapter, self.styles['Heading1']),
            Spacer(1, 20)
        ]
        
        # Teoría
        elements += self._create_section(
            EDUCATIONAL_STRUCTURE['chapter_sections']['theory']['title'],
            sections['theory']
        )
        
        # Práctica
        elements += self._create_section(
            EDUCATIONAL_STRUCTURE['chapter_sections']['practice']['title'],
            sections['practice'],
            is_practical=True
        )
        
        # Evaluación
        elements += self._create_assessment(sections['quizzes'])
        
        return elements + [PageBreak()]
    
    def _create_section(self, title, content, is_practical=False):
        section = [
            Paragraph(title, self.styles['Heading2']),
            Table([
                [Paragraph(f"• {item}", self.styles['BodyText']) for item in art['elements']],
                [Paragraph(art['content'], self.styles['Normal'])]
            ] for art in content)
        ]
        return section
    
    def _create_assessment(self, quizzes):
        return [
            Paragraph(EDUCATIONAL_STRUCTURE['assessment']['quiz_header'], self.styles['Heading3']),
            Table([
                [Paragraph(q['pregunta'], self.styles['Normal']),
                 Paragraph(q['respuesta'], self.styles['Italic'])]
                for q in quizzes
            ], colWidths=[100*mm, 80*mm])
        ]