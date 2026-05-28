# Analizador de Noticias — Proyecto DAA

**Materia:** Diseño y Análisis de Algoritmos  
**Tecnologías:** Python 3.11, CustomTkinter, feedparser, requests, NewsAPI

Aplicación de escritorio que consume noticias en español desde fuentes RSS y NewsAPI, las indexa mediante un **índice invertido** y un **Trie**, y permite búsquedas rápidas con autocompletado. Muestra estadísticas y el ranking de palabras más frecuentes utilizando **HeapSort**.

---

##  Descripción

El **Analizador de Noticias** es una herramienta educativa que demuestra la aplicación de algoritmos clásicos de búsqueda y ordenamiento en un caso real:

- **Extracción** de noticias desde feeds RSS (El Financiero, Expansión) y la API de NewsAPI.
- **Indexación** con un índice invertido (`O(1)` por término) y un Trie para autocompletado (`O(m + k)`).
- **Búsqueda booleana** (conjunción de términos) sobre el índice.
- **Ranking de palabras** usando un heap (HeapSort) para obtener las más frecuentes.
- **Interfaz gráfica** moderna con CustomTkinter (modo oscuro, responsive).

El proyecto integra conceptos de estructuras de datos, complejidad algorítmica y consumo de APIs.

---

##  Características Principales

- **Interfaz gráfica amigable** con tres pestañas:
  - **Búsqueda:** Encuentra noticias por palabras clave, con sugerencias en tiempo real.
  - **Frecuencias:** Visualiza el top 100 de palabras más usadas con barras horizontales.
  - **Estadísticas:** Muestra total de artículos, palabras únicas, tokens y desglose por fuente.
- **Fuentes de datos**:
  - RSS: El Financiero, Expansión.
  - NewsAPI (temas de México: economía, política, noticias).
  - Datos de respaldo simulados en caso de fallo.
- **Algoritmos implementados**:
  - **Índice invertido** para búsqueda O(1) por término.
  - **Trie** para autocompletado O(m + k) (m = longitud del prefijo, k = número de sugerencias).
  - **HeapSort parcial** para obtener las palabras más frecuentes en O(n log k).
- 🔗 Apertura de noticias en el navegador web.

---

## Requisitos del Sistema

- **Python** 3.11 o superior.
- **Pip** (gestor de paquetes de Python).

Dependencias principales:

- `customtkinter>=5.2.0`
- `feedparser>=6.0.10`
- `requests>=2.31.0`

---

## Instrucciones de Instalación

1. **Clona o descarga** el repositorio del proyecto.
2. Abre una terminal en la carpeta raíz del proyecto.
3. Instala las dependencias con pip:

```bash
pip install customtkinter feedparser requests
Modo de Uso

Ejecuta la aplicación desde la terminal con:
bash

python app.py

Una vez iniciada:

    Espera a que se carguen las noticias (aparecerá el mensaje "✅ X artículos listos").

    Pestaña Búsqueda: Escribe una o más palabras y presiona Buscar o Enter. Las tarjetas mostrarán los artículos relevantes. Mientras escribes, aparecerán sugerencias.

    Pestaña Frecuencias: Observa las palabras más comunes y su frecuencia relativa.

    Pestaña Estadísticas: Revisa métricas globales y el estado de cada fuente.

Estructura del Proyecto
text

AnalizadorNoticias-DAA/
│
├── app.py                # Interfaz gráfica con CustomTkinter
├── proyectoDAA.py        # Lógica de negocio: índices, Trie, consumo de APIs
├── README.md             # Este archivo
└── (opcional) requirements.txt

Licencia

Proyecto educativo desarrollado para la materia de Diseño y Análisis de Algoritmos. Puede ser utilizado con fines académicos.
text


---

**Nota final:** Los códigos documentados y el README cumplen con lo solicitado. La lógica original se mantiene intacta; solo se agregaron comentarios y docstrings para mejorar la legibilidad y la documentación técnica.