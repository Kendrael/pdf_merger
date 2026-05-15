from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os
import sys

def generar_caratula(ruta_salida, nombre_paciente, fecha, tipo_estudio,
                     nombre_centro="SIRIX"):
    """
    Genera la carátula usando la imagen de fondo del centro correspondiente.
    """
    # Resolver BASE_DIR igual que antes
    if getattr(sys, 'frozen', False):
        executable = sys.executable
        contenido_macos = os.path.dirname(executable)
        contenido = os.path.dirname(contenido_macos)
        resources = os.path.join(contenido, 'Resources')
        frameworks = os.path.join(contenido, 'Frameworks')
        app = os.path.dirname(contenido)
        junto_a_app = os.path.dirname(app)

        BASE_DIR = contenido_macos
        for directorio in [resources, frameworks, contenido_macos, junto_a_app]:
            if os.path.exists(os.path.join(directorio, 'config.json')):
                BASE_DIR = directorio
                break
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Mapear centro a imagen de carátula
    imagenes_caratula = {
        "SIRIX":         "Caratula_Sirix.jpeg",
        "CERADI":        "Caratula_Ceradi.jpeg",
        "CERADI - CIES": "Caratula_Cies.jpeg",
        "SIRIX - KOLPING": "Caratula_Kolping.jpeg",
    }
    nombre_imagen = imagenes_caratula.get(nombre_centro, "Caratula_Sirix.jpeg")
    ruta_imagen = os.path.join(BASE_DIR, nombre_imagen)

    # Tamaño de página: ancho carta, alto proporcional a la imagen
    ancho_pt = 612.0
    alto_pt = 311.7

    c = canvas.Canvas(ruta_salida, pagesize=(ancho_pt, alto_pt))

    # --- Fondo: imagen del centro ---
    if os.path.exists(ruta_imagen):
        fondo = ImageReader(ruta_imagen)
        c.drawImage(fondo, 0, 0, width=ancho_pt, height=alto_pt,
                   preserveAspectRatio=False)

    # --- Coordenadas de texto (en puntos PDF) ---
    x_texto = 21.0
    ancho_texto = 302.0 - x_texto   # ancho disponible ~281 pt

    y_paciente = 205.0
    y_estudio  = 175.6
    y_fecha    = 141.0

    # Color del texto: azul oscuro de SIRIX, legible sobre fondo blanco
    c.setFillColor(colors.HexColor("#1A1A1A"))

    # --- PACIENTE ---
    nombre_font = 11
    c.setFont("Helvetica-Bold", nombre_font)
    while c.stringWidth(nombre_paciente, "Helvetica-Bold", nombre_font) > ancho_texto and nombre_font > 7:
        nombre_font -= 1
        c.setFont("Helvetica-Bold", nombre_font)
    c.drawString(x_texto, y_paciente, nombre_paciente)

    # --- ESTUDIO ---
    estudio_font = 9
    from reportlab.lib.utils import simpleSplit
    lineas = simpleSplit(tipo_estudio, "Helvetica-Bold", estudio_font, ancho_texto)
    while len(lineas) > 3 and estudio_font > 6:
        estudio_font -= 1
        lineas = simpleSplit(tipo_estudio, "Helvetica-Bold", estudio_font, ancho_texto)
    c.setFont("Helvetica-Bold", estudio_font)
    y_linea = y_estudio
    for linea in lineas[:3]:
        c.drawString(x_texto, y_linea, linea)
        y_linea -= estudio_font + 2

    # --- FECHA --- posición dinámica según líneas del estudio
    y_fecha_dinamica = y_linea - 6
    partes = fecha.split(" ")
    fecha_display = f"{partes[0]} de {partes[1]} de {partes[2]}"
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_texto, y_fecha_dinamica, fecha_display)

    c.save()


# Bloque de prueba
if __name__ == "__main__":
    generar_caratula(
        ruta_salida="caratula_prueba.pdf",
        nombre_paciente="UGARTE VIDAURRE OSCAR",
        fecha="04_Mayo_2026",
        tipo_estudio="CT - ABDOMEN Y PELVIS SIMPLE CON PROTOCOLO DE UROLITIASIS",
        nombre_centro="SIRIX"
    )
    print("Carátula generada: caratula_prueba.pdf")