import pdfplumber
import re
from datetime import datetime

FLAGS = re.IGNORECASE | re.MULTILINE

# Etiquetas aceptadas (agrega aquí nuevos alias cuando aparezcan)
ETIQ_NOMBRE = r"(?:nombre(?:\s+del\s+paciente)?|paciente|pcte\.?)"
ETIQ_FECHA = r"(?:fecha(?:\s+de(?:l)?\s+estudio)?)"

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12
}
MESES_NOMBRE = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}


def es_informe(texto):
    """
    True si el texto parece un informe médico.
    1) Etiqueta de nombre/paciente + etiqueta de fecha al inicio de línea.
    2) Failsafe: mucho texto con palabras típicas de un informe.
    """
    tiene_nombre = re.search(rf"^\s*{ETIQ_NOMBRE}\s*:?\s*\S", texto, FLAGS)
    tiene_fecha = re.search(rf"\b{ETIQ_FECHA}\s*:?\s*\d", texto, FLAGS)
    if tiene_nombre and tiene_fecha:
        return True
    if len(texto.strip()) > 500 and re.search(
            r"conclusi[oó]n|descripci[oó]n|hallazgos", texto, re.IGNORECASE):
        return True
    return False


def _extraer_nombre(texto):
    # Intento 1: etiqueta con dos puntos, en cualquier parte de la página
    m = re.search(rf"^\s*{ETIQ_NOMBRE}\s*:\s*(.+)$", texto, FLAGS)
    # Intento 2: sin dos puntos, solo en las primeras líneas (ej: tabla)
    if not m:
        cabecera = "\n".join(texto.splitlines()[:12])
        m = re.search(rf"^\s*{ETIQ_NOMBRE}\s+(.+)$", cabecera, FLAGS)
    if not m:
        return "DESCONOCIDO"
    nombre = re.split(r"\s{2,}|\t|m[eé]dico", m.group(1), flags=re.IGNORECASE)[0].strip()
    return nombre if nombre else "DESCONOCIDO"


def _extraer_fecha(texto):
    m = re.search(rf"\b{ETIQ_FECHA}\s*:?\s*(\d.*)$", texto, FLAGS)
    if not m:
        return "Fecha_desconocida"
    linea = m.group(1)

    try:
        # Formato numérico: 12/04/26, 12.04.2026, 12-04-26
        num = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", linea)
        if num:
            dia = int(num.group(1))
            mes = int(num.group(2))
            anio = int(num.group(3))
            if anio < 100:
                anio += 2000
            if 1 <= mes <= 12:
                return f"{dia:02d}_{MESES_NOMBRE[mes]}_{anio}"

        # Formato texto: 9 de octubre de 2026
        txt = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+(?:de|del)\s+(\d{4})",
                        linea, re.IGNORECASE)
        if txt:
            dia = int(txt.group(1))
            mes = MESES.get(txt.group(2).lower())
            if mes:
                return f"{dia:02d}_{MESES_NOMBRE[mes]}_{txt.group(3)}"
    except ValueError:
        pass

    return "Fecha_desconocida"


def _extraer_estudio(texto):
    # Intento 1: línea "Estudio: ..." al inicio de línea (formato anterior)
    m = re.search(r'^\s*estudio\s*:\s*(.+?)(?:\n\n|\nDatos|\nHallazgos)',
                  texto, FLAGS | re.DOTALL)
    if m:
        return " ".join(m.group(1).strip().split())

    # Intento 2: título sin etiqueta (TOMOGRAFIA DE ..., RESONANCIA ...)
    m = re.search(
        r"^\s*((?:tomograf|resonanc|ecograf|radiograf|mamograf|densitometr|angio)\w*.*)$",
        texto, FLAGS)
    if m:
        return " ".join(m.group(1).strip().split())

    return "Estudio Tomográfico"


def extraer_datos(ruta_pdf):
    """
    Abre el informe PDF y extrae nombre, fecha y estudio.
    Retorna un diccionario con 'nombre', 'fecha' y 'estudio'.
    """
    with pdfplumber.open(ruta_pdf) as pdf:
        texto = pdf.pages[0].extract_text() or ""

    return {
        "nombre": _extraer_nombre(texto),
        "fecha": _extraer_fecha(texto),
        "estudio": _extraer_estudio(texto)
    }


# Bloque de prueba
if __name__ == "__main__":
    ruta = input("Arrastra el informe PDF aquí y presiona Enter: ").strip().strip('"').strip("'").lstrip("& '")
    datos = extraer_datos(ruta)
    print(f"Nombre extraído: {datos['nombre']}")
    print(f"Fecha extraída:  {datos['fecha']}")
    print(f"Estudio:         {datos['estudio']}")
    print(f"Nombre de archivo sugerido: {datos['nombre'].replace(' ', '_')}_{datos['fecha']}.pdf")