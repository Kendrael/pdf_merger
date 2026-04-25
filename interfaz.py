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

        # Convertir primera página a imagen para analizar color
        from pypdfium2 import PdfDocument
        from PIL import Image
        import numpy as np

        doc = PdfDocument(ruta)
        page = doc[0]
        bitmap = page.render(scale=0.5)  # escala reducida para rapidez
        img = bitmap.to_pil()

        # Convertir a numpy y analizar saturación de color
        img_rgb = img.convert("RGB")
        arr = np.array(img_rgb)
        datos = [(int(r), int(g), int(b)) for r, g, b in arr.reshape(-1, 3)]

        # Contar píxeles con color significativo
        # Un píxel es "de color" si la diferencia entre sus canales RGB es > umbral
        umbral = 20
        pixeles_color = sum(
            1 for r, g, b in datos
            if max(r, g, b) - min(r, g, b) > umbral
        )

        porcentaje_color = pixeles_color / len(datos)

        # Si más del 2% de píxeles tienen color, es VR
        if porcentaje_color > 0.02:
            return "vr"
        else:
            return "mosaico"

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
        btn_config.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

        menu_centros = tk.Menu(btn_config, tearoff=0)
        for nombre in listar_centros():
            menu_centros.add_radiobutton(label=nombre,
                                        variable=self.var_centro,
                                        value=nombre,
                                        command=self._cambiar_centro)
        btn_config.config(menu=menu_centros)

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
    
    def _generar(self):
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
            ruta_caratula_temp = "_caratula_temp.pdf"
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
            carpeta = os.path.dirname(self.informe)
            ruta_final = os.path.join(carpeta, nombre_archivo)

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

            with open(ruta_final, "wb") as f:
                writer.write(f)

            os.remove(ruta_caratula_temp)

            self.label_estado.config(
                text=f"✅ Reporte generado: {nombre_archivo}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.label_estado.config(text="")

if __name__ == "__main__":
    app = AplicacionPDF()
    app.mainloop()