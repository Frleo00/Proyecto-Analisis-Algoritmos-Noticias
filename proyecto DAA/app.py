import webbrowser
import threading
import customtkinter as ctk
from proyectoDAA import AnalizadorNoticias

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BG_DEEP   = "#0D0F14"
BG_CARD   = "#151820"
BG_HOVER  = "#1C2030"
ACCENT    = "#E8C547"
ACCENT2   = "#4A9EFF"
MUTED     = "#6B7280"
TEXT_MAIN = "#E8ECF0"
TEXT_SUB  = "#9CA3AF"
RED_ERR   = "#EF4444"
GREEN_OK  = "#22C55E"
BORDER    = "#252A38"


class TarjetaNoticia(ctk.CTkFrame):
    """Tarjeta visual para cada resultado de búsqueda."""
    def __init__(self, master, articulo: dict, idx: int, **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)

        self.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
        hdr.columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text=f"#{idx:02d}", font=ctk.CTkFont("Courier New", 11, "bold"),
                     text_color=ACCENT, width=36, anchor="w").grid(row=0, column=0)
        ctk.CTkLabel(hdr, text=articulo["fuente"], font=ctk.CTkFont(size=11),
                     text_color=MUTED, anchor="e").grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(self, text=articulo["titulo"],
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_MAIN, wraplength=560, anchor="w",
                     justify="left").grid(row=1, column=0, sticky="ew", padx=14, pady=(2, 4))

        if articulo.get("resumen"):
            res = articulo["resumen"][:160] + ("…" if len(articulo["resumen"]) > 160 else "")
            ctk.CTkLabel(self, text=res, font=ctk.CTkFont(size=11),
                         text_color=TEXT_SUB, wraplength=560, anchor="w",
                         justify="left").grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 6))

        link_btn = ctk.CTkButton(
            self, text=f"🔗 {articulo['link'][:65]}{'…' if len(articulo['link']) > 65 else ''}",
            font=ctk.CTkFont(size=10), text_color=ACCENT2,
            fg_color="transparent", hover_color=BG_HOVER,
            anchor="w", cursor="hand2",
            command=lambda url=articulo["link"]: webbrowser.open(url),
        )
        link_btn.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))


class BarraFrequencia(ctk.CTkFrame):
    """Fila de barra horizontal para el ranking HeapSort."""
    def __init__(self, master, rank: int, palabra: str, freq: int, max_freq: int, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.columnconfigure(1, weight=1)

        pct = freq / max_freq if max_freq else 0

        ctk.CTkLabel(self, text=f"{rank:2}.", width=26,
                     font=ctk.CTkFont("Courier New", 12, "bold"),
                     text_color=ACCENT, anchor="e").grid(row=0, column=0, padx=(0, 8))

        ctk.CTkLabel(self, text=palabra, width=130,
                     font=ctk.CTkFont("Courier New", 12),
                     text_color=TEXT_MAIN, anchor="w").grid(row=0, column=1, sticky="w")

        # Barra de fondo
        barra_bg = ctk.CTkFrame(self, height=14, fg_color=BORDER, corner_radius=4)
        barra_bg.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        barra_bg.columnconfigure(0, weight=1)

        ancho_fill = max(4, int(pct * 200))
        ctk.CTkFrame(barra_bg, height=14, width=ancho_fill,
                     fg_color=ACCENT, corner_radius=4).place(x=0, y=0)

        ctk.CTkLabel(self, text=f"{freq:,}", width=50,
                     font=ctk.CTkFont("Courier New", 11),
                     text_color=MUTED, anchor="e").grid(row=0, column=3)

        self.columnconfigure(2, weight=1)


class EstadisticaBadge(ctk.CTkFrame):
    """Badge de estadística con número grande."""
    def __init__(self, master, valor: str, etiqueta: str, color=ACCENT, **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)
        ctk.CTkLabel(self, text=valor,
                     font=ctk.CTkFont("Courier New", 22, "bold"),
                     text_color=color).pack(pady=(14, 2), padx=20)
        ctk.CTkLabel(self, text=etiqueta, font=ctk.CTkFont(size=10),
                     text_color=MUTED).pack(pady=(0, 12), padx=20)


class AppAnalizador(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.configure(fg_color=BG_DEEP)
        self.title("📰 Analizador de Noticias — DAA")
        self.geometry("900x720")
        self.minsize(760, 600)

        self.analizador = AnalizadorNoticias()
        self._cargando = True

        self._construir_ui()
        threading.Thread(target=self._cargar_datos, daemon=True).start()

    def _construir_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG_CARD,
                              corner_radius=0, border_width=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="📰",
                     font=ctk.CTkFont(size=28)).grid(row=0, column=0, padx=(20, 8), pady=14)
        ctk.CTkLabel(header, text="ANALIZADOR DE NOTICIAS",
                     font=ctk.CTkFont("Georgia", 18, "bold"),
                     text_color=ACCENT).grid(row=0, column=1, sticky="w", pady=14)

        self.lbl_estado = ctk.CTkLabel(header, text="⏳ Cargando…",
                                        font=ctk.CTkFont(size=11), text_color=MUTED)
        self.lbl_estado.grid(row=0, column=2, padx=20)

        self.tabs = ctk.CTkTabview(self, fg_color=BG_DEEP,
                                    segmented_button_fg_color=BG_CARD,
                                    segmented_button_selected_color=ACCENT,
                                    segmented_button_selected_hover_color="#D4B13C",
                                    segmented_button_unselected_color=BG_CARD,
                                    segmented_button_unselected_hover_color=BG_HOVER,
                                    text_color=TEXT_MAIN,
                                    text_color_disabled=MUTED)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 16))

        self.tabs.add("🔍  Búsqueda")
        self.tabs.add("📊  Frecuencias")
        self.tabs.add("📁  Estadísticas")

        self._tab_busqueda()
        self._tab_frecuencias()
        self._tab_estadisticas()

    def _tab_busqueda(self):
        tab = self.tabs.tab("🔍  Búsqueda")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        barra = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=10,
                              border_width=1, border_color=BORDER)
        barra.grid(row=0, column=0, sticky="ew", pady=(4, 6))
        barra.grid_columnconfigure(0, weight=1)

        input_row = ctk.CTkFrame(barra, fg_color="transparent")
        input_row.grid(row=0, column=0, sticky="ew", padx=14, pady=10)
        input_row.grid_columnconfigure(0, weight=1)

        self.entry_busqueda = ctk.CTkEntry(
            input_row, placeholder_text="🔍  Busca noticias por palabra(s)…",
            font=ctk.CTkFont(size=13), height=40,
            fg_color=BG_DEEP, border_color=BORDER,
            text_color=TEXT_MAIN, placeholder_text_color=MUTED,
        )
        self.entry_busqueda.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_busqueda.bind("<KeyRelease>", self._on_key)
        self.entry_busqueda.bind("<Return>", lambda e: self._buscar())

        self.btn_buscar = ctk.CTkButton(
            input_row, text="Buscar", width=100, height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT, text_color="#0D0F14",
            hover_color="#D4B13C", corner_radius=8,
            command=self._buscar,
        )
        self.btn_buscar.grid(row=0, column=1)

        self.lbl_sugerencias = ctk.CTkLabel(
            barra, text="", font=ctk.CTkFont(size=11, slant="italic"),
            text_color=ACCENT2, anchor="w",
        )
        self.lbl_sugerencias.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        self.lbl_resultados_hdr = ctk.CTkLabel(
            tab, text="Escribe algo para empezar…",
            font=ctk.CTkFont(size=11), text_color=MUTED, anchor="w",
        )
        self.lbl_resultados_hdr.grid(row=1, column=0, sticky="w", pady=(0, 4))

        self.scroll_resultados = ctk.CTkScrollableFrame(
            tab, fg_color=BG_DEEP, corner_radius=8,
        )
        self.scroll_resultados.grid(row=2, column=0, sticky="nsew")
        self.scroll_resultados.grid_columnconfigure(0, weight=1)

        self._placeholder_label = ctk.CTkLabel(
            self.scroll_resultados,
            text="Índice invertido O(1) · Trie para autocompletado O(m+k)",
            font=ctk.CTkFont(size=12), text_color=MUTED,
        )
        self._placeholder_label.grid(row=0, column=0, pady=40)

    def _tab_frecuencias(self):
        tab = self.tabs.tab("📊  Frecuencias")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=10,
                            border_width=1, border_color=BORDER)
        hdr.grid(row=0, column=0, sticky="ew", pady=(4, 8))
        ctk.CTkLabel(hdr, text="Frecuencias de palabras",
                     font=ctk.CTkFont("Georgia", 15, "bold"),
                     text_color=ACCENT).pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(hdr, text="HeapSort",
                     font=ctk.CTkFont("Courier New", 10),
                     text_color=MUTED).pack(side="left")

        self.scroll_heap = ctk.CTkScrollableFrame(tab, fg_color=BG_DEEP, corner_radius=8)
        self.scroll_heap.grid(row=1, column=0, sticky="nsew")
        self.scroll_heap.grid_columnconfigure(0, weight=1)

        self._heap_placeholder = ctk.CTkLabel(
            self.scroll_heap, text="Cargando datos…",
            font=ctk.CTkFont(size=12), text_color=MUTED,
        )
        self._heap_placeholder.grid(row=0, column=0, pady=40)

    def _tab_estadisticas(self):
        tab = self.tabs.tab("📁  Estadísticas")
        tab.grid_columnconfigure((0, 1, 2), weight=1)
        tab.grid_rowconfigure(1, weight=1)

        self.badge_articulos = EstadisticaBadge(tab, "—", "Artículos indexados")
        self.badge_articulos.grid(row=1, column=0, sticky="nsew", padx=(0, 6))

        self.badge_palabras = EstadisticaBadge(tab, "—", "Palabras únicas", color=ACCENT2)
        self.badge_palabras.grid(row=1, column=1, sticky="nsew", padx=6)

        self.badge_tokens = EstadisticaBadge(tab, "—", "Tokens totales", color=GREEN_OK)
        self.badge_tokens.grid(row=1, column=2, sticky="nsew", padx=(6, 0))

        # Tabla de fuentes
        self.frame_fuentes = ctk.CTkScrollableFrame(tab, fg_color=BG_CARD,
                                                      corner_radius=10,
                                                      border_width=1,
                                                      border_color=BORDER)
        self.frame_fuentes.grid(row=2, column=0, columnspan=3,
                                sticky="nsew", pady=(12, 0))
        tab.grid_rowconfigure(2, weight=1)
        self.frame_fuentes.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for col, texto in enumerate(["Fuente", "Artículos", "Palabras", "Estado"]):
            ctk.CTkLabel(self.frame_fuentes, text=texto,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=MUTED).grid(row=0, column=col, sticky="w",
                                                padx=14, pady=(10, 4))

    def _cargar_datos(self):
        self.analizador.cargar(usar_rss=True, usar_newsapi=True)
        self._cargando = False
        self.after(0, self._post_carga)

    def _post_carga(self):
        n = len(self.analizador.articulos)
        self.lbl_estado.configure(
            text=f"✅ {n:,} artículos listos",
            text_color=GREEN_OK,
        )
        self._actualizar_heap()
        self._actualizar_estadisticas()

    def _on_key(self, event):
        texto = self.entry_busqueda.get().strip()
        if self._cargando or not texto:
            self.lbl_sugerencias.configure(text="")
            return
        ultima = texto.split()[-1] if texto.split() else ""
        if len(ultima) >= 2:
            sugs = self.analizador.autocompletar(ultima)
            if sugs:
                self.lbl_sugerencias.configure(
                    text="💡 Sugerencias: " + "  ·  ".join(sugs)
                )
                return
        self.lbl_sugerencias.configure(text="")

    def _buscar(self):
        if self._cargando:
            return
        consulta = self.entry_busqueda.get().strip()
        if not consulta:
            return

        resultados = self.analizador.buscar(consulta)

        for w in self.scroll_resultados.winfo_children():
            w.destroy()

        n = len(resultados)
        color_n = GREEN_OK if n > 0 else RED_ERR
        self.lbl_resultados_hdr.configure(
            text=f"'{consulta}'  →  {n} artículo{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''}",
            text_color=color_n,
        )

        if not resultados:
            ctk.CTkLabel(
                self.scroll_resultados,
                text="Sin resultados para esa consulta.",
                font=ctk.CTkFont(size=12), text_color=MUTED,
            ).grid(row=0, column=0, pady=40)
            return

        for i, art in enumerate(resultados):
            tarjeta = TarjetaNoticia(self.scroll_resultados, art, i + 1)
            tarjeta.grid(row=i, column=0, sticky="ew", pady=(0, 8))

    def _actualizar_heap(self):
        for w in self.scroll_heap.winfo_children():
            w.destroy()

        frecuencias = self.analizador.indice.frecuencias
        filtradas = sorted(frecuencias.items(), key=lambda x: x[1], reverse=True)[:100]

        if not filtradas:
            ctk.CTkLabel(self.scroll_heap, text="Sin palabras disponibles.",
                         font=ctk.CTkFont(size=12), text_color=MUTED).grid(row=0, column=0, pady=40)
            return

        max_freq = filtradas[0][1]
        for i, (palabra, freq) in enumerate(filtradas):
            barra = BarraFrequencia(
                self.scroll_heap, rank=i + 1,
                palabra=palabra, freq=freq, max_freq=max_freq,
            )
            barra.grid(row=i, column=0, sticky="ew", padx=14,
                       pady=(10 if i == 0 else 4, 4))

    def _actualizar_estadisticas(self):
        total_tokens = sum(self.analizador.indice.frecuencias.values())
        n_arts = len(self.analizador.articulos)
        n_unicas = len(self.analizador.indice.tabla)

        self.badge_articulos.winfo_children()[0].configure(text=f"{n_arts:,}")
        self.badge_palabras.winfo_children()[0].configure(text=f"{n_unicas:,}")
        self.badge_tokens.winfo_children()[0].configure(text=f"{total_tokens:,}")

        for fila_idx, fuente in enumerate(self.analizador.fuentes_resumen, start=1):
            ok = fuente["status"] == "ok"
            color_estado = GREEN_OK if ok else RED_ERR
            datos = [
                fuente["fuente"],
                f"{fuente['articulos']:,}",
                f"{fuente['palabras']:,}",
                "✅ OK" if ok else "❌ Error",
            ]
            for col, val in enumerate(datos):
                ctk.CTkLabel(
                    self.frame_fuentes, text=val,
                    font=ctk.CTkFont(size=11),
                    text_color=color_estado if col == 3 else TEXT_MAIN,
                    anchor="w",
                ).grid(row=fila_idx, column=col, sticky="w",
                       padx=14, pady=4)


if __name__ == "__main__":
    app = AppAnalizador()
    app.mainloop()

