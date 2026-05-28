"""
Módulo de lógica de negocio para el Analizador de Noticias.
Incluye extracción de noticias desde RSS/NewsAPI, índice invertido,
Trie para autocompletado y algoritmos de ordenamiento (HeapSort).
"""

import re
import heapq
import feedparser
import requests

# Clave de API de NewsAPI (reemplazar por la propia si es necesario)
NEWSAPI_KEY = "57b8e2e64b8641aa94d770888ca8e3e4"

# Conjunto de palabras vacías (stopwords) en español
STOPWORDS = {
    "el","la","los","las","un","una","unos","unas","y","o","de","del","al",
    "en","con","por","para","que","se","su","sus","es","son","fue","han",
    "no","si","pero","mas","como","este","esta","esto","entre","sobre",
    "ante","tras","desde","hasta","hay","a","e","u","le","les","lo","me",
    "te","nos","ser","era","han","hoy","ayer","aun","muy","tan","ya",
}


def normalizar(texto: str) -> str:
    """
    Normaliza un texto: minúsculas, elimina acentos y caracteres no alfanuméricos.

    Args:
        texto (str): Texto de entrada.

    Returns:
        str: Texto normalizado (solo letras minúsculas, números y espacios).
    """
    texto = texto.lower()
    texto = texto.translate(str.maketrans("áéíóúüñ", "aeiouun"))
    return re.sub(r"[^a-z0-9\s]", "", texto)


def tokenizar(texto: str) -> list:
    """
    Divide el texto en tokens (palabras) aplicando stopwords y longitud mínima.

    Args:
        texto (str): Texto a tokenizar.

    Returns:
        list: Lista de tokens válidos.
    """
    return [p for p in normalizar(texto).split() if p not in STOPWORDS and len(p) > 2]


class IndiceInvertido:
    """
    Estructura de datos para indexar documentos por palabras.
    Permite búsquedas booleanas (conjunción de términos).
    """

    def __init__(self):
        self.tabla: dict = {}   # palabra -> set(ids_articulos)
        self.frecuencias: dict = {}  # palabra -> frecuencia total

    def insertar(self, id_art: int, texto: str):
        """
        Indexa un artículo extrayendo sus tokens.

        Args:
            id_art (int): Identificador único del artículo.
            texto (str): Texto completo del artículo (título + resumen).
        """
        for palabra in tokenizar(texto):
            if palabra not in self.tabla:
                self.tabla[palabra] = set()
            self.tabla[palabra].add(id_art)
            self.frecuencias[palabra] = self.frecuencias.get(palabra, 0) + 1

    def buscar(self, palabra: str) -> set:
        """
        Devuelve los ids de los artículos que contienen una palabra exacta.

        Args:
            palabra (str): Palabra a buscar.

        Returns:
            set: Conjunto de ids de artículos.
        """
        return self.tabla.get(normalizar(palabra), set())

    def buscar_multiple(self, palabras: list) -> set:
        """
        Realiza una consulta de conjunción (AND) sobre varias palabras.

        Args:
            palabras (list): Lista de palabras a buscar.

        Returns:
            set: Intersección de los ids de artículos que contienen todas las palabras.
        """
        if not palabras:
            return set()
        resultado = self.buscar(palabras[0])
        for p in palabras[1:]:
            resultado &= self.buscar(p)
        return resultado


class NodoTrie:
    """Nodo del Trie para autocompletado eficiente."""

    def __init__(self):
        self.hijos: dict = {}   # caracter -> NodoTrie
        self.es_fin: bool = False   # indica si el nodo representa el final de una palabra
        self.frecuencia: int = 0    # frecuencia de la palabra (para ordenar sugerencias)


