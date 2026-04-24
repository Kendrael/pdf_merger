from pypdf import PdfWriter, PdfReader
import os

def unir_pdfs(ruta_caratula, ruta_informe, ruta_mosaico, ruta_vr, ruta_salida):
    """
    Une la carátula, el informe, los mosaicos y los VRs en un solo PDF.
    Los recibe en orden y los guarda en ruta_salida.
    """
    writer = PdfWriter()

    archivos = [ruta_caratula, ruta_informe, ruta_mosaico, ruta_vr]

    for ruta in archivos:
        if ruta and os.path.exists(ruta):
            reader = PdfReader(ruta)
            for pagina in reader.pages:
                writer.add_page(pagina)
        else:
            print(f"Advertencia: no se encontró el archivo {ruta}, se omite.")

    with open(ruta_salida, "wb") as archivo_final:
        writer.write(archivo_final)

    print(f"PDF final generado: {ruta_salida}")

# Bloque de prueba
if __name__ == "__main__":
    unir_pdfs(
        ruta_caratula="caratula_prueba.pdf",
        ruta_informe=input("Arrastra el informe PDF aquí y presiona Enter: ").strip().strip('"').strip("'").lstrip("& '"),
        ruta_mosaico=None,
        ruta_vr=None,
        ruta_salida="prueba_final.pdf"
    )