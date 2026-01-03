import fitz  # PyMuPDF

def get_page_count(pdf_path: str) -> int:
    """Devuelve el número total de páginas del PDF."""
    with fitz.open(pdf_path) as doc:
        return doc.page_count


def extract_page_image(pdf_path: str, page_number: int) -> bytes:
    """Retorna la página como bytes PNG a 300 dpi."""
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        return pix.tobytes("png")
    