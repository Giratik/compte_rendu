from docx import Document
from fpdf import FPDF

import io
import markdown
from docx import Document
from htmldocx import HtmlToDocx

def generer_docx(markdown_text: str):
    """
    Convertit un texte Markdown (généré par l'IA) en un vrai document Word (.docx)
    avec le formatage appliqué (Gras, Titres, Listes à puces...).
    """
    # 1. Convertir le Markdown en HTML (avec l'extension 'extra' pour gérer les tableaux et listes complexes)
    html_text = markdown.markdown(markdown_text, extensions=['extra', 'sane_lists'])

    # 2. Initialiser un document Word vierge
    doc = Document()

    # 3. Utiliser HtmlToDocx pour traduire les balises HTML en vrai formatage Word
    parser = HtmlToDocx()
    parser.add_html_to_document(html_text, doc)

    # 4. Sauvegarder le document dans un buffer virtuel (mémoire) pour l'envoyer via l'API
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer

def generer_pdf(texte_markdown):
    """Convertit le texte Markdown en fichier PDF en mémoire avec sécurités"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    
    for ligne in texte_markdown.split('\n'):
        ligne_propre = ligne.strip()
        
        # 1. Ignorer les lignes de séparation Markdown (ex: "---", "***", "___")
        # Si la ligne ne contient que ces caractères, on la zappe pour éviter le plantage
        if set(ligne_propre) <= {'-', '_', '*', ' '} and len(ligne_propre) >= 3:
            pdf.ln(4) # On fait juste un petit saut de ligne visuel à la place
            continue
            
        # 2. Nettoyer les balises Markdown de base
        ligne_propre = ligne_propre.replace('**', '').replace('#', '')
        
        # 3. Sécurité d'encodage : Helvetica ne supporte pas les emojis ou caractères rares
        # On remplace les caractères non supportés par un "?" pour éviter un crash
        ligne_propre = ligne_propre.encode('latin-1', 'replace').decode('latin-1')
        
        # 4. Écriture dans le PDF
        if ligne_propre:
            # Si le texte est vraiment trop long sans espaces (ex: très long lien URL)
            # On le coupe pour forcer l'écriture
            try:
                pdf.multi_cell(0, 6, text=ligne_propre)
            except ValueError:
                pdf.multi_cell(0, 6, text=ligne_propre[:80] + "...") # Coupe de sécurité
        else:
            pdf.ln(6) # Conserve les sauts de ligne normaux du texte
            
    return bytes(pdf.output())