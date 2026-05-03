# PDF Merger - Radiology Report Generator

Desktop tool to merge and present medical imaging study reports (CT, ultrasound, X-ray, and others) into a single PDF file ready to send.

Developed for **SIRIX - Diagnóstico e Intervencionismo** and associated centers (CERADI, CERADI-CIES, SIRIX-KOLPING), La Paz, Bolivia.

---

## Features

- Drag & drop or manual file selection
- Automatic file classification (report, mosaics, VR) by content and color analysis
- Automatic cover page generation with institutional logo and study data
- Automatic extraction of patient name, date, and study type from the report
- Auto-generated output filename (LastName_FirstName_Month_Year.pdf)
- Institutional watermark on the report page
- Support for multiple mosaic files
- Active center selector (SIRIX / CERADI / CERADI-CIES / SIRIX-KOLPING)
- Per-center color theming

---

## Requirements

- Python 3.13+
- Dependencies:

pip install pypdf pdfplumber reportlab pillow tkinterdnd2 pypdfium2 numpy

---

## Usage

python interfaz.py

1. Drag PDF files onto the window, or use the selection buttons
2. Verify that files were classified correctly
3. Press **GENERAR REPORTE**
4. The final PDF is saved in the same folder as the report

---

## Project Structure

pdf_merger/
├── interfaz.py          # Main graphical interface
├── extractor.py         # Data extraction from report
├── caratula.py          # Cover page PDF generation
├── merger.py            # PDF file merging
├── marca_agua.py        # Watermark application
├── config_manager.py    # Center configuration management
├── config.json          # Center and logo configuration
├── logo_sirix.jpg       # SIRIX logo
└── logo_ceradi.jpg      # CERADI logo

---

## Notes

- Developed with AI assistance (Claude, Anthropic)
- Compatible with reports generated in Pages (macOS) exported to PDF
- Version 1.0.2

---

## Author

Kenny Mejia — Bioimagenólogo & Health Data Specialist, La Paz, Bolivia

---
---

# PDF Merger - Generador de Reportes Imagenológicos

Herramienta de escritorio para unir y presentar reportes de estudios imagenológicos (tomografía, ecografía, rayos X y otros) en un solo archivo PDF listo para enviar.

Desarrollada para **SIRIX - Diagnóstico e Intervencionismo** y centros asociados (CERADI, CERADI-CIES, SIRIX-KOLPING), La Paz, Bolivia.

---

## Funcionalidades

- Drag & drop o selección manual de archivos PDF
- Clasificación automática de archivos (informe, mosaicos, VR) por contenido y análisis de color
- Generación automática de carátula con logo y datos del estudio
- Extracción automática de nombre del paciente, fecha y tipo de estudio desde el informe
- Nombre de archivo de salida autogenerado (Apellido_Nombre_Mes_Año.pdf)
- Marca de agua institucional en el informe
- Soporte para múltiples mosaicos
- Selector de centro activo (SIRIX / CERADI / CERADI-CIES / SIRIX-KOLPING)
- Temas de color por centro

---

## Requisitos

- Python 3.13+
- Dependencias:

pip install pypdf pdfplumber reportlab pillow tkinterdnd2 pypdfium2 numpy

---

## Uso

python interfaz.py

1. Arrastra los archivos PDF del estudio a la ventana, o usa los botones de selección
2. Verifica que los archivos fueron clasificados correctamente
3. Presiona **GENERAR REPORTE**
4. El PDF final se guarda en la misma carpeta del informe

---

## Notas

- Desarrollado con asistencia de IA (Claude, Anthropic)
- Compatible con informes generados en Pages (macOS) exportados a PDF
- Versión 1.0.2

---

## Autor

Kenny Mejia — Bioimagenólogo & Health Data Specialist, La Paz, Bolivia