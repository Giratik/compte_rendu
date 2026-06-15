import streamlit as st
import os
from docx import Document
import fitz  # PyMuPDF
from PIL import Image

def get_pdf_images(file_path):
    """Convertit les pages d'un PDF en une liste d'images PIL"""
    images = []
    try:
        # Ouvrir le document PDF
        pdf_document = fitz.open(file_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            # Utiliser une matrice pour augmenter la résolution de l'image (zoom 2x)
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            
            # Convertir le format de PyMuPDF vers une image PIL
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images
    except Exception as e:
        return f"Erreur lors de la lecture du PDF: {str(e)}"

def read_docx(file_path):
    """Read text content from a Word document"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error reading Word document: {str(e)}"

def read_txt(file_path):
    """Read text content from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading text file: {str(e)}"

def get_document_files(directory):
    """Get list of Word, PDF, and text files from the specified directory"""
    document_files = []
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.pdf', '.docx', '.txt')):
                document_files.append(filename)
    return sorted(document_files)

def render_manuel():
    st.title("📚 Manuel et Documentation")
    st.markdown("""
    <style>
    .document-viewer {
        border: 1px solid #2a2d35;
        border-radius: 8px;
        padding: 1.5rem;
        background-color: #13161d;
        min-height: 400px;
        max-height: 600px;
        overflow-y: auto;
    }
    .document-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #2a2d35;
    }
    .file-selector {
        margin-bottom: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Path to the ressource directory
    ressource_dir = "ressource"

    # Get available document files
    document_files = get_document_files(ressource_dir)

    if not document_files:
        st.info("📁 Aucun document trouvé dans le dossier 'ressource'.")
        st.markdown("""
        <div style="text-align:center;padding:3rem 2rem;color:#6b7280;
                    font-family:'JetBrains Mono',monospace;font-size:0.9rem;">
            <div style="font-size:2.5rem;margin-bottom:1rem;opacity:0.4">📄</div>
            <div>Placez des fichiers Word (.docx), PDF (.pdf) ou Texte (.txt) dans le dossier :</div>
            <div style="font-size:0.8rem;margin-top:0.8rem;color:#87CEEB">
                ressource/
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # File selection
    
    selected_file = "/app/ressource/manuel_compte-rendu.pdf"


    if selected_file:
        file_path = os.path.join(ressource_dir, selected_file)
        file_ext = os.path.splitext(selected_file)[1].lower()
        clean_title = selected_file.replace('.pdf', '').replace('.docx', '').replace('.txt', '')

        if file_ext == '.pdf':
            # --- GESTION DES PDF (Images) ---
            pdf_images = get_pdf_images(file_path)
            
            if isinstance(pdf_images, str): # Cas d'erreur
                st.error(pdf_images)
            else:
                # Affichage de l'en-tête
                st.markdown(f"""
                <div class="document-header">
                    <span style="color:#87CEEB;font-size:0.8rem;font-family:'JetBrains Mono',monospace;">
                        PDF • {len(pdf_images)} pages
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # Ajout d'un slider pour contrôler la largeur (le "zoom")
                zoom_width = st.slider(
                    "🔍 Ajuster la taille d'affichage", 
                    min_value=300, 
                    max_value=1500, 
                    value=700,  # Valeur par défaut raisonnable
                    step=50
                )
                
                # Conteneur scrollable
                with st.container(height=600):
                    for i, img in enumerate(pdf_images):
                        # On utilise explicitement le paramètre `width` au lieu de `use_column_width`
                        st.image(img, width=zoom_width, caption=f"Page {i+1}")

        else:
            # --- GESTION DES DOCX ET TXT (Texte) ---
            if file_ext == '.docx':
                content = read_docx(file_path)
                file_type = "Word"
            elif file_ext == '.txt':
                content = read_txt(file_path)
                file_type = "Texte"
            else:
                content = "Format non supporté."
                file_type = "Inconnu"

            st.markdown(f"""
            <div class="document-viewer">
                <div class="document-header">
                    <h3 style="margin:0;color:#e8e4dc;font-family:'Syne',sans-serif;">{clean_title}</h3>
                    <span style="color:#87CEEB;font-size:0.8rem;font-family:'JetBrains Mono',monospace;">
                        {file_type} • {len(content.split())} mots
                    </span>
                </div>
                <div style="white-space:pre-wrap;font-family:'JetBrains Mono',monospace;
                           font-size:0.85rem;line-height:1.6;color:#d1d5db;">
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Download button
        st.markdown("<br>", unsafe_allow_html=True)
        with open(file_path, "rb") as file:
            file_bytes = file.read()

        st.download_button(
            label="⬇ Télécharger le document original",
            data=file_bytes,
            file_name=selected_file,
            mime="application/octet-stream"
        )

if __name__ == "__main__":
    render_manuel()