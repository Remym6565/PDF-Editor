import fitz  # PyMuPDF
from pypdf import PdfWriter, PdfReader
import os
from PyQt6.QtGui import QImage

class PDFProcessor:
    """
    Gère toutes les opérations backend sur les fichiers PDF en utilisant PyMuPDF (fitz) et pypdf.
    """
    def __init__(self):
        self.doc = None
        self.current_file_path = None

    def create_new_pdf(self):
        """Crée un nouveau document PDF vierge."""
        self.doc = fitz.open()
        self.doc.new_page()
        self.current_file_path = None

    def open_pdf(self, file_path):
        """Ouvre un document PDF existant."""
        self.doc = fitz.open(file_path)
        self.current_file_path = file_path

    def get_page_count(self):
        """Retourne le nombre total de pages."""
        return len(self.doc) if self.doc else 0

    def get_text_blocks(self, page_number):
        """
        Extrait les blocs de texte avec leurs coordonnées ET leurs propriétés de police.
        """
        if not self.doc or page_number < 0 or page_number >= len(self.doc):
            return []
            
        page = self.doc[page_number]
        text_dict = page.get_text("dict")
        text_blocks = []

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # 0 = texte
                continue

            bbox = block["bbox"]
            full_text = ""
            # Propriétés du premier span (style dominant du bloc)
            font_name = "Helvetica"
            font_size = 12.0
            font_color = (0, 0, 0)
            is_bold = False
            is_italic = False
            got_first_span = False

            last_y0 = None
            last_x1 = None
            for line in block.get("lines", []):
                y0 = line.get("bbox", [0,0,0,0])[1]
                
                # S'il y a déjà du texte, on décide si on ajoute un espace ou un \n
                if full_text:
                    if last_y0 is not None and abs(y0 - last_y0) < font_size * 0.5:
                        # Même ligne visuelle, on n'ajoute pas de \n
                        pass
                    else:
                        full_text += "\n"
                        last_x1 = None # reset x for new line
                
                last_y0 = y0
                
                for span in line.get("spans", []):
                    span_bbox = span.get("bbox", [0,0,0,0])
                    x0 = span_bbox[0]
                    
                    # Ajouter des espaces proportionnels à l'écart horizontal (tabulations)
                    if last_x1 is not None and (x0 - last_x1) > font_size * 0.2:
                        spaces_count = max(1, int((x0 - last_x1) / (font_size * 0.25)))
                        full_text += " " * spaces_count
                        
                    if not got_first_span:
                        font_name = span.get("font", "Helvetica")
                        font_size = max(1.0, span.get("size", 12.0))
                        color_int = span.get("color", 0)
                        r = (color_int >> 16) & 0xFF
                        g = (color_int >> 8) & 0xFF
                        b = color_int & 0xFF
                        font_color = (r, g, b)
                        flags = span.get("flags", 0)
                        is_bold = bool(flags & 16)
                        is_italic = bool(flags & 2)
                        fname_lower = font_name.lower()
                        if "bold" in fname_lower: is_bold = True
                        if "italic" in fname_lower or "oblique" in fname_lower: is_italic = True
                        got_first_span = True
                        
                    full_text += span.get("text", "")
                    last_x1 = span_bbox[2]

            full_text = full_text.strip()
            if full_text:
                text_blocks.append({
                    'rect': bbox,
                    'text': full_text,
                    'raw_block': block,  # Pour extraire le style span par span plus tard
                })
        return text_blocks

    def get_image_blocks(self, page_number):
        """
        Extrait les images existantes de la page avec leurs coordonnées.
        """
        if not self.doc or page_number < 0 or page_number >= len(self.doc):
            return []
        page = self.doc[page_number]
        image_blocks = []
        try:
            # TEXT_PRESERVE_IMAGES (flag=4) est requis pour inclure les blocs images
            raw = page.get_text("dict", flags=fitz.TEXT_PRESERVE_IMAGES)
            for block in raw["blocks"]:
                if block.get("type") == 1:  # type 1 = image
                    bbox = block["bbox"]
                    image_blocks.append({
                        'rect': (bbox[0], bbox[1], bbox[2], bbox[3]),
                        'xref': block.get("number", 0)
                    })
        except Exception:
            pass
        return image_blocks

    def get_page_image(self, page_number, zoom=1.0, redactions=None):
        """
        Rend une page du PDF en QImage pour l'affichage dans l'interface PyQt6.
        redactions: liste de tuples (x0, y0, x1, y1) à masquer sur l'image générée.
        """
        if not self.doc or page_number < 0 or page_number >= len(self.doc):
            return None

        # On travaille sur une copie temporaire de la page pour ne pas affecter le vrai document
        # si on applique des redactions juste pour l'affichage
        page = self.doc[page_number]
        
        # Pour ne pas modifier le document original en cours de visualisation, on utilise des annotations
        # ou un draw_rect temporaire sur le pixmap.
        
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        
        # Masquer visuellement les zones rédigées sur le pixmap généré
        if redactions:
            for r in redactions:
                rect = fitz.Rect(r)
                rect *= zoom # Ajuster avec le zoom
                pix.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1)) # Remplir en blanc
        
        # Convertir Pixmap en QImage
        fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        return img.copy()  # Important : retourner une copie pour éviter les crashs de mémoire

    def save_pdf(self, save_path, page_modifications=None):
        """
        Sauvegarde le PDF actuel.
        page_modifications: dictionnaire {page_number: [{'type': 'text'|'image'|'redact', ...}]}
        """
        if not self.doc:
            return False

        if page_modifications:
            self._apply_modifications(page_modifications)

        self.doc.save(save_path, garbage=4, deflate=True)
        self.current_file_path = save_path
        return True

    def _apply_modifications(self, modifications):
        """
        Applique les modifications dans le document PDF.
        """
        for page_num, mods in modifications.items():
            page = self.doc[page_num]
            
            # Appliquer les rédactions (suppressions de texte) d'abord
            for mod in mods:
                if mod['type'] == 'redact':
                    rect = fitz.Rect(mod['rect'])
                    # Ajouter l'annotation de suppression
                    page.add_redact_annot(rect, fill=(1, 1, 1)) # Fond blanc
            
            # Appliquer toutes les rédactions sur la page
            page.apply_redactions()

            # Ensuite, ajouter les nouveaux éléments
            for mod in mods:
                if mod['type'] == 'text':
                    point = fitz.Point(mod['x'], mod['y'])
                    color = mod.get('color', (0, 0, 0)) # Default black
                    color = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
                    
                    family = mod.get('family', 'helv').lower()
                    bold = mod.get('bold', False)
                    italic = mod.get('italic', False)
                    
                    fontname = "helv"
                    if "times" in family:
                        if bold and italic: fontname = "tibi"
                        elif bold: fontname = "tibo"
                        elif italic: fontname = "tiit"
                        else: fontname = "tiro"
                    elif "courier" in family:
                        if bold and italic: fontname = "cobi"
                        elif bold: fontname = "cobo"
                        elif italic: fontname = "coit"
                        else: fontname = "cour"
                    else:
                        if bold and italic: fontname = "hebi"
                        elif bold: fontname = "hebo"
                        elif italic: fontname = "heit"
                        else: fontname = "helv"
                        
                    page.insert_text(point, mod['text'], fontsize=mod.get('size', 12), color=color, fontname=fontname)
                elif mod['type'] == 'image':
                    rect = fitz.Rect(mod['x'], mod['y'], mod['x'] + mod['width'], mod['y'] + mod['height'])
                    page.insert_image(rect, filename=mod['path'])

    @staticmethod
    def merge_pdfs(input_paths, output_path):
        """Fusionne plusieurs fichiers PDF en un seul."""
        merger = PdfWriter()
        for path in input_paths:
            merger.append(path)
        with open(output_path, "wb") as f_out:
            merger.write(f_out)
            
    @staticmethod
    def split_pdf(input_path, output_dir):
        """Divise un fichier PDF en plusieurs fichiers (un par page)."""
        reader = PdfReader(input_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            out_file = os.path.join(output_dir, f"{base_name}_page_{i+1}.pdf")
            with open(out_file, "wb") as f_out:
                writer.write(f_out)
