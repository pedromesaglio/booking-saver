import os
import logging
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from backend.config import EDUCATIONAL_STRUCTURE

logger = logging.getLogger(__name__)

class BookGenerator:
    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        self.styles = self._create_styles()
        logger.info(f"Ruta completa del PDF: {self.filename}")

    def _create_styles(self):
        """Configura estilos personalizados con validación robusta"""
        styles = getSampleStyleSheet()
        
        # Estilo para objetivos de aprendizaje
        if 'LearningObjective' not in styles:
            styles.add(ParagraphStyle(
                name='LearningObjective',
                fontSize=12,
                textColor=colors.HexColor("#3A7D44"),
                spaceAfter=15,
                leading=14
            ))
        
        # Estilo para viñetas personalizadas
        if 'CustomBullet' not in styles:
            styles.add(ParagraphStyle(
                name='CustomBullet',
                parent=styles['BodyText'],
                leftIndent=10,
                bulletIndent=0,
                spaceAfter=5,
                bulletFontName='Helvetica',
                bulletFontSize=10
            ))
        
        return styles

    def generate_book(self, structure):
        """Genera el libro PDF con manejo profesional de errores"""
        if not structure:
            logger.error("No hay datos para generar el libro")
            raise ValueError("La estructura del libro está vacía")
        
        try:
            logger.info(f"Iniciando generación de PDF con {len(structure)} capítulos")
            
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
            
            for chapter_title, sections in structure.items():
                logger.debug(f"Procesando capítulo: {chapter_title}")
                try:
                    chapter_content = self._create_chapter(chapter_title, sections)
                    elements += chapter_content
                except Exception as e:
                    logger.error(f"Error en capítulo {chapter_title}: {str(e)}")
                    continue
            
            logger.info("Construyendo documento PDF...")
            doc.build(elements)
            logger.info(f"✅ PDF generado exitosamente en: {self.filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error crítico al generar PDF: {str(e)}")
            if os.path.exists(self.filename):
                os.remove(self.filename)
                logger.warning("Se eliminó archivo PDF incompleto")
            return False

    def _create_cover(self):
        """Diseño de portada profesional"""
        table_style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2A5D34")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ])
        
        return [
            Paragraph("Guía Completa de Cultivo", self.styles['Title']),
            Spacer(1, 40),
            self._create_learning_objectives_table(table_style),
            PageBreak()
        ]

    def _create_learning_objectives_table(self, style):
        """Tabla de objetivos de aprendizaje con validación"""
        try:
            table_data = []
            for level in ['basic', 'intermediate', 'expert']:
                config = EDUCATIONAL_STRUCTURE['learning_levels'][level]
                table_data.append([
                    config['icon'],
                    Paragraph(
                        f"<b>{config['description']}</b><br/>" + 
                        "<br/>".join(config['objectives']), 
                        self.styles['LearningObjective']
                    )  # ¡Paréntesis cerrado correctamente!
                ])
            return Table(
                table_data, 
                colWidths=[20*mm, 150*mm],
                style=style
            )
        except KeyError as e:
            logger.error(f"Error en estructura de niveles: {str(e)}")
            raise

    def _create_chapter(self, title, sections):
        """Construye estructura de capítulo con validación mejorada"""
        required_sections = ['theory', 'practice', 'case_study']
        for section in required_sections:
            if section not in sections:
                logger.warning(f"Capítulo '{title}' sin sección: {section}")
                sections[section] = []
        
        chapter_elements = [
            Paragraph(title, self.styles['Heading1']),
            Spacer(1, 20)
        ]
        
        # Sección Teórica
        chapter_elements += self._create_section(
            EDUCATIONAL_STRUCTURE['chapter_sections']['theory']['title'],
            sections['theory']
        )
        
        # Sección Práctica
        chapter_elements += self._create_section(
            EDUCATIONAL_STRUCTURE['chapter_sections']['practice']['title'],
            sections['practice'],
            style='CustomBullet'
        )
        
        # Casos de Estudio
        chapter_elements += self._create_section(
            EDUCATIONAL_STRUCTURE['chapter_sections']['case_study']['title'],
            sections['case_study']
        )
        
        # Evaluación (opcional)
        if 'quizzes' in sections and sections['quizzes']:
            chapter_elements += self._create_assessment(sections['quizzes'])
        
        return chapter_elements + [PageBreak()]

    def _create_section(self, title, content, style='BodyText'):
        """Crea sección con contenido validado"""
        if not content:
            logger.warning(f"Sección '{title}' vacía")
            return []
            
        section_elements = [
            Paragraph(title, self.styles['Heading2']),
            Spacer(1, 10)
        ]
        
        for item in content:
            text = item.get('content', 'Contenido no disponible') if isinstance(item, dict) else str(item)
            section_elements.append(Paragraph(f"• {text}", self.styles[style]))
            section_elements.append(Spacer(1, 5))
                
        return section_elements

    def _create_assessment(self, quizzes):
        """Crea evaluación con preguntas validadas"""
        if not quizzes:
            logger.warning("No hay preguntas de evaluación")
            return []
            
        assessment = [
            Paragraph(EDUCATIONAL_STRUCTURE['assessment']['quiz_header'], self.styles['Heading3']),
            Spacer(1, 15)
        ]
        
        for idx, quiz in enumerate(quizzes, 1):
            question = quiz.get('question', 'Pregunta no disponible')
            assessment.append(Paragraph(f"{idx}. {question}", self.styles['Normal']))
            assessment.append(Spacer(1, 10))
            
        return assessment