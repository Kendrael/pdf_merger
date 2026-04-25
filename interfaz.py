import tkinter as tk
from tkinter import filedialog, messagebox
import os
from extractor import extraer_datos
from caratula import generar_caratula
from merger import unir_pdfs

class AplicacionPDF(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SIRIX - Generador de Reportes")
        self.geometry("600x500")
        self.resizable(False, False)
        self.configure(bg="#1A3C6E")

        # Variables para rutas de archivos
        self.ruta_informe = tk.StringVar()
        self.ruta_mosaico = tk.StringVar()
        self.ruta_vr = tk.StringVar()

        self._construir_interfaz()

    def _construir_interfaz(self):
        # --- Título ---
        tk.Label(self, text="SIRIX", font=("Helvetica", 22, "bold"),
                bg="#1A3C6E", fg="white").pack(pady=(20, 0))
        tk.Label(self, text="Diagnóstico e Intervencionismo",
                font=("Helvetica", 11), bg="#1A3C6E", fg="white").pack()
        tk.Label(self, text="Generador de Reportes Tomográficos",
                font=("Helvetica", 10), bg="#1A3C6E", fg="#A8C4E0").pack(pady=(0, 20))

        # --- Panel central blanco ---
        panel = tk.Frame(self, bg="white", padx=20, pady=20)
        panel.pack(padx=20, fill="both", expand=True)

        # --- Selector de informe ---
        tk.Label(panel, text="Informe:", font=("Helvetica", 10, "bold"),
                bg="white", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(panel, textvariable=self.ruta_informe, width=45,
                state="readonly").grid(row=0, column=1, padx=5)
        tk.Button(panel, text="Seleccionar", bg="#1A3C6E", fg="white",
                 command=self._seleccionar_informe).grid(row=0, column=2)

        # --- Selector de mosaico ---
        tk.Label(panel, text="Mosaico:", font=("Helvetica", 10, "bold"),
                bg="white", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(panel, textvariable=self.ruta_mosaico, width=45,
                state="readonly").grid(row=1, column=1, padx=5)
        tk.Button(panel, text="Seleccionar", bg="#1A3C6E", fg="white",
                 command=self._seleccionar_mosaico).grid(row=1, column=2)

        # --- Selector de VR ---
        tk.Label(panel, text="VR:", font=("Helvetica", 10, "bold"),
                bg="white", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        tk.Entry(panel, textvariable=self.ruta_vr, width=45,
                state="readonly").grid(row=2, column=1, padx=5)
        tk.Button(panel, text="Seleccionar", bg="#1A3C6E", fg="white",
                 command=self._seleccionar_vr).grid(row=2, column=2)

        # --- Botón generar ---
        tk.Button(panel, text="GENERAR REPORTE", font=("Helvetica", 12, "bold"),
                 bg="#1A3C6E", fg="white", padx=20, pady=10,
                 command=self._generar).grid(row=3, column=0, columnspan=3, pady=20)

        # --- Estado ---
        self.label_estado = tk.Label(panel, text="", font=("Helvetica", 10),
                                    bg="white", fg="#1A3C6E", wraplength=500)
        self.label_estado.grid(row=4, column=0, columnspan=3)

    def _seleccionar_informe(self):
        ruta = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if ruta:
            self.ruta_informe.set(ruta)

    def _seleccionar_mosaico(self):
        ruta = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if ruta:
            self.ruta_mosaico.set(ruta)

    def _seleccionar_vr(self):
        ruta = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if ruta:
            self.ruta_vr.set(ruta)

    def _generar(self):
        if not self.ruta_informe.get():
            messagebox.showwarning("Atención", "El informe es obligatorio.")
            return

        self.label_estado.config(text="Extrayendo datos del informe...")
        self.update()

        try:
            # Extraer nombre y fecha del informe
            datos = extraer_datos(self.ruta_informe.get())
            nombre = datos["nombre"]
            fecha = datos["fecha"]

            # Generar carátula temporal
            ruta_caratula_temp = "_caratula_temp.pdf"
            generar_caratula(
                ruta_salida=ruta_caratula_temp,
                nombre_paciente=nombre,
                fecha=fecha.replace("_", " "),
                tipo_estudio="CT - Estudio Tomográfico",
                ruta_logo="logo_sirix.jpg"
            )

            # Nombre del archivo final
            nombre_archivo = f"{nombre.replace(' ', '_')}_{fecha}.pdf"
            carpeta = os.path.dirname(self.ruta_informe.get())
            ruta_final = os.path.join(carpeta, nombre_archivo)

            # Unir PDFs
            self.label_estado.config(text="Uniendo archivos...")
            self.update()

            unir_pdfs(
                ruta_caratula=ruta_caratula_temp,
                ruta_informe=self.ruta_informe.get(),
                ruta_mosaico=self.ruta_mosaico.get() or None,
                ruta_vr=self.ruta_vr.get() or None,
                ruta_salida=ruta_final
            )

            # Limpiar carátula temporal
            os.remove(ruta_caratula_temp)

            self.label_estado.config(
                text=f"✅ Reporte generado:\n{nombre_archivo}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.label_estado.config(text="")

if __name__ == "__main__":
    app = AplicacionPDF()
    app.mainloop()