from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfWriter, PdfReader
from PIL import Image
import os
import io

def remover_fondo_blanco(ruta_imagen, umbral=240):
    """
    Convierte el fondo blanco de una imagen en transparente.
    umbral: píxeles más claros que este valor se vuelven transparentes.
    """
    img = Image.open(ruta_imagen).convert("RGBA")
    import numpy as np
    arr = np.array(img)
    r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
    mascara_blanco = (r >= umbral) & (g >= umbral) & (b >= umbral)
    arr[:,:,3] = np.where(mascara_blanco, 0, a)
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def agregar_marca_agua(ruta_pdf_entrada, ruta_pdf_salida, ruta_logo, opacidad=0.06):
    """
    Agrega el logo como marca de agua centrada en cada página del PDF.
    opacidad: valor entre 0 y 1 (0.06 = muy sutil)
    """
    reader = PdfReader(ruta_pdf_entrada)
    writer = PdfWriter()

    for pagina in reader.pages:
        ancho = float(pagina.mediabox.width)
        alto = float(pagina.mediabox.height)

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(ancho, alto))
        c.setFillAlpha(opacidad)

        if ruta_logo and os.path.exists(ruta_logo):
            # Remover fondo blanco antes de aplicar
            logo_sin_fondo = remover_fondo_blanco(ruta_logo)
            logo = ImageReader(logo_sin_fondo)
            tam = min(ancho, alto) * 0.6
            x = (ancho - tam) / 2
            y = (alto - tam) / 2
            c.drawImage(logo, x, y, width=tam, height=tam,
                       preserveAspectRatio=True, mask='auto')

        c.save()
        buffer.seek(0)

        pagina_marca = PdfReader(buffer).pages[0]
        pagina.merge_page(pagina_marca)
        writer.add_page(pagina)

    with open(ruta_pdf_salida, "wb") as f:
        writer.write(f)

# Bloque de prueba
if __name__ == "__main__":
    agregar_marca_agua(
        ruta_pdf_entrada=input("Arrastra un mosaico aquí: ").strip().strip('"').strip("'").lstrip("& '"),
        ruta_pdf_salida="prueba_marca_agua.pdf",
        ruta_logo="logo_sirix.jpg"
    )
    print("Marca de agua aplicada: prueba_marca_agua.pdf")