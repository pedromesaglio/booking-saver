from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from config import EDUCATIONAL_STRUCTURE

class BookGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.styles = self._create_styles()
    
    def _create_styles(self):
        """Corregido: Mejorado estilos y añadido estilo para viñetas"""
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='LearningObjective',
            fontSize=12,
            textColor=colors.HexColor("#3A7D44"),
            spaceAfter=15
        ))
        # Añadido estilo para listas
        styles.add(ParagraphStyle(
            name='Bullet',
            parent=styles['BodyText'],
            leftIndent=10,
            spaceAfter=5,
            bulletIndent=0,
            bulletFontName='Helvetica',
            bulletFontSize=10
        ))
        return styles
    
    def generate_book(self, structure):
        """Corregido: Añadidos márgenes al documento"""
        doc = SimpleDocTemplate(
            self.filename,
            pagesize=A4,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        elements = []
        
        elements += self._create_cover()
        
        for chapter, sections in structure.items():
            elements += self._create_chapter(chapter, sections)
        
        doc.build(elements)
    
    def _create_cover(self):
        """Corregido: Mejorado formato de la tabla"""
        table_style = TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ])
        
        return [
            Paragraph("Educational Cultivation Guide", self.styles['Title']),
            Spacer(1, 40),
            self._create_learning_objectives_table(table_style),
            PageBreak()
        ]
    
    def _create_learning_objectives_table(self, style):
        """Corregido: Añadido estilo a la tabla"""
        table_data = []
        for level in ['basic', 'intermediate', 'expert']:
            config = EDUCATIONAL_STRUCTURE['learning_levels'][level]
            table_data.append([
                config['icon'],
                Paragraph(
                    f"<b>{config['description']}</b>\n" + "\n".join(config['objectives']), 
                    self.styles['BodyText']
                )
            ])
        return Table(table_data, 
                   colWidths=[20*mm, 150*mm],
                   style=style)
    
    def _create_chapter(self, title, sections):
        """Corregido: Validación de secciones"""
        chapter = [
            Paragraph(title, self.styles['Heading1']),
            Spacer(1, 20)
        ]
        
        # Validar secciones requeridas
        required_sections = ['theory', 'practice', 'case_study', 'quizzes']
        for section in required_sections:
            if section not in sections:
                raise ValueError(f"Sección faltante en capítulo {title}: {section}")
        
        chapter += self._create_section(
            EDUCATIONAL_STRUCTURE['chapter_sections']['theory']['title'],
            sections['theory']
        )
        
        chapter += self._create_section(
            EDUCATIONAL_STRUCTURE['chapter_sections']['practice']['title'],
            sections['practice'],
            bullet_style='Bullet'  # Usar estilo de viñeta personalizado
        )
        
        chapter += self._create_section(
            EDUCATIONAL_STRUCTURE['chapter_sections']['case_study']['title'],
            sections['case_study']
        )
        
        chapter += self._create_assessment(sections['quizzes'])
        
        return chapter + [PageBreak()]
    
    def _create_section(self, title, content, bullet_style='BodyText'):
        """Corregido: Usar estilo de viñeta apropiado"""
        section = [
            Paragraph(title, self.styles['Heading2']),
            Spacer(1, 10)
        ]
        for item in content:
            # Usar estilo con viñetas automáticas
            section.append(Paragraph(f"• {item}", self.styles[bullet_style]))
            section.append(Spacer(1, 5))
        return section
    
    def _create_assessment(self, quizzes):
        """Corregido: Validación de estructura de preguntas"""
        if not isinstance(quizzes, list):
            raise TypeError("Las preguntas deben ser una lista")
            
        assessment = [
            Paragraph(EDUCATIONAL_STRUCTURE['assessment']['quiz_header'], self.styles['Heading3']),
            Spacer(1, 15)
        ]
        
        for idx, quiz in enumerate(quizzes, 1):
            if not isinstance(quiz, dict) or 'question' not in quiz:
                raise ValueError("Formato de pregunta inválido")
                
            assessment.append(Paragraph(f"{idx}. {quiz['question']}", self.styles['Normal']))
            assessment.append(Spacer(1, 10))
            
        return assessment