import pdfplumber
import re
from datetime import datetime

def extraer_datos(ruta_pdf):
    """
    Abre el informe PDF y extrae el nombre del paciente y la fecha del estudio.
    Soporta formato estándar (Pages) y formato simplificado (celular).
    Retorna un diccionario con 'nombre', 'fecha' y 'estudio'.
    """
    with pdfplumber.open(ruta_pdf) as pdf:
        texto = pdf.pages[0].extract_text()

    # Buscar nombre completo al final del documento (formato estándar)
    nombre_completo_match = re.search(r'^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)\s*-\s*(?:CT|ECO|RX|\d{1,2}/)', texto, re.MULTILINE)
    if nombre_completo_match:
        nombre = nombre_completo_match.group(1).strip()
    else:
        # Fallback: buscar después de "Nombre:" o "NOMBRE:"
        nombre_match = re.search(r'(?i)nombre:\s*(.+?)(?:\n|$)', texto)
        if nombre_match:
            nombre = ' '.join(nombre_match.group(1).strip().split())
        else:
            nombre = "DESCONOCIDO"

    # Buscar fecha - soporta separadores / o . y año de 2 o 4 dígitos
    fecha_match = re.search(r'(?i)fecha:\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})', texto)
    fecha_raw = fecha_match.group(1).strip() if fecha_match else None

    if fecha_raw:
        fecha_normalizada = fecha_raw.replace(".", "/")
        partes = fecha_normalizada.split("/")
        dia = partes[0].zfill(2)
        mes_num = int(partes[1])
        anio = partes[2] if len(partes[2]) == 4 else f"20{partes[2]}"
        meses = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        fecha_formateada = f"{dia}_de_{meses[mes_num]}_de_{anio}"
    else:
        fecha_formateada = "Fecha_desconocida"

    # Buscar tipo de estudio
    estudio_match = re.search(r'(?i)estudio:\s*(.+?)(?:\n\n|\nDatos|\nHallazgos)', texto, re.DOTALL)
    if estudio_match:
        estudio = " ".join(estudio_match.group(1).strip().split())
    else:
        estudio = "Estudio Tomográfico"

    return {
        "nombre": nombre,
        "fecha": fecha_formateada,
        "estudio": estudio
    }

# Bloque de prueba - solo corre cuando ejecutamos este archivo directamente
if __name__ == "__main__":
    ruta = input("Arrastra el informe PDF aquí y presiona Enter: ").strip().strip('"').strip("'").lstrip("& '")
    datos = extraer_datos(ruta)
    print(f"Nombre extraído: {datos['nombre']}")
    print(f"Fecha extraída:  {datos['fecha']}")
    print(f"Nombre de archivo sugerido: {datos['nombre'].replace(' ', '_')}_{datos['fecha']}.pdf")