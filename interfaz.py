import io
import os
import sys
import tkinter as tk
from tkinter import messagebox, filedialog

import numpy as np
import pdfplumber
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from tkinterdnd2 import TkinterDnD, DND_FILES

from caratula import generar_caratula
from config_manager import obtener_centro_activo, cambiar_centro, listar_centros
from extractor import extraer_datos, es_informe
from marca_agua import remover_fondo_blanco

def clasificar_pdf(ruta):
    """
    Analiza el PDF y determina si es informe, mosaico o VR.
    - Informe: texto con etiquetas de paciente y fecha (ver es_informe)
    - VR: imagen con color (R, G, B distintos)
    - Mosaico: imagen en escala de grises
    """
    try:
        with pdfplumber.open(ruta) as pdf:
            texto = pdf.pages[0].extract_text() or ""
            num_paginas = len(pdf.pages)

        # Primero verificar si es informe
        if es_informe(texto):
            return "informe"

        # Extraer imágenes de la primera página y analizar color
        imagenes = list(PdfReader(ruta).pages[0].images)

        if imagenes:
            img = Image.open(io.BytesIO(imagenes[0].data)).convert("RGB")
            arr = np.array(img)
            # Diferencia entre el canal más alto y el más bajo de cada píxel
            diferencia = (arr.max(axis=2).astype(np.int16)
                          - arr.min(axis=2).astype(np.int16))
            porcentaje_color = (diferencia > 10).mean()
            return "vr" if porcentaje_color > 0.005 else "mosaico"

        # Sin imágenes extraíbles, clasificar por número de páginas
        return "mosaico" if num_paginas > 1 else "vr"

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error clasificando {ruta}: {e}")
        return "desconocido"


