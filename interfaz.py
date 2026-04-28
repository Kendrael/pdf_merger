import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import re
import pdfplumber
from extractor import extraer_datos
from caratula import generar_caratula
from merger import unir_pdfs
from config_manager import obtener_centro_activo, cambiar_centro, listar_centros

def clasificar_pdf(ruta):
    """
    Analiza el PDF y determina si es informe, mosaico o VR.
    - Informe: contiene 'Nombre:' y 'FECHA:'
    - VR: tiene píxeles a color (R, G, B distintos)
    - Mosaico: escala de grises
    """
    try:
        with pdfplumber.open(ruta) as pdf:
            texto = pdf.pages[0].extract_text() or ""

        # Primero verificar si es informe
        if re.search(r'Nombre:', texto) and re.search(r'FECHA:', texto):
            return "informe"

        # Usar pypdf para extraer imágenes y analizar color
        from pypdf import PdfReader
        from PIL import Image
        import numpy as np
        import io

        reader = PdfReader(ruta)
        page = reader.pages[0]

        # Intentar extraer imágenes de la página
        imagenes = []
        if hasattr(page, 'images'):
            imagenes = page.images

        if imagenes:
            # Analizar la primera imagen
            img_data = imagenes[0].data
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            arr = np.array(img)
            datos = arr.reshape(-1, 3)

            # Contar píxeles con color significativo
            umbral = 10
            pixeles_color = sum(
                1 for r, g, b in datos
                if max(int(r), int(g), int(b)) - min(int(r), int(g), int(b)) > umbral
            )
            porcentaje_color = pixeles_color / len(datos)

            if porcentaje_color > 0.005:
                return "vr"
            else:
                return "mosaico"
        else:
            # Sin imágenes extraíbles, clasificar por número de páginas
            with pdfplumber.open(ruta) as pdf:
                num_paginas = len(pdf.pages)
            return "mosaico" if num_paginas > 1 else "vr"

    except Exception as e:
        print(f"Error clasificando {ruta}: {e}")
        return "desconocido"