class Trie:
    """Estructura Trie que soporta inserción y autocompletado por prefijo."""

    def __init__(self):
        self.raiz = NodoTrie()

    def insertar(self, palabra: str, freq: int = 1):
        """
        Inserta una palabra en el Trie junto con su frecuencia.

        Args:
            palabra (str): Palabra a insertar.
            freq (int): Frecuencia de la palabra (para ordenar sugerencias).
        """
        nodo = self.raiz
        for c in palabra:
            if c not in nodo.hijos:
                nodo.hijos[c] = NodoTrie()
            nodo = nodo.hijos[c]
        nodo.es_fin = True
        nodo.frecuencia = freq

    def _recolectar(self, nodo, prefijo, res):
        """
        Recorre recursivamente el Trie para recolectar todas las palabras que
        cuelgan de un nodo dado.

        Args:
            nodo (NodoTrie): Nodo actual.
            prefijo (str): Prefijo acumulado.
            res (list): Lista donde se guardan los pares (frecuencia, palabra).
        """
        if nodo.es_fin:
            res.append((nodo.frecuencia, prefijo))
        for c, hijo in nodo.hijos.items():
            self._recolectar(hijo, prefijo + c, res)

    def autocompletar(self, prefijo: str, limite: int = 6) -> list:
        """
        Devuelve sugerencias de palabras que comienzan con el prefijo dado,
        ordenadas por frecuencia descendente.

        Args:
            prefijo (str): Prefijo a completar.
            limite (int): Número máximo de sugerencias.

        Returns:
            list: Lista de palabras sugeridas.
        """
        prefijo = normalizar(prefijo)
        nodo = self.raiz
        for c in prefijo:
            if c not in nodo.hijos:
                return []
            nodo = nodo.hijos[c]
        res = []
        self._recolectar(nodo, prefijo, res)
        res.sort(reverse=True)   # ordena por frecuencia descendente
        return [p for _, p in res[:limite]]


def top_palabras(frecuencias: dict, n: int = 10) -> list:
    """
    Obtiene las n palabras más frecuentes usando un heap (HeapSort parcial).

    Args:
        frecuencias (dict): Diccionario palabra -> frecuencia.
        n (int): Número de palabras a retornar.

    Returns:
        list: Lista de tuplas (palabra, frecuencia) ordenadas de mayor a menor.
    """
    heap = []
    for palabra, freq in frecuencias.items():
        if len(heap) < n:
            heapq.heappush(heap, (freq, palabra))
        elif freq > heap[0][0]:
            heapq.heapreplace(heap, (freq, palabra))
    return [(p, f) for f, p in sorted(heap, reverse=True)]


# Fuentes RSS configuradas
FEEDS_RSS = {
    "El Financiero": "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml",
    "Expansión":     "https://expansion.mx/rss",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def obtener_noticias_rss() -> tuple:
    """
    Extrae noticias desde las fuentes RSS configuradas.

    Returns:
        tuple: (lista_articulos, lista_resumen_fuentes)
            - articulos: lista de diccionarios con claves: titulo, resumen, fuente, link, texto
            - resumen_fuentes: lista de diccionarios con estadísticas por fuente
    """
    articulos = []
    resumen_fuentes = []

    for fuente, url in FEEDS_RSS.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            count = 0
            palabras_fuente = 0
            for entry in feed.entries:
                titulo = entry.get("title", "").strip()
                resumen = re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip()
                link = entry.get("link", "")
                if titulo:
                    texto = titulo + " " + resumen
                    articulos.append({
                        "titulo": titulo,
                        "resumen": resumen,
                        "fuente": fuente,
                        "link": link,
                        "texto": texto,
                    })
                    palabras_fuente += len(texto.split())
                    count += 1
            resumen_fuentes.append({
                "fuente": fuente, "articulos": count,
                "palabras": palabras_fuente, "status": "ok",
            })
        except Exception:
            resumen_fuentes.append({
                "fuente": fuente, "articulos": 0,
                "palabras": 0, "status": "error",
            })

    return articulos, resumen_fuentes


def obtener_noticias_newsapi() -> tuple:
    """
    Extrae noticias desde la API de NewsAPI (temas relacionados con México).

    Returns:
        tuple: (lista_articulos, lista_resumen_fuente)
            - articulos: lista de diccionarios (mismo formato que RSS)
            - resumen_fuente: lista con un único diccionario de estadísticas para NewsAPI
    """
    if not NEWSAPI_KEY:
        return [], []

    TEMAS = ["México economía", "México política", "México noticias"]
    todos = []

    try:
        for tema in TEMAS:
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": tema,
                    "language": "es",
                    "sortBy": "publishedAt",
                    "pageSize": 30,
                    "apiKey": NEWSAPI_KEY,
                },
                timeout=10,
            )
            data = r.json()
            if data.get("status") != "ok":
                continue
            todos += data.get("articles", [])

        vistos = set()
        articulos = []
        palabras_total = 0
        for art in todos:
            titulo = (art.get("title") or "").strip()
            resumen = (art.get("description") or "").strip()
            link = (art.get("url") or "")
            fuente = art.get("source", {}).get("name", "NewsAPI")
            if not titulo or titulo == "[Removed]" or titulo in vistos:
                continue
            vistos.add(titulo)
            texto = titulo + " " + resumen
            articulos.append({
                "titulo": titulo,
                "resumen": resumen,
                "fuente": fuente,
                "link": link,
                "texto": texto,
            })
            palabras_total += len(texto.split())

        resumen = [{
            "fuente": "NewsAPI (es)",
            "articulos": len(articulos),
            "palabras": palabras_total,
            "status": "ok",
        }]
        return articulos, resumen

    except Exception:
        return [], [{"fuente": "NewsAPI", "articulos": 0, "palabras": 0, "status": "error"}]


