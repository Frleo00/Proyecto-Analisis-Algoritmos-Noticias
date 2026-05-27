import webbrowser
import customtkinter as ctk
from proyectoDAA import AnalizadorNoticias

ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")

class AppAnalizador(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.analizador = AnalizadorNoticias()
        self.analizador.cargar(usar_rss=True, usar_newsapi=False)
        
        self.title("Analizador de Noticias - Estructuras de Datos")
        self.geometry("750x650")
        
        self.tabview = ctk.CTkTabview(self, width=700, height=600)
        self.tabview.pack(padx=20, pady=20)
        
        self.tab_busqueda = self.tabview.add("Búsqueda")
        self.tab_stats = self.tabview.add("Palabras Frecuentes (HeapSort)")
        
        self.label_titulo = ctk.CTkLabel(self.tab_busqueda, text="Analizador de Noticias", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.pack(padx=20, pady=20)
        
        self.entry_busqueda = ctk.CTkEntry(self.tab_busqueda, placeholder_text="Escribe tu búsqueda aquí...", width=400)
        self.entry_busqueda.pack(padx=20, pady=5)
        self.entry_busqueda.bind("<KeyRelease>", self.evento_autocompletar)
        
        self.label_sugerencias = ctk.CTkLabel(self.tab_busqueda, text="", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
        self.label_sugerencias.pack(padx=20, pady=2)
        
        self.btn_buscar = ctk.CTkButton(self.tab_busqueda, text="Buscar con Hash O(1)", command=self.evento_buscar)
        self.btn_buscar.pack(padx=20, pady=10)
        
        self.txt_resultados = ctk.CTkTextbox(self.tab_busqueda, width=600, height=300)
        self.txt_resultados.pack(padx=20, pady=15)
        
        self.txt_resultados.tag_config("link_estilo", foreground="#1f538d", underline=True)
        self.txt_resultados.tag_bind("link_estilo", "<Enter>", lambda e: self.txt_resultados.configure(cursor="hand2"))
        self.txt_resultados.tag_bind("link_estilo", "<Leave>", lambda e: self.txt_resultados.configure(cursor=""))

        self.label_titulo_heap = ctk.CTkLabel(self.tab_stats, text="Top 10 Palabras más frecuentes", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_titulo_heap.pack(padx=20, pady=20)
        
        self.txt_heapsort = ctk.CTkTextbox(self.tab_stats, width=500, height=350, font=ctk.CTkFont(family="Courier", size=14))
        self.txt_heapsort.pack(padx=20, pady=10)
        
        self.actualizar_heapsort()

    def actualizar_heapsort(self):
        top = self.analizador.top_palabras(10)
        self.txt_heapsort.delete("0.0", "end")
        self.txt_heapsort.insert("end", f"{'PALABRA':<20} | {'MENCIONES':<10}\n")
        self.txt_heapsort.insert("end", "-"*35 + "\n")
        for palabra, frecuencia in top:
            self.txt_heapsort.insert("end", f"{palabra:<20} | {frecuencia:<10}\n")

    def evento_autocompletar(self, event):
        texto_actual = self.entry_busqueda.get().strip()
        palabras = texto_actual.split()
        if not palabras:
            self.label_sugerencias.configure(text="")
            return
        ultima_palabra = palabras[-1]
        if len(ultima_palabra) >= 2:
            sugerencias = self.analizador.autocompletar(ultima_palabra)
            if sugerencias:
                self.label_sugerencias.configure(text="Sugerencias: " + ", ".join(sugerencias))
            else:
                self.label_sugerencias.configure(text="")
        else:
            self.label_sugerencias.configure(text="")

    def evento_buscar(self):
        consulta = self.entry_busqueda.get()
        resultados = self.analizador.buscar(consulta)
        self.txt_resultados.delete("0.0", "end")
        self.txt_resultados.insert("end", f"Resultados para: '{consulta}' ({len(resultados)} encontrados)\n")
        self.txt_resultados.insert("end", "="*50 + "\n\n")
        for idx, art in enumerate(resultados):
            self.txt_resultados.insert("end", f"Titulo: {art['titulo']}\n")
            self.txt_resultados.insert("end", f"Fuente: {art['fuente']}\n")
            self.txt_resultados.insert("end", f"Resumen: {art['resumen']}\n")
            self.txt_resultados.insert("end", "Enlace: ")
            url = art['link']
            tag_unico = f"link-{idx}"
            self.txt_resultados.insert("end", f"{url}\n", ("link_estilo", tag_unico))
            self.txt_resultados.tag_bind(tag_unico, "<Button-1>", lambda e, url_actual=url: webbrowser.open(url_actual))
            self.txt_resultados.insert("end", "-"*50 + "\n\n")

if __name__ == "__main__":
    app = AppAnalizador()
    app.mainloop()