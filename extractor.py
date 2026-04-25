import pdfplumber
import re
from datetime import datetime

def extraer_datos(ruta_pdf):
    """
    Abre el informe PDF y extrae el nombre del paciente y la fecha del estudio.
    Retorna un diccionario con 'nombre' y 'fecha'.
    """
    with pdfplumber.open(ruta_pdf) as pdf:
        texto = pdf.pages[0].extract_text()

    # Buscar nombre del paciente
    nombre_match = re.search(r'Nombre:\s*(.+?)(?:\s{2,}|\t|Médico|$)', texto)
    nombre = nombre_match.group(1).strip() if nombre_match else "DESCONOCIDO"

    # Buscar fecha del estudio (acepta / o . como separador)
    fecha_match = re.search(r'FECHA:\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})', texto)
    fecha_raw = fecha_match.group(1).strip() if fecha_match else None

    # Convertir fecha a formato "Abril_2026"
    if fecha_raw:
        fecha_normalizada = fecha_raw.replace(".", "/")
        fecha_obj = datetime.strptime(fecha_normalizada, "%d/%m/%y")
        meses = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        fecha_formateada = f"{meses[fecha_obj.month]}_{fecha_obj.year}"
    else:
        fecha_formateada = "Fecha_desconocida"

    return {
        "nombre": nombre,
        "fecha": fecha_formateada
    }

# Bloque de prueba - solo corre cuando ejecutamos este archivo directamente
if __name__ == "__main__":
    ruta = input("Arrastra el informe PDF aquí y presiona Enter: ").strip().strip('"').strip("'").lstrip("& '")
    datos = extraer_datos(ruta)
    print(f"Nombre extraído: {datos['nombre']}")
    print(f"Fecha extraída:  {datos['fecha']}")
    print(f"Nombre de archivo sugerido: {datos['nombre'].replace(' ', '_')}_{datos['fecha']}.pdf")