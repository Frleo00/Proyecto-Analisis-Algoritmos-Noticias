import re
import heapq
import feedparser
import requests

NEWSAPI_KEY = "57b8e2e64b8641aa94d770888ca8e3e4" 
STOPWORDS = {
    "el","la","los","las","un","una","unos","unas","y","o","de","del","al",
    "en","con","por","para","que","se","su","sus","es","son","fue","han",
    "no","si","pero","mas","como","este","esta","esto","entre","sobre",
    "ante","tras","desde","hasta","hay","a","e","u","le","les","lo","me",
    "te","nos","ser","era","han","hoy","ayer","aun","muy","tan","ya",
}

def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = texto.translate(str.maketrans("áéíóúüñ", "aeiouun"))
    return re.sub(r"[^a-z0-9\s]", "", texto)

def tokenizar(texto: str) -> list:
    return [p for p in normalizar(texto).split() if p not in STOPWORDS and len(p) > 2]

class IndiceInvertido:
    def __init__(self):
        self.tabla: dict = {}
        self.frecuencias: dict = {}

    def insertar(self, id_art: int, texto: str):
        for palabra in tokenizar(texto):
            if palabra not in self.tabla:
                self.tabla[palabra] = set()
            self.tabla[palabra].add(id_art)
            self.frecuencias[palabra] = self.frecuencias.get(palabra, 0) + 1

    def buscar(self, palabra: str) -> set:
        return self.tabla.get(normalizar(palabra), set())

    def buscar_multiple(self, palabras: list) -> set:
        if not palabras:
            return set()
        resultado = self.buscar(palabras[0])
        for p in palabras[1:]:
            resultado &= self.buscar(p)
        return resultado

class NodoTrie:
    def __init__(self):
        self.hijos: dict = {}
        self.es_fin: bool = False
        self.frecuencia: int = 0

class Trie:
    def __init__(self):
        self.raiz = NodoTrie()

    def insertar(self, palabra: str, freq: int = 1):
        nodo = self.raiz
        for c in palabra:
            if c not in nodo.hijos:
                nodo.hijos[c] = NodoTrie()
            nodo = nodo.hijos[c]
        nodo.es_fin = True
        nodo.frecuencia = freq

    def _recolectar(self, nodo, prefijo, res):
        if nodo.es_fin:
            res.append((nodo.frecuencia, prefijo))
        for c, hijo in nodo.hijos.items():
            self._recolectar(hijo, prefijo + c, res)

    def autocompletar(self, prefijo: str, limite: int = 6) -> list:
        prefijo = normalizar(prefijo)
        nodo = self.raiz
        for c in prefijo:
            if c not in nodo.hijos:
                return []
            nodo = nodo.hijos[c]
        res = []
        self._recolectar(nodo, prefijo, res)
        res.sort(reverse=True)
        return [p for _, p in res[:limite]]

def top_palabras(frecuencias: dict, n: int = 10) -> list:
    heap = []
    for palabra, freq in frecuencias.items():
        if len(heap) < n:
            heapq.heappush(heap, (freq, palabra))
        elif freq > heap[0][0]:
            heapq.heapreplace(heap, (freq, palabra))
    return [(p, f) for f, p in sorted(heap, reverse=True)]

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
                titulo  = entry.get("title", "").strip()
                resumen = re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip()
                link    = entry.get("link", "")
                if titulo:
                    texto = titulo + " " + resumen
                    articulos.append({
                        "titulo":  titulo,
                        "resumen": resumen,
                        "fuente":  fuente,
                        "link":    link,
                        "texto":   texto,
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
    if not NEWSAPI_KEY:
        return [], []

    TEMAS = ["México economía", "México política", "México noticias"]
    todos = []

    try:
        for tema in TEMAS:
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        tema,
                    "language": "es",
                    "sortBy":   "publishedAt",
                    "pageSize": 30,
                    "apiKey":   NEWSAPI_KEY,
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
            titulo  = (art.get("title")       or "").strip()
            resumen = (art.get("description") or "").strip()
            link    = (art.get("url")         or "")
            fuente  = art.get("source", {}).get("name", "NewsAPI")
            if not titulo or titulo == "[Removed]" or titulo in vistos:
                continue
            vistos.add(titulo)
            texto = titulo + " " + resumen
            articulos.append({
                "titulo":  titulo,
                "resumen": resumen,
                "fuente":  fuente,
                "link":    link,
                "texto":   texto,
            })
            palabras_total += len(texto.split())

        resumen = [{
            "fuente":    "NewsAPI (es)",
            "articulos": len(articulos),
            "palabras":  palabras_total,
            "status":    "ok",
        }]
        return articulos, resumen

    except Exception:
        return [], [{"fuente": "NewsAPI", "articulos": 0, "palabras": 0, "status": "error"}]

def obtener_noticias_simuladas() -> tuple:
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
    def __init__(self):
        self.articulos: list = []
        self.fuentes_resumen: list = []
        self.indice = IndiceInvertido()
        self.trie = Trie()

    def cargar(self, usar_rss: bool = True, usar_newsapi: bool = True):
        todos_articulos = []
        todos_resumen   = []

        if usar_rss:
            arts, res = obtener_noticias_rss()
            todos_articulos += arts
            todos_resumen   += res

        if usar_newsapi:
            arts, res = obtener_noticias_newsapi()
            todos_articulos += arts
            todos_resumen   += res

        if not todos_articulos:
            todos_articulos, todos_resumen = obtener_noticias_simuladas()

        self.articulos       = todos_articulos
        self.fuentes_resumen = todos_resumen

        for i, art in enumerate(self.articulos):
            self.indice.insertar(i, art["texto"])
        for palabra, freq in self.indice.frecuencias.items():
            self.trie.insertar(palabra, freq)

    def buscar(self, consulta: str) -> list:
        ids = self.indice.buscar_multiple(tokenizar(consulta))
        return [self.articulos[i] for i in sorted(ids)]

    def autocompletar(self, prefijo: str) -> list:
        return self.trie.autocompletar(prefijo)

    def top_palabras(self, n: int = 10) -> list:
        return top_palabras(self.indice.frecuencias, n)