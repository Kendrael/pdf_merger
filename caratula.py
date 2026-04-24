from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

def generar_caratula(ruta_salida, nombre_paciente, fecha, tipo_estudio, ruta_logo=None):
    """
    Genera una página de carátula en PDF con los datos del estudio.
    """
    c = canvas.Canvas(ruta_salida, pagesize=letter)
    ancho, alto = letter

    # --- Franja superior azul ---
    c.setFillColor(colors.HexColor("#1A3C6E"))
    c.rect(0, alto - 4*cm, ancho, 4*cm, fill=True, stroke=False)

    # --- Logo (si existe) ---
    if ruta_logo and os.path.exists(ruta_logo):
        logo = ImageReader(ruta_logo)
        c.drawImage(logo, 1.5*cm, alto - 3.5*cm, width=5*cm, height=3*cm,
                   preserveAspectRatio=True, mask='auto')

    # --- Nombre del centro en la franja ---
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(ancho/2, alto - 2*cm, "SIRIX")
    c.setFont("Helvetica", 11)
    c.drawCentredString(ancho/2, alto - 2.8*cm, "Diagnóstico e Intervencionismo")

    # --- Título del documento ---
    c.setFillColor(colors.HexColor("#1A3C6E"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(ancho/2, alto - 7*cm, "REPORTE DE TOMOGRAFÍA")

    # --- Línea divisoria ---
    c.setStrokeColor(colors.HexColor("#1A3C6E"))
    c.setLineWidth(2)
    c.line(2*cm, alto - 7.8*cm, ancho - 2*cm, alto - 7.8*cm)

    # --- Datos del paciente ---
    c.setFillColor(colors.HexColor("#1A3C6E"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, alto - 10*cm, "DATOS DEL ESTUDIO")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, alto - 11.5*cm, "Paciente:")
    c.setFont("Helvetica", 11)
    c.drawString(6*cm, alto - 11.5*cm, nombre_paciente)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, alto - 12.5*cm, "Fecha:")
    c.setFont("Helvetica", 11)
    c.drawString(6*cm, alto - 12.5*cm, fecha)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, alto - 13.5*cm, "Estudio:")
    c.setFont("Helvetica", 11)
    c.drawString(6*cm, alto - 13.5*cm, tipo_estudio)

    # --- Línea divisoria inferior ---
    c.setStrokeColor(colors.HexColor("#1A3C6E"))
    c.setLineWidth(1)
    c.line(2*cm, alto - 14.5*cm, ancho - 2*cm, alto - 14.5*cm)

    # --- Pie de página ---
    c.setFillColor(colors.HexColor("#1A3C6E"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(ancho/2, 2*cm, "El presente estudio se almacenará en nuestro sistema PACS por 4 años")

    c.save()

# Bloque de prueba
if __name__ == "__main__":
    generar_caratula(
        ruta_salida="caratula_prueba.pdf",
        nombre_paciente="UGARTE VIDAURRE OSCAR",
        fecha="Abril 2026",
        tipo_estudio="CT - ABDOMEN Y PELVIS SIMPLE CON PROTOCOLO DE UROLITIASIS",
        ruta_logo="logo_sirix.jpg"
    )
    print("Carátula generada: caratula_prueba.pdf")