def obtener_noticias_simuladas() -> tuple:
    """
    Proporciona un conjunto de noticias de respaldo (simuladas) en caso de que
    las fuentes externas fallen o no devuelvan datos.

    Returns:
        tuple: (lista_articulos_simulados, lista_resumen_fuente)
    """
    articulos = [
        {"titulo":"CDMX implementa nuevo sistema de transporte eléctrico","resumen":"El gobierno de la Ciudad de México anunció la expansión del sistema de trolebuses eléctricos en las principales avenidas.","fuente":"El Universal","link":"https://ejemplo.com/1","texto":"CDMX implementa nuevo sistema transporte eléctrico gobierno Ciudad México expansión trolebuses eléctricos avenidas."},
        {"titulo":"Elecciones: resultados finales en estados del norte","resumen":"El INE publicó los resultados definitivos en Nuevo León, Tamaulipas y Chihuahua con alta participación ciudadana.","fuente":"Milenio","link":"https://ejemplo.com/2","texto":"Elecciones resultados finales estados norte INE Nuevo León Tamaulipas Chihuahua participación ciudadana."},
        {"titulo":"Economía mexicana crece en el segundo trimestre","resumen":"El INEGI reportó crecimiento del PIB impulsado por el sector manufacturero y exportaciones al mercado estadounidense.","fuente":"Infobae México","link":"https://ejemplo.com/3","texto":"Economía mexicana crece segundo trimestre INEGI PIB sector manufacturero exportaciones mercado estadounidense."},
        {"titulo":"Liga MX: América gana el Clásico Nacional","resumen":"Las Águilas del América vencieron en el Estadio Azteca ante una gran asistencia de aficionados.","fuente":"Milenio","link":"https://ejemplo.com/4","texto":"Liga MX América golea Guadalajara Clásico Nacional Águilas Chivas Estadio Azteca aficionados."},
        {"titulo":"UNAM lanza programa de becas para estudiantes","resumen":"La Universidad Nacional Autónoma de México abrió convocatoria para becas de nivel licenciatura.","fuente":"El Universal","link":"https://ejemplo.com/5","texto":"UNAM programa becas estudiantes bajos recursos Universidad Nacional México convocatoria licenciatura."},
        {"titulo":"Sequía afecta cultivos en el norte de México","resumen":"Productores de Sonora, Sinaloa y Chihuahua reportan afectaciones por la falta de lluvias constantes.","fuente":"La Jornada","link":"https://ejemplo.com/6","texto":"Sequía afecta cultivos norte México Sonora Sinaloa Chihuahua pérdidas lluvias presas."},
        {"titulo":"Pemex anuncia inversión en refinería","resumen":"La empresa estatal informó una inversión adicional para aumentar la capacidad de refinación en el sureste.","fuente":"Infobae México","link":"https://ejemplo.com/7","texto":"Pemex inversión refinería Dos Bocas empresa estatal capacidad refinación Tabasco."},
        {"titulo":"Tasa de desempleo en México muestra disminuciones","resumen":"El INEGI informó que la desocupación disminuyó con la generación de plazas en el sector de servicios.","fuente":"El Universal","link":"https://ejemplo.com/8","texto":"Tasa desempleo México agosto INEGI desocupación empleos formales servicios economía."},
        {"titulo":"Selección mexicana asegura puesto en el Mundial","resumen":"El equipo nacional aseguró su clasificación tras el último encuentro disputado en el Estadio Azteca.","fuente":"Milenio","link":"https://ejemplo.com/9","texto":"Selección mexicana clasifica Mundial 2026 Tri victoria Honduras Estadio Azteca fútbol."},
        {"titulo":"Gobierno presenta plan de salud mental para jóvenes","resumen":"La Secretaría de Salud implementó un programa estratégico orientado a la atención de los adolescentes.","fuente":"La Jornada","link":"https://ejemplo.com/10","texto":"Gobierno plan nacional salud mental jóvenes Secretaría programa crisis adolescentes universitarios."},
    ]
    fuentes = [{"fuente": "Datos de respaldo", "articulos": len(articulos), "palabras": sum(len(a["texto"].split()) for a in articulos), "status": "ok"}]
    return articulos, fuentes