class AplicacionPDF(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generador de Reportes")
        self.geometry("650x600")
        self.resizable(True, True)
        self.configure(bg="#1A3C6E")

        # Almacenamiento de archivos clasificados
        self.informe = None
        self.mosaicos = []
        self.vr = None
        self.centro = obtener_centro_activo()

        self.var_centro = tk.StringVar(value=self.centro["nombre"])

        self._construir_interfaz()

    def _construir_interfaz(self):
        self.label_nombre_centro = tk.Label(self, text=self.centro["nombre"],
                font=("Helvetica", 22, "bold"), bg="#1A3C6E", fg="white")
        self.label_nombre_centro.pack(pady=(20, 0))

        self.label_subtitulo_centro = tk.Label(self, text=self.centro["subtitulo"],
                font=("Helvetica", 11), bg="#1A3C6E", fg="white")
        self.label_subtitulo_centro.pack()

        tk.Label(self, text="Generador de Reportes",
                font=("Helvetica", 10), bg="#1A3C6E", fg="#A8C4E0").pack(pady=(0, 5))

        # --- Botón configuración esquina superior derecha ---
        btn_config = tk.Menubutton(self, text="⚙ Centro", bg="#1A3C6E", fg="#A8C4E0",
                                  font=("Helvetica", 8), relief="flat",
                                  activebackground="#1A3C6E", activeforeground="white")
        btn_config.place(relx=0.0, rely=0.0, anchor="nw", x=10, y=10)

        menu_centros = tk.Menu(btn_config, tearoff=0)
        for nombre in listar_centros():
            menu_centros.add_radiobutton(label=nombre,
                                        variable=self.var_centro,
                                        value=nombre,
                                        command=self._cambiar_centro)
        btn_config.config(menu=menu_centros)

        # --- Botón About ---
        btn_about = tk.Button(self, text="?", bg="#1A3C6E", fg="#A8C4E0",
                             font=("Helvetica", 8), relief="flat",
                             activebackground="#1A3C6E", activeforeground="white",
                             command=self._mostrar_about)
        btn_about.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

        # --- Zona de drag & drop ---
        self.zona_drop = tk.Label(
            self,
            text="Arrastra aquí los archivos PDF\n(informe, mosaicos y VR)",
            font=("Helvetica", 12),
            bg="white", fg="#1A3C6E",
            relief="solid", bd=2,
            width=50, height=4
        )
        self.zona_drop.pack(padx=20, pady=(10, 0))
        self.zona_drop.drop_target_register(DND_FILES)
        self.zona_drop.dnd_bind('<<Drop>>', self._on_drop)

        # --- Botones de selección manual ---
        panel_botones = tk.Frame(self, bg="#1A3C6E")
        panel_botones.pack(padx=20, pady=8, fill="x")

        tk.Button(panel_botones, text="+ Informe", bg="white", fg="#1A3C6E",
                 font=("Helvetica", 9, "bold"),
                 command=self._seleccionar_informe).pack(side="left", padx=5)
        tk.Button(panel_botones, text="+ Mosaico(s)", bg="white", fg="#1A3C6E",
                 font=("Helvetica", 9, "bold"),
                 command=self._seleccionar_mosaicos).pack(side="left", padx=5)
        tk.Button(panel_botones, text="+ VR", bg="white", fg="#1A3C6E",
                 font=("Helvetica", 9, "bold"),
                 command=self._seleccionar_vr).pack(side="left", padx=5)
        tk.Button(panel_botones, text="Limpiar", bg="#A8C4E0", fg="#1A3C6E",
                 font=("Helvetica", 9),
                 command=self._limpiar).pack(side="right", padx=5)

        # --- Panel de archivos detectados ---
        panel = tk.Frame(self, bg="white", padx=20, pady=15)
        panel.pack(padx=20, fill="both", expand=True)

        tk.Label(panel, text="Archivos detectados:",
                font=("Helvetica", 10, "bold"), bg="white",
                fg="#1A3C6E").pack(anchor="w")

        self.texto_archivos = tk.Text(panel, height=8, width=70,
                                      state="disabled", bg="#F5F8FC",
                                      font=("Helvetica", 9), relief="flat")
        self.texto_archivos.pack(pady=5)

        # --- Botón generar ---
        tk.Button(self, text="GENERAR REPORTE",
                 font=("Helvetica", 12, "bold"),
                 bg="white", fg="#1A3C6E",
                 padx=20, pady=10,
                 command=self._generar).pack(pady=10)

        # --- Estado ---
        self.label_estado = tk.Label(self, text="",
                                    font=("Helvetica", 10),
                                    bg="#1A3C6E", fg="white",
                                    wraplength=580)
        self.label_estado.pack(pady=5)

    def _seleccionar_informe(self):
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if ruta:
            self.informe = ruta
            self._actualizar_panel()

    def _seleccionar_mosaicos(self):
        from tkinter import filedialog
        rutas = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if rutas:
            self.mosaicos.extend(rutas)
            self._actualizar_panel()

    def _seleccionar_vr(self):
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if ruta:
            self.vr = ruta
            self._actualizar_panel()

    def _limpiar(self):
        self.informe = None
        self.mosaicos = []
        self.vr = None
        self._actualizar_panel()
        self.label_estado.config(text="")
        
    def _on_drop(self, event):
        """Recibe los archivos arrastrados, los clasifica y muestra el resultado."""
        # Parsear rutas (pueden venir con llaves si tienen espacios)
        rutas_raw = self.tk.splitlist(event.data)

        self.informe = None
        self.mosaicos = []
        self.vr = None

        self.label_estado.config(text="Clasificando archivos...")
        self.update()

        for ruta in rutas_raw:
            ruta = ruta.strip()
            if not ruta.lower().endswith(".pdf"):
                continue
            tipo = clasificar_pdf(ruta)
            if tipo == "informe":
                self.informe = ruta
            elif tipo == "mosaico":
                self.mosaicos.append(ruta)
            elif tipo == "vr":
                self.vr = ruta

        self._actualizar_panel()
        self.label_estado.config(text="")

    def _actualizar_panel(self):
        """Muestra en el panel los archivos clasificados."""
        self.texto_archivos.config(state="normal")
        self.texto_archivos.delete("1.0", tk.END)

        if self.informe:
            self.texto_archivos.insert("1.0",
                f"INFORME:  {os.path.basename(self.informe)}\n\n")
        else:
            self.texto_archivos.insert("1.0", "Informe:  no detectado\n\n")

        if self.mosaicos:
            for i, m in enumerate(self.mosaicos, 1):
                self.texto_archivos.insert(tk.END,
                    f"MOSAICO {i}: {os.path.basename(m)}\n")
            self.texto_archivos.insert(tk.END, "\n")
        else:
            self.texto_archivos.insert(tk.END, "Mosaico: no detectado\n\n")

        if self.vr:
            self.texto_archivos.insert(tk.END,
                f"VR:       {os.path.basename(self.vr)}\n")
        else:
            self.texto_archivos.insert(tk.END, "VR:      no detectado\n")

        self.texto_archivos.config(state="disabled")
        self.update_idletasks()

    def _cambiar_centro(self):
        nombre = self.var_centro.get()
        cambiar_centro(nombre)
        self.centro = obtener_centro_activo()
        self.label_nombre_centro.config(text=self.centro["nombre"])
        self.label_subtitulo_centro.config(text=self.centro["subtitulo"])
        self.label_estado.config(text=f"✅ Centro activo: {self.centro['nombre']}")
    
    def _mostrar_about(self):
        from tkinter import messagebox
        messagebox.showinfo(
            "Acerca de",
            "Generador de Reportes Imagenológicos\n"
            "Versión 1.0.0\n\n"
            "Desarrollado por Kenny Mejia\n"
            "Bioimagenólogo & Health Data Specialist\n"
            "La Paz, Bolivia\n\n"
            "github.com/Kendrael/pdf_merger"
        )

    def _generar(self):
        # Forzar directorio de trabajo a home del usuario
        os.chdir(os.path.expanduser("~"))
        
        if not self.informe:
            messagebox.showwarning("Atención", "No se detectó ningún informe.")
            return

        self.label_estado.config(text="Extrayendo datos del informe...")
        self.update()

        try:
            datos = extraer_datos(self.informe)
            nombre = datos["nombre"]
            fecha = datos["fecha"]

            # Generar carátula temporal
            import tempfile
            temp_dir = os.path.expanduser("~")
            ruta_caratula_temp = os.path.join(temp_dir, "_caratula_temp.pdf")
            generar_caratula(
                ruta_salida=ruta_caratula_temp,
                nombre_paciente=nombre,
                fecha=fecha.replace("_", " "),
                tipo_estudio=datos["estudio"],
                ruta_logo=self.centro["logo"],
                nombre_centro=self.centro["nombre"],
                subtitulo_centro=self.centro["subtitulo"]
            )

            # Nombre y ubicación del archivo final
            nombre_archivo = f"{nombre.replace(' ', '_')}_{fecha}.pdf"
            from tkinter import filedialog
            ruta_final = filedialog.asksaveasfilename(
                initialfile=nombre_archivo,
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                title="Guardar reporte como"
            )
            if not ruta_final:
                self.label_estado.config(text="")
                return

            # Unir en orden: carátula → informe → mosaicos → VR
            self.label_estado.config(text="Uniendo archivos...")
            self.update()

            from pypdf import PdfWriter, PdfReader
            writer = PdfWriter()

            for ruta in [ruta_caratula_temp, self.informe] + self.mosaicos + [self.vr]:
                if ruta and os.path.exists(ruta):
                    reader = PdfReader(ruta)
                    for pagina in reader.pages:
                        writer.add_page(pagina)

            # Guardar PDF unido temporalmente
            ruta_temp_unido = os.path.join(temp_dir, "_temp_unido.pdf")
            with open(ruta_temp_unido, "wb") as f:
                writer.write(f)

            # Aplicar marca de agua a todas las páginas excepto la carátula
            from marca_agua import agregar_marca_agua
            from pypdf import PdfWriter as PdfWriterFinal, PdfReader as PdfReaderFinal
            from marca_agua import remover_fondo_blanco
            from reportlab.pdfgen import canvas as rl_canvas
            from reportlab.lib.utils import ImageReader
            import io

            reader_temp = PdfReaderFinal(ruta_temp_unido)
            writer_final = PdfWriterFinal()

           # Guardar PDF unido temporalmente
            ruta_temp_unido = "_temp_unido.pdf"
            with open(ruta_temp_unido, "wb") as f:
                writer.write(f)

            # Aplicar marca de agua solo al informe (página 2, índice 1)
            from marca_agua import remover_fondo_blanco
            from reportlab.pdfgen import canvas as rl_canvas
            from reportlab.lib.utils import ImageReader
            import io

            reader_temp = PdfReaderFinal(ruta_temp_unido)
            writer_final = PdfWriterFinal()

            for i, pagina in enumerate(reader_temp.pages):
                if i == 1:
                    # Solo el informe recibe marca de agua
                    ancho = float(pagina.mediabox.width)
                    alto = float(pagina.mediabox.height)
                    buf = io.BytesIO()
                    c = rl_canvas.Canvas(buf, pagesize=(ancho, alto))
                    c.setFillAlpha(0.06)
                    ruta_logo = self.centro["logo"]
                    if ruta_logo and os.path.exists(ruta_logo):
                        logo_buf = remover_fondo_blanco(ruta_logo)
                        logo = ImageReader(logo_buf)
                        tam = min(ancho, alto) * 0.6
                        x = (ancho - tam) / 2
                        y = (alto - tam) / 2
                        c.drawImage(logo, x, y, width=tam, height=tam,
                                   preserveAspectRatio=True, mask='auto')
                    c.save()
                    buf.seek(0)
                    pagina_marca = PdfReaderFinal(buf).pages[0]
                    pagina.merge_page(pagina_marca)
                writer_final.add_page(pagina)

            with open(ruta_final, "wb") as f:
                writer_final.write(f)

            os.remove(ruta_caratula_temp)
            os.remove(ruta_temp_unido)

            self.label_estado.config(
                text=f"✅ Reporte generado: {nombre_archivo}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.label_estado.config(text="")

if __name__ == "__main__":
    app = AplicacionPDF()
    app.mainloop()