class AplicacionPDF(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generador de Reportes")
        self.geometry("650x600")
        self.resizable(True, True)
        self.configure(bg="#3A3A3A")

        # Almacenamiento de archivos clasificados
        self.informe = None
        self.mosaicos = []
        self.vrs = []
        self.centro = obtener_centro_activo()
        self.color_primario = self.centro["color_primario"]
        self.color_acento = self.centro["color_acento"]
        self.var_centro = tk.StringVar(value=self.centro["nombre"])

        self._construir_interfaz()
        self.bind("<Button-1>", lambda e: self.focus_force())

    def _construir_interfaz(self):
        self.frame_header = tk.Frame(self, bg=self.color_primario)
        self.frame_header.pack(fill="x")

        # Línea de acento a la izquierda, cubre todo el alto del header
        self.frame_acento = tk.Frame(self.frame_header, bg=self.color_acento, width=5)
        self.frame_acento.pack(side="left", fill="y")

        # Contenedor derecho con todo el contenido del header
        self.frame_contenido = tk.Frame(self.frame_header, bg=self.color_primario)
        self.frame_contenido.pack(side="left", fill="both", expand=True)

        # Fila superior: botón config izquierda, botón about derecha
        self.frame_top = tk.Frame(self.frame_contenido, bg=self.color_primario)
        self.frame_top.pack(fill="x", padx=10, pady=(5, 0))

        self.btn_config = tk.Menubutton(self.frame_top, text="⚙ Centro", bg=self.color_primario, fg="#A8C4E0",
                    font=("Helvetica", 8), relief="flat",
                    activebackground=self.color_primario, activeforeground="white")
        self.btn_config.pack(side="left")

        menu_centros = tk.Menu(self.btn_config, tearoff=0)
        for nombre in listar_centros():
            menu_centros.add_radiobutton(label=nombre,
                                        variable=self.var_centro,
                                        value=nombre,
                                        command=self._cambiar_centro)
        self.btn_config.config(menu=menu_centros)

        self.btn_about = tk.Label(self.frame_top, text="?", bg=self.color_primario, fg="#A8C4E0",
                    font=("Helvetica", 8), cursor="hand2")
        self.btn_about.bind("<Button-1>", lambda e: self._mostrar_about())
        self.btn_about.pack(side="right")

        # Títulos centrados
        self.label_nombre_centro = tk.Label(self.frame_contenido, text=self.centro["nombre"],
                font=("Helvetica", 22, "bold"), bg=self.color_primario, fg="white")
        self.label_nombre_centro.pack(fill="x")

        self.label_subtitulo_centro = tk.Label(self.frame_contenido, text=self.centro["subtitulo"],
                font=("Helvetica", 11), bg=self.color_primario, fg="white")
        self.label_subtitulo_centro.pack(fill="x")

        self.label_generador = tk.Label(self.frame_contenido, text="Generador de Reportes",
                font=("Helvetica", 10), bg=self.color_primario, fg="#A8C4E0")
        self.label_generador.pack(pady=(0, 5), fill="x")

        # --- Zona de drag & drop ---
        self.zona_drop = tk.Label(
            self,
            text="Arrastre aquí los archivos PDF\n(Informe, Mosaicos y VR)",
            font=("Helvetica", 12),
            bg="white", fg=self.color_primario,
            relief="solid", bd=2,
            width=50, height=4
        )
        self.zona_drop.pack(padx=20, pady=(10, 0))
        self.zona_drop.drop_target_register(DND_FILES)
        self.zona_drop.dnd_bind('<<Drop>>', self._on_drop)

        # --- Botones de selección manual ---
        panel_botones = tk.Frame(self, bg="#3A3A3A")
        panel_botones.pack(padx=20, pady=8, fill="x")

        self.btn_informe = tk.Button(panel_botones, text="+ Informe", bg="white", fg=self.color_primario,
            font=("Helvetica", 9, "bold"),
            command=self._seleccionar_informe)
        self.btn_informe.pack(side="left", padx=5)

        self.btn_mosaicos = tk.Button(panel_botones, text="+ Mosaico(s)", bg="white", fg=self.color_primario,
                font=("Helvetica", 9, "bold"),
                command=self._seleccionar_mosaicos)
        self.btn_mosaicos.pack(side="left", padx=5)

        self.btn_vr = tk.Button(panel_botones, text="+ VR", bg="white", fg=self.color_primario,
                font=("Helvetica", 9, "bold"),
                command=self._seleccionar_vr)
        self.btn_vr.pack(side="left", padx=5)

        self.btn_limpiar = tk.Label(panel_botones, text="Limpiar", bg=self.color_acento, fg="white",
                font=("Helvetica", 9), padx=8, pady=4, cursor="hand2")
        self.btn_limpiar.bind("<Button-1>", lambda e: self._limpiar())
        self.btn_limpiar.pack(side="right", padx=5)

        # --- Panel de archivos detectados ---
        panel = tk.Frame(self, bg="white", padx=20, pady=15)
        panel.pack(padx=20, fill="both", expand=True)

        self.label_archivos = tk.Label(panel, text="Archivos detectados:",
            font=("Helvetica", 10, "bold"), bg="white",
            fg=self.color_primario)
        self.label_archivos.pack(anchor="w")

        self.texto_archivos = tk.Text(panel, height=8, width=70,
                              state="disabled", bg="#F5F8FC", fg=self.color_primario,
                              font=("Helvetica", 9), relief="flat",
                              insertbackground=self.color_primario)
        self.texto_archivos.pack(pady=5)

        # --- Botón generar ---
        self.btn_generar = tk.Label(self, text="GENERAR REPORTE",
                font=("Helvetica", 12, "bold"),
                bg=self.color_acento, fg="white",
                padx=20, pady=10, cursor="hand2")
        self.btn_generar.bind("<Button-1>", lambda e: self._generar())
        self.btn_generar.pack(pady=10)

        # --- Estado ---
        self.label_estado = tk.Label(self, text="",
                            font=("Helvetica", 10),
                            bg="#3A3A3A", fg="white",
                            wraplength=580)
        self.label_estado.pack(pady=5)

    def _seleccionar_informe(self):
        ruta = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if ruta:
            self.informe = ruta
            self._actualizar_panel()

    def _seleccionar_mosaicos(self):
        rutas = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if rutas:
            self.mosaicos.extend(rutas)
            self._actualizar_panel()

    def _seleccionar_vr(self):
        rutas = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if rutas:
            self.vrs.extend(rutas)
            self._actualizar_panel()

    def _limpiar(self):
        self.informe = None
        self.mosaicos = []
        self.vrs = []
        self._actualizar_panel()
        self.label_estado.config(text="")
        
    def _on_drop(self, event):
        """Recibe los archivos arrastrados, los clasifica y muestra el resultado."""
        # Parsear rutas (pueden venir con llaves si tienen espacios)
        rutas_raw = self.tk.splitlist(event.data)

        self.informe = None
        self.mosaicos = []
        self.vrs = []

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
                self.vrs.append(ruta)

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

        if self.vrs:
            for i, v in enumerate(self.vrs, 1):
                self.texto_archivos.insert(tk.END,
                    f"VR {i}:      {os.path.basename(v)}\n")
        else:
            self.texto_archivos.insert(tk.END, "VR:      no detectado\n")

        self.texto_archivos.config(state="disabled")
        self.update_idletasks()

    def _cambiar_centro(self):
        nombre = self.var_centro.get()
        cambiar_centro(nombre)
        self.centro = obtener_centro_activo()
        self.color_primario = self.centro["color_primario"]
        self.color_acento = self.centro["color_acento"]
        self.configure(bg="#3A3A3A")
        self.label_nombre_centro.config(text=self.centro["nombre"], bg=self.color_primario)
        self.label_subtitulo_centro.config(text=self.centro["subtitulo"], bg=self.color_primario)
        self.zona_drop.config(fg=self.color_primario)
        self.label_estado.config(text=f"✅ Centro activo: {self.centro['nombre']}")
        self.btn_informe.config(fg=self.color_primario)
        self.btn_mosaicos.config(fg=self.color_primario)
        self.btn_vr.config(fg=self.color_primario)
        self.btn_limpiar.config(bg=self.color_acento, highlightbackground=self.color_acento)
        self.label_archivos.config(fg=self.color_primario)
        self.texto_archivos.config(fg=self.color_primario, insertbackground=self.color_primario)
        self.btn_generar.config(bg=self.color_acento, highlightbackground=self.color_acento)
        self.btn_config.config(bg=self.color_primario, activebackground=self.color_primario)
        self.btn_about.config(bg=self.color_primario, activebackground=self.color_primario)
        self.frame_header.config(bg=self.color_primario)
        self.label_generador.config(bg=self.color_primario)
        self.frame_top.config(bg=self.color_primario)
        self.frame_acento.config(bg=self.color_acento)
        self.frame_contenido.config(bg=self.color_primario)
    
    def _mostrar_about(self):
        messagebox.showinfo(
            "Acerca de",
            "Generador de Reportes Imagenológicos\n"
            "Versión 1.0.7\n\n"
            "Desarrollado por Kenny Mejia\n"
            "Bioimagenólogo & Health Data Specialist\n"
            "La Paz, Bolivia\n\n"
            "github.com/Kendrael/pdf_merger"
        )

    def _resolver_ruta_logo(self):
        """Busca el logo del centro activo (dentro del bundle si está compilado)."""
        ruta_logo = self.centro["logo"]
        if os.path.isabs(ruta_logo):
            return ruta_logo
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
            for directorio in [base,
                               os.path.join(base, '..', 'Resources'),
                               os.path.join(base, '..', 'Frameworks')]:
                candidato = os.path.join(directorio, ruta_logo)
                if os.path.exists(candidato):
                    return candidato
            return ruta_logo
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta_logo)

    def _pagina_marca_agua(self, logo_png, ancho, alto):
        """Devuelve una página PDF con el logo centrado y muy sutil."""
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=(ancho, alto))
        c.setFillAlpha(0.06)
        tam = min(ancho, alto) * 0.6
        c.drawImage(ImageReader(io.BytesIO(logo_png)),
                    (ancho - tam) / 2, (alto - tam) / 2,
                    width=tam, height=tam,
                    preserveAspectRatio=True, mask='auto')
        c.save()
        buf.seek(0)
        return PdfReader(buf).pages[0]

    def _generar(self):
        # Forzar directorio de trabajo a home del usuario
        os.chdir(os.path.expanduser("~"))

        if not self.informe:
            messagebox.showwarning("Atención", "No se detectó ningún informe.")
            return

        self.label_estado.config(text="Extrayendo datos del informe...")
        self.update()

        ruta_caratula_temp = os.path.join(os.path.expanduser("~"), "_caratula_temp.pdf")

        try:
            datos = extraer_datos(self.informe)
            nombre = datos["nombre"]
            fecha = datos["fecha"]

            # Generar carátula temporal
            generar_caratula(
                ruta_salida=ruta_caratula_temp,
                nombre_paciente=nombre.upper(),
                fecha=fecha.replace("_", " "),
                tipo_estudio=datos["estudio"],
                nombre_centro=self.centro["nombre"]
            )

            # Nombre y ubicación del archivo final
            nombre_archivo = f"{nombre.replace(' ', '_')}_{fecha}.pdf"
            ruta_final = filedialog.asksaveasfilename(
                initialfile=nombre_archivo,
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                title="Guardar reporte como"
            )
            if not ruta_final:
                self.label_estado.config(text="")
                return

            self.label_estado.config(text="Uniendo archivos...")
            self.update()

            # Logo para la marca de agua (se prepara una sola vez)
            ruta_logo = self._resolver_ruta_logo()
            logo_png = None
            if ruta_logo and os.path.exists(ruta_logo):
                logo_png = remover_fondo_blanco(ruta_logo).getvalue()

            # Unir en orden: carátula → informe → mosaicos → VR
            # La marca de agua solo va en las páginas del informe
            writer = PdfWriter()
            archivos = [ruta_caratula_temp, self.informe] + self.mosaicos + self.vrs
            for ruta in archivos:
                if not (ruta and os.path.exists(ruta)):
                    continue
                for pagina in PdfReader(ruta).pages:
                    if ruta == self.informe and logo_png:
                        ancho = float(pagina.mediabox.width)
                        alto = float(pagina.mediabox.height)
                        pagina.merge_page(self._pagina_marca_agua(logo_png, ancho, alto))
                    writer.add_page(pagina)

            with open(ruta_final, "wb") as f:
                writer.write(f)

            self.label_estado.config(
                text=f"✅ Reporte generado: {nombre_archivo}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", str(e))
            self.label_estado.config(text="")

        finally:
            if os.path.exists(ruta_caratula_temp):
                os.remove(ruta_caratula_temp)

if __name__ == "__main__":
    app = AplicacionPDF()
    app.mainloop()