class AnalizadorNoticias:
    """
    Clase principal que orquesta la carga de noticias, la indexación y las consultas.
    """

    def __init__(self):
        self.articulos: list = []           # Lista de diccionarios de artículos
        self.fuentes_resumen: list = []     # Resumen por fuente
        self.indice = IndiceInvertido()     # Índice invertido
        self.trie = Trie()                  # Trie para autocompletado

    def cargar(self, usar_rss: bool = True, usar_newsapi: bool = True):
        """
        Carga noticias desde las fuentes especificadas (RSS, NewsAPI) y construye
        las estructuras de datos (índice invertido y Trie).

        Args:
            usar_rss (bool): Si se deben consultar los feeds RSS.
            usar_newsapi (bool): Si se debe consultar NewsAPI.
        """
        todos_articulos = []
        todos_resumen = []

        if usar_rss:
            arts, res = obtener_noticias_rss()
            todos_articulos += arts
            todos_resumen += res

        if usar_newsapi:
            arts, res = obtener_noticias_newsapi()
            todos_articulos += arts
            todos_resumen += res

        # Si no se obtuvo nada, usar datos simulados de respaldo
        if not todos_articulos:
            todos_articulos, todos_resumen = obtener_noticias_simuladas()

        self.articulos = todos_articulos
        self.fuentes_resumen = todos_resumen

        # Indexar cada artículo
        for i, art in enumerate(self.articulos):
            self.indice.insertar(i, art["texto"])

        # Insertar palabras en el Trie con sus frecuencias
        for palabra, freq in self.indice.frecuencias.items():
            self.trie.insertar(palabra, freq)

    def buscar(self, consulta: str) -> list:
        """
        Busca artículos que contengan todas las palabras de la consulta.

        Args:
            consulta (str): Texto de búsqueda (puede contener múltiples palabras).

        Returns:
            list: Lista de diccionarios de artículos que coinciden.
        """
        ids = self.indice.buscar_multiple(tokenizar(consulta))
        return [self.articulos[i] for i in sorted(ids)]

    def autocompletar(self, prefijo: str) -> list:
        """
        Obtiene sugerencias de palabras a partir de un prefijo.

        Args:
            prefijo (str): Prefijo para autocompletar.

        Returns:
            list: Lista de palabras sugeridas.
        """
        return self.trie.autocompletar(prefijo)

    def top_palabras(self, n: int = 10) -> list:
        """
        Devuelve las n palabras más frecuentes.

        Args:
            n (int): Número de palabras a retornar.

        Returns:
            list: Lista de tuplas (palabra, frecuencia).
        """
        return top_palabras(self.indice.frecuencias, n)