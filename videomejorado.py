import threading
import json
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from yt_dlp import YoutubeDL
import time
import os

CONFIG_FILE = "config.json"

class DescargadorVideosApp:
    def __init__(self, root):
        self.root = root
        root.title("Descargador Profesional de Videos y Listas")
        root.geometry("650x740")
        root.resizable(False, False)

        self.ydl = None
        self.descarga_activa = False
        self.thread_descarga = None
        self.cola_urls = []
        self.scheduled_task = None
        self.pausado = False
        self.detener_descarga = False

        self.temas = {
            "Claro": {"bg": "#f0f0f0", "fg": "#000000", "entry_bg": "#ffffff", "entry_fg": "#000000"},
            "Oscuro": {"bg": "#2e2e2e", "fg": "#ffffff", "entry_bg": "#3e3e3e", "entry_fg": "#ffffff"},
            "Azul": {"bg": "#dbe9f4", "fg": "#1a1a1a", "entry_bg": "#ffffff", "entry_fg": "#1a1a1a"},
            "Verde": {"bg": "#e6f2e6", "fg": "#004d00", "entry_bg": "#ffffff", "entry_fg": "#004d00"},
            "Naranja": {"bg": "#fff4e6", "fg": "#994d00", "entry_bg": "#ffffff", "entry_fg": "#994d00"},
            "Púrpura": {"bg": "#f3e6ff", "fg": "#4b0082", "entry_bg": "#ffffff", "entry_fg": "#4b0082"},
            "Rojo": {"bg": "#ffe6e6", "fg": "#800000", "entry_bg": "#ffffff", "entry_fg": "#800000"},
            "Gris": {"bg": "#d9d9d9", "fg": "#404040", "entry_bg": "#f2f2f2", "entry_fg": "#404040"},
            "Turquesa": {"bg": "#e0f7f7", "fg": "#004c4c", "entry_bg": "#ffffff", "entry_fg": "#004c4c"},
            "Amarillo": {"bg": "#fffde6", "fg": "#999900", "entry_bg": "#ffffff", "entry_fg": "#999900"},
            "Coral": {"bg": "#ffe0db", "fg": "#b22222", "entry_bg": "#ffffff", "entry_fg": "#b22222"},
            "Cian": {"bg": "#e0ffff", "fg": "#007777", "entry_bg": "#ffffff", "entry_fg": "#007777"},
            "Rosa": {"bg": "#ffe6f2", "fg": "#cc0066", "entry_bg": "#ffffff", "entry_fg": "#cc0066"},
            "Menta": {"bg": "#e6fff5", "fg": "#008060", "entry_bg": "#ffffff", "entry_fg": "#008060"},
            "Chocolate": {"bg": "#f2e6e6", "fg": "#5c3317", "entry_bg": "#ffffff", "entry_fg": "#5c3317"},
            "Oliva": {"bg": "#f0f5e6", "fg": "#556b2f", "entry_bg": "#ffffff", "entry_fg": "#556b2f"},
            "Lavanda": {"bg": "#f5e6ff", "fg": "#663399", "entry_bg": "#ffffff", "entry_fg": "#663399"},
            "Celeste": {"bg": "#e6f7ff", "fg": "#007acc", "entry_bg": "#ffffff", "entry_fg": "#007acc"},
            "Durazno": {"bg": "#fff0e6", "fg": "#cc6600", "entry_bg": "#ffffff", "entry_fg": "#cc6600"},
            "Tierra": {"bg": "#ede7dd", "fg": "#5d4037", "entry_bg": "#ffffff", "entry_fg": "#5d4037"},
            "Vino": {"bg": "#f5e6ec", "fg": "#800040", "entry_bg": "#ffffff", "entry_fg": "#800040"},
            "Marino": {"bg": "#e6eaf2", "fg": "#003366", "entry_bg": "#ffffff", "entry_fg": "#003366"},
            "Aguamarina": {"bg": "#e0fff9", "fg": "#007f7f", "entry_bg": "#ffffff", "entry_fg": "#007f7f"},
            "Esmeralda": {"bg": "#e6fff0", "fg": "#006644", "entry_bg": "#ffffff", "entry_fg": "#006644"},
            "Mandarina": {"bg": "#fff5e6", "fg": "#cc5500", "entry_bg": "#ffffff", "entry_fg": "#cc5500"},
            "Carbón": {"bg": "#3a3a3a", "fg": "#f0f0f0", "entry_bg": "#4a4a4a", "entry_fg": "#ffffff"},
            "Cobre": {"bg": "#fff0e0", "fg": "#b87333", "entry_bg": "#ffffff", "entry_fg": "#b87333"},
            "Marfil": {"bg": "#fffff0", "fg": "#4d4d4d", "entry_bg": "#ffffff", "entry_fg": "#4d4d4d"},
            "Perla": {"bg": "#f8f8ff", "fg": "#444444", "entry_bg": "#ffffff", "entry_fg": "#444444"},
            "Granito": {"bg": "#f2f2f2", "fg": "#5a5a5a", "entry_bg": "#ffffff", "entry_fg": "#5a5a5a"}
        }

        self.estilo = ttk.Style(root)
        self.estilo.theme_use('clam')

        self._crear_widgets()
        self._configurar_eventos()
        self._cargar_config()

        self.aplicar_tema()
        self.verificar_carpeta_valida()
        root.protocol("WM_DELETE_WINDOW", self.cerrar_app)

    def _crear_widgets(self):
        ttk.Label(self.root, text="🎨 Tema de la interfaz:").pack(anchor='w', padx=10, pady=(10, 2))
        self.combo_tema = ttk.Combobox(self.root, values=list(self.temas.keys()), width=15, state="readonly")
        self.combo_tema.pack(padx=10)
        self.combo_tema.set("Claro")

        ttk.Label(self.root, text="🔗 URL del video, lista o canal:").pack(anchor='w', padx=10, pady=(10, 2))
        frame_url = ttk.Frame(self.root)
        frame_url.pack(fill='x', padx=10)
        self.entrada_url = ttk.Entry(frame_url, width=60)
        self.entrada_url.pack(side='left', fill='x', expand=True)
        ttk.Button(frame_url, text="Agregar a cola", command=self.agregar_a_cola).pack(side='left', padx=5)

        ttk.Label(self.root, text="Cola de Descargas (URL - Tipo):").pack(anchor='w', padx=10)
        self.lista_urls = tk.Listbox(self.root, height=7)
        self.lista_urls.pack(fill='both', padx=10, pady=(5, 5))

        frame_botones_cola = ttk.Frame(self.root)
        frame_botones_cola.pack(pady=(0, 10))
        ttk.Button(frame_botones_cola, text="🗑 Quitar seleccionado", command=self.quitar_url_seleccionada).pack(side='left', padx=5)
        ttk.Button(frame_botones_cola, text="🧹 Limpiar cola", command=self.limpiar_cola).pack(side='left', padx=5)

        ttk.Label(self.root, text="🎮 Formato:").pack(anchor='w', padx=10, pady=(10, 2))
        self.combo_formato = ttk.Combobox(self.root, values=["mp4", "mp3"], width=10, state="readonly")
        self.combo_formato.set("mp4")
        self.combo_formato.pack(padx=10)

        ttk.Label(self.root, text="🎚️ Calidad deseada:").pack(anchor='w', padx=10, pady=(10, 2))
        self.combo_calidad = ttk.Combobox(self.root, values=["Alta (1080p+)", "Media (720p)", "Baja (480p)"], width=20, state="readonly")
        self.combo_calidad.set("Alta (1080p+)")
        self.combo_calidad.pack(padx=10)

        ttk.Label(self.root, text="📂 Carpeta destino:").pack(anchor='w', padx=10, pady=(10, 2))
        frame_carpeta = ttk.Frame(self.root)
        frame_carpeta.pack(fill='x', padx=10)
        self.entrada_carpeta = ttk.Entry(frame_carpeta)
        self.entrada_carpeta.pack(side='left', fill='x', expand=True)
        ttk.Button(frame_carpeta, text="Seleccionar", command=self.seleccionar_carpeta).pack(side='left', padx=5)
        self.boton_abrir = ttk.Button(frame_carpeta, text="Abrir carpeta", command=self.abrir_carpeta_destino, state='disabled')
        self.boton_abrir.pack(side='left', padx=5)

        self.info_video = ttk.Label(self.root, text="", wraplength=600, justify='left')
        self.info_video.pack(pady=5)

        ttk.Label(self.root, text="⏰ Programar descarga (opcional, formato 24h):").pack(anchor='w', padx=10, pady=(10, 2))
        frame_prog = ttk.Frame(self.root)
        frame_prog.pack(fill='x', padx=10)
        ttk.Label(frame_prog, text="Fecha (YYYY-MM-DD):").pack(side='left')
        self.entrada_fecha = ttk.Entry(frame_prog, width=12)
        self.entrada_fecha.pack(side='left', padx=(5, 15))
        ttk.Label(frame_prog, text="Hora (HH:MM):").pack(side='left')
        self.entrada_hora = ttk.Entry(frame_prog, width=7)
        self.entrada_hora.pack(side='left', padx=(5, 0))
        ttk.Label(frame_prog, text=" (vacío = descarga inmediata)").pack(side='left')

        self.boton_descargar = ttk.Button(self.root, text="⬇️ Descargar cola", command=self.iniciar_descarga)
        self.boton_descargar.pack(pady=10)

        self.progress_var = tk.DoubleVar()
        self.barra_progreso = ttk.Progressbar(self.root, maximum=100, variable=self.progress_var, mode='determinate')
        self.barra_progreso.pack(fill='x', padx=10)
        self.etiqueta_status = ttk.Label(self.root, text="", foreground="blue")
        self.etiqueta_status.pack(pady=5)

        frame_botones_control = ttk.Frame(self.root)
        frame_botones_control.pack(pady=5)

        self.boton_pausar = tk.Button(frame_botones_control, text="⏸ Pausar", command=self.pausar_descarga, state='disabled')
        self.boton_pausar.pack(side='left', padx=5)

        self.boton_reanudar = tk.Button(frame_botones_control, text="▶ Reanudar", command=self.reanudar_descarga, state='disabled')
        self.boton_reanudar.pack(side='left', padx=5)

        self.boton_detener = tk.Button(frame_botones_control, text="⛔ Detener", command=self.detener_descarga_func, state='disabled')
        self.boton_detener.pack(side='left', padx=5)
        self.boton_detener.pack(pady=2)
        self.boton_cancelar = ttk.Button(self.root, text="❌ Cancelar", command=self.cancelar_descarga, state='disabled')
        self.boton_cancelar.pack()

    def _configurar_eventos(self):
        self.combo_tema.bind("<<ComboboxSelected>>", lambda e: self.aplicar_tema())

    def aplicar_tema(self):
        tema = self.combo_tema.get()
        config = self.temas.get(tema, self.temas["Claro"])
        self.root.configure(bg=config["bg"])
        for widget in self.root.winfo_children():
            try:
                widget.configure(background=config["bg"], foreground=config["fg"])
            except Exception:
                pass
        self.estilo.configure('TEntry', fieldbackground=config["entry_bg"], foreground=config["entry_fg"])
        self.estilo.configure('TLabel', background=config["bg"], foreground=config["fg"])
        self.estilo.configure('TButton', background=config["bg"], foreground=config["fg"])

    def seleccionar_carpeta(self):
        ruta = filedialog.askdirectory()
        if ruta:
            self.entrada_carpeta.delete(0, tk.END)
            self.entrada_carpeta.insert(0, ruta)
            self.verificar_carpeta_valida()

    def abrir_carpeta_destino(self):
        carpeta = self.entrada_carpeta.get().strip()
        if carpeta and os.path.isdir(carpeta):
            try:
                if platform.system() == "Windows":
                    os.startfile(carpeta)
                elif platform.system() == "Darwin":
                    os.system(f'open "{carpeta}"')
                else:
                    os.system(f'xdg-open "{carpeta}"')
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}")

    def verificar_carpeta_valida(self):
        ruta = self.entrada_carpeta.get().strip()
        if ruta and os.path.isdir(ruta):
            self.boton_abrir.config(state="normal")
        else:
            self.boton_abrir.config(state="disabled")

    def agregar_a_cola(self):
        url = self.entrada_url.get().strip()
        if url:
            tipo = "Canal" if "channel" in url else "Lista" if "list" in url else "Video"
            self.cola_urls.append((url, tipo))
            self.lista_urls.insert(tk.END, f"{url} - {tipo}")
            self.entrada_url.delete(0, tk.END)
        else:
            messagebox.showwarning("Aviso", "Por favor, introduce una URL válida.")

    def quitar_url_seleccionada(self):
        seleccion = self.lista_urls.curselection()
        if seleccion:
            idx = seleccion[0]
            self.lista_urls.delete(idx)
            del self.cola_urls[idx]

    def limpiar_cola(self):
        self.lista_urls.delete(0, tk.END)
        self.cola_urls.clear()

    def obtener_opciones_descarga(self):
        formato = self.combo_formato.get()
        calidad = self.combo_calidad.get()
        carpeta = self.entrada_carpeta.get().strip()

        ydl_opts = {
            "outtmpl": os.path.join(carpeta, "%(title)s.%(ext)s"),
            "noplaylist": False,
            "progress_hooks": [self.actualizar_progreso],
            "quiet": True,
            "format": "bestvideo+bestaudio/best",
        }

        if formato == "mp3":
            ydl_opts["format"] = "bestaudio"
            ydl_opts["postprocessors"] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif calidad == "Media (720p)":
            ydl_opts["format"] = "bestvideo[height<=720]+bestaudio/best[height<=720]"
        elif calidad == "Baja (480p)":
            ydl_opts["format"] = "bestvideo[height<=480]+bestaudio/best[height<=480]"

        return ydl_opts

    def actualizar_progreso(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total_bytes:
                porcentaje = downloaded / total_bytes * 100
                self.progress_var.set(porcentaje)
                self.etiqueta_status.config(text=f"Descargando: {d['_percent_str']} {d['_eta_str']}")
                self.root.update_idletasks()
        elif d['status'] == 'finished':
            self.progress_var.set(100)
            self.etiqueta_status.config(text="✅ Descarga finalizada")

    def iniciar_descarga(self):
        if not self.cola_urls:
            messagebox.showwarning("Aviso", "La cola de descargas está vacía.")
            return
        if not self.entrada_carpeta.get().strip():
            messagebox.showwarning("Aviso", "Debes seleccionar una carpeta destino.")
            return

        self.pausado = False
        self.detener_descarga = False
        self.boton_pausar.config(state="normal")
        self.boton_detener.config(state="normal")
        self.boton_cancelar.config(state="normal")
        self.progress_var.set(0)
        self.etiqueta_status.config(text="")

        fecha = self.entrada_fecha.get().strip()
        hora = self.entrada_hora.get().strip()
        if fecha and hora:
            try:
                fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
                delay = (fecha_hora - datetime.now()).total_seconds()
                if delay > 0:
                    self.etiqueta_status.config(text=f"Descarga programada para: {fecha_hora}")
                    self.scheduled_task = threading.Timer(delay, self.descargar_cola)
                    self.scheduled_task.start()
                    return
                else:
                    messagebox.showerror("Error", "La fecha y hora deben ser futuras.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha u hora inválido.")
                return

        self.descargar_cola()

    def descargar_cola(self):
        self.descarga_activa = True
        self.thread_descarga = threading.Thread(target=self._descargar_cola_thread)
        self.thread_descarga.start()

    def _descargar_cola_thread(self):
        ydl_opts = self.obtener_opciones_descarga()
        self.ydl = YoutubeDL(ydl_opts)

        for url, tipo in self.cola_urls:
            if self.detener_descarga:
                break
            while self.pausado:
                time.sleep(1)
            try:
                self.info_video.config(text=f"Descargando {tipo}:\n{url}")
                self.ydl.download([url])
            except Exception as e:
                self.etiqueta_status.config(text=f"❌ Error: {e}")

        self.descarga_activa = False
        self.boton_pausar.config(state="disabled")
        self.boton_reanudar.config(state="disabled")
        self.boton_detener.config(state="disabled")
        self.boton_cancelar.config(state="disabled")
        self.info_video.config(text="✔️ Todas las descargas completadas")
        self.progress_var.set(0)

    def pausar_descarga(self):
        self.pausado = True
        self.etiqueta_status.config(text="⏸️ Descarga pausada")
        self.boton_pausar.config(state="disabled")
        self.boton_reanudar.config(state="normal")

    def reanudar_descarga(self):
        self.pausado = False
        self.etiqueta_status.config(text="▶️ Reanudando descarga...")
        self.boton_pausar.config(state="normal")
        self.boton_reanudar.config(state="disabled")

    def detener_descarga_func(self):
        self.detener_descarga = True
        self.etiqueta_status.config(text="⛔ Descarga detenida")

    def cancelar_descarga(self):
        if self.scheduled_task and self.scheduled_task.is_alive():
            self.scheduled_task.cancel()
            self.etiqueta_status.config(text="❌ Descarga programada cancelada")
        else:
            self.detener_descarga_func()

    def cerrar_app(self):
        if self.descarga_activa:
            if not messagebox.askyesno("Salir", "Hay una descarga en curso. ¿Estás seguro de que quieres salir?"):
                return
        self.cancelar_descarga()
        self._guardar_config()
        self.root.destroy()

    def _guardar_config(self):
        config = {
            "carpeta_destino": self.entrada_carpeta.get().strip(),
            "tema": self.combo_tema.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def _cargar_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.entrada_carpeta.insert(0, config.get("carpeta_destino", ""))
                    self.combo_tema.set(config.get("tema", "Claro"))
            except Exception:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = DescargadorVideosApp(root)
    root.mainloop()