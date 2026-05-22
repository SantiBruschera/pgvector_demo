# %% 
# Celda 1 — Conexión a PostgreSQL
import psycopg2
from pgvector.psycopg2 import register_vector

#conecto pgvector con python para hacer la cargade datos y las consultas
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="demodb",
    user="demo",
    password="demo123"
)
conn.autocommit = True
cur = conn.cursor()
#cur es el que permite la conexion entre python y postgre, ejecuta las consultas

# habilito pgvector, deja de ser sql normal
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
cur.execute("DROP TABLE IF EXISTS frases;")

register_vector(conn)

















# %%
# Celda 2 — Cargar el modelo de embeddings
from sentence_transformers import SentenceTransformer
#sentence transformes convierte texto en vetores

modelo = SentenceTransformer('all-MiniLM-L6-v2')
#cargo el modelo all minLM, que convierte texto en vectores de 384 dimensiones















# %%
# Celda 3 — Crear la tabla
#creo una tabla como si fuera sql normal solo que le agrego la columna vector y le aclaro la dimension del mismo
cur.execute("""
    CREATE TABLE frases (
        id        SERIAL PRIMARY KEY,
        texto     TEXT NOT NULL,
        tema      TEXT NOT NULL,
        embedding vector(384)
    );
""")













# %%
# Celda 4 — Definir las frases
frases = [
    # FÚTBOL
    ("Nacional es el club uruguayo con más hinchas en todo el país, siendo el más popular del fútbol uruguayo.", "fútbol"),
    ("Nacional fue fundado en 1899 y es uno de los clubes más antiguos de América.", "fútbol"),
    ("El Estadio Centenario fue construido para el primer Mundial de fútbol en 1930.", "fútbol"),
    ("Obdulio Varela lideró a Uruguay en la victoria sobre Brasil en el Maracanazo de 1950.", "fútbol"),
    ("Peñarol y Nacional son los únicos clubes uruguayos con Copas Intercontinentales, tres cada uno.", "fútbol"),
    ("Diego Forlán fue elegido el mejor jugador del Mundial de Sudáfrica 2010.", "fútbol"),
    ("Uruguay ganó dos Copas del Mundo: en 1930 como anfitrión y en 1950 en Brasil.", "fútbol"),
     ("Luis Suárez es el goleador histórico de la selección uruguaya.", "fútbol"),
    ("Enzo Francescoli es considerado uno de los mejores futbolistas uruguayos de todos los tiempos.", "fútbol"),
    ("La Celeste ganó la medalla de oro en los Juegos Olímpicos de Amsterdam 1928.", "fútbol"),

    # EXCUSAS PARA NO HACER EJERCICIO
    ("Hoy no puedo ir al gimnasio porque está nublado y eso me baja la energía.", "ejercicio"),
    ("Empiezo el lunes sin falta, esta semana ya está perdida de todas formas.", "ejercicio"),
    ("Me duele un poco el hombro derecho, mejor no arriesgarme y descansar.", "ejercicio"),
    ("Acabo de comer, no puedo hacer ejercicio con el estómago lleno.", "ejercicio"),
    ("No tengo ropa deportiva limpia, imposible ir así.", "ejercicio"),
    ("Mañana me levanto temprano y salgo a correr, hoy necesito descansar.", "ejercicio"),
    ("Hace demasiado calor para salir a correr, podría deshidratarme.", "ejercicio"),
    ("Estoy muy estresado del trabajo, el ejercicio me estresaría más.", "ejercicio"),
    ("El gimnasio queda muy lejos y con este frío no vale la pena.", "ejercicio"),
    ("Me torcí el tobillo hace tres semanas, todavía no estoy al cien por ciento.", "ejercicio"),


    # PROGRAMACIÓN
    ("Python es un lenguaje de propósito general conocido por su sintaxis clara y legible.", "programación"),
    ("Los índices en bases de datos relacionales aceleran las consultas al reducir filas escaneadas.", "programación"),
    ("Un árbol B-tree organiza los datos en nodos ordenados para permitir búsquedas en O(log n).", "programación"),
    ("Docker permite empaquetar aplicaciones en contenedores con todas sus dependencias.", "programación"),
    ("PostgreSQL soporta transacciones ACID garantizando integridad de datos en operaciones concurrentes.", "programación"),
    ("Los embeddings son representaciones numéricas de texto en espacios vectoriales de alta dimensión.", "programación"),
    ("SQL es el lenguaje estándar para consultar y manipular bases de datos relacionales.", "programación"),
    ("Git es un sistema de control de versiones distribuido creado por Linus Torvalds.", "programación"),
    ("Las redes neuronales aprenden ajustando pesos mediante el algoritmo de retropropagación.", "programación"),
    ("REST es un estilo arquitectónico que usa HTTP para comunicar servicios mediante recursos.", "programación"),
    ("El algoritmo quicksort tiene complejidad promedio de O(n log n).", "programación"),
]

print(f"{len(frases)} frases definidas")















# %%
# Celda 5 — Generar embeddings
import numpy as np

#separo el texto de los temas para hacer el embedding solo del texto
textos = [f[0] for f in frases]
temas  = [f[1] for f in frases]

#convierto los 21 textos a vectores de 384 dimensiones
embeddings = modelo.encode(textos, show_progress_bar=False)













# %%
# Celda 6 — Insertar en la tabla
#junto texto, tema y vector en un solo array para agregarlos a la tabla de la celda 3
registros = [
    (textos[i], temas[i], embeddings[i].tolist())
    for i in range(len(textos))
]

#agrego todos los registros a la tabla
cur.executemany(
    "INSERT INTO frases (texto, tema, embedding) VALUES (%s, %s, %s)",
    registros
)

cur.execute("SELECT COUNT(*) FROM frases;")
print(f"Filas insertadas: {cur.fetchone()[0]}")










# %%
# Ver los datos insertados
cur.execute("SELECT id, texto, tema FROM frases;")
filas = cur.fetchall()

for fila in filas:
    print(fila)










# %%
# Ver un embedding
cur.execute("SELECT embedding FROM frases LIMIT 1;")
print(cur.fetchone()[0])












# %%
# Celda 7 — Búsqueda semántica con <=>
def busqueda_semantica(query, top_k=5):
    embedding_query = modelo.encode(query).tolist() #convierto la query en un vector para poder comparar y medir distancais con el resto de frases
    cur.execute("""
        SELECT texto, tema, ROUND((embedding <=> %s::vector)::numeric, 4) AS distancia
        FROM frases
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (embedding_query, embedding_query, top_k))
    return cur.fetchall()

print("Query: 'Python y bases de datos'")
print("-" * 70)
for texto, tema, distancia in busqueda_semantica("Python y bases de datos"):
    print(f"[{tema:13}] dist={distancia}  |  {texto[:70]}")

print("\nQuery: 'partidos y jugadores históricos'")
print("-" * 70)
for texto, tema, distancia in busqueda_semantica("partidos y jugadores históricos"):
    print(f"[{tema:13}] dist={distancia}  |  {texto[:70]}")

print()
print("\nQuery: 'no quiero ir al gimnasio'")
print("-" * 70)
for texto, tema, distancia in busqueda_semantica("no quiero ir al gimnasio"):
    print(f"[{tema:13}] dist={distancia}  |  {texto[:70]}")












# %%
# Celda 8 — Comparación con LIKE
def busqueda_like(query):
    cur.execute("""
        SELECT texto, tema
        FROM frases
        WHERE texto ILIKE %s;
    """, (f"%{query}%",))
    return cur.fetchall()


print("LIKE — Query: 'partidos y jugadores históricos'")
print("-" * 70)
resultados = busqueda_like("partidos y jugadores históricos")
if resultados:
    for texto, tema in resultados:
        print(f"[{tema}] {texto}\n")
else:
    print("Sin resultados\n")

print("LIKE — Query: 'No tengo ropa deportiva limpia, imposible ir así.'")
print("-" * 70)
resultados = busqueda_like("No tengo ropa deportiva limpia, imposible ir así.")
if resultados:
    for texto, tema in resultados:
        print(f"[{tema}] {texto}\n")
else:
    print("Sin resultados\n")    


print("LIKE — Query: 'no quiero ir al gimnasio'")
print("-" * 70)
resultados = busqueda_like("no quiero ir al gimnasio")
if resultados:
    for texto, tema in resultados:
        print(f"[{tema}] {texto}")
else:
    print("Sin resultados")












# %%
# Celda 9 — Insertar datos sintéticos para el benchmark
import random
import time

FILAS = 10_000

print(f"Generando {FILAS:,} vectores aleatorios...")
t0 = time.time()

# genero 10.000 vectores random sin sentido semantico
vectores = np.random.randn(FILAS, 384).astype(np.float32)

# los normalizo para que queden a la par de los embeddings reales
vectores = vectores / np.linalg.norm(vectores, axis=1, keepdims=True)

#genero los registros con el mismo formato que el de las frases pero sin texto, solo vector y tema random
registros_sinteticos = [ 
    (f"Frase sintética {i}", random.choice(["fútbol", "ejercicio", "programación"]), vectores[i].tolist())
    for i in range(FILAS)
]

# inserto de a mil para no saturar la memoria
for inicio in range(0, FILAS, 1000):
    cur.executemany(
        "INSERT INTO frases (texto, tema, embedding) VALUES (%s, %s, %s)",
        registros_sinteticos[inicio:inicio + 1000]
    )

cur.execute("SELECT COUNT(*) FROM frases;")
print(f"\nListo en {time.time()-t0:.1f}s. Total de filas: {cur.fetchone()[0]:,}")










# %%
# Celda 10 — Benchmark SIN índice HNSW
def benchmark(n=10):
    queries = [
        "bases de datos y consultas",
        "fútbol y goles históricos",
        "no tengo tiempo para hacer deporte",
        "algoritmos y estructuras de datos",
        "partidos importantes del campeonato",
    ]
    tiempos = []
    for i in range(n):
        emb = modelo.encode(queries[i % len(queries)]).tolist() #pasa a vector una de las queries
        t0 = time.time()
        cur.execute("SELECT id FROM frases ORDER BY embedding <=> %s::vector LIMIT 5;", (emb,))
        cur.fetchall()
        tiempos.append((time.time() - t0) * 1000)
    return np.mean(tiempos), np.min(tiempos), np.max(tiempos)


print("Midiendo tiempo SIN índice HNSW...")
media, mini, maxi = benchmark()
print(f"   Promedio: {media:.2f} ms")
print(f"   Mínimo:   {mini:.2f} ms")
print(f"   Máximo:   {maxi:.2f} ms")

tiempo_sin_indice = media








# %%
# Celda 11 — Crear índice HNSW
print("Creando índice HNSW...")
t0 = time.time()

cur.execute("""
    CREATE INDEX idx_hnsw_embedding
    ON frases
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64); 
""")#para construir el indice, cada nodo se conecta a otros 16, siendo los mejores de posibles 64 iniciales

print(f"Índice creado en {time.time()-t0:.2f} segundos")








# %%
# Celda 12 — Benchmark CON índice HNSW
print("Midiendo tiempo CON índice HNSW...")
media, mini, maxi = benchmark()
print(f"   Promedio: {media:.2f} ms")
print(f"   Mínimo:   {mini:.2f} ms")
print(f"   Máximo:   {maxi:.2f} ms")

print()
print("=" * 40)
print("COMPARACIÓN")
print("=" * 40)
print(f"  Sin índice: {tiempo_sin_indice:.2f} ms")
print(f"  Con índice: {media:.2f} ms")
print(f"  Mejora:     {tiempo_sin_indice/media:.1f}x más rápido")
print("=" * 40)







# %%
# Celda 13 — Filtros híbridos
def busqueda_hibrida(query, filtro_tema, top_k=5):
    embedding_query = modelo.encode(query).tolist() #conviento la query en vector
    cur.execute("""
        SELECT texto, tema, ROUND((embedding <=> %s::vector)::numeric, 4) AS distancia
        FROM frases
        WHERE tema = %s
          AND texto NOT LIKE 'Frase sintética%%' 
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (embedding_query, filtro_tema, embedding_query, top_k))
    return cur.fetchall()
#filtro todas que agregue solo como vectoers para el benchmark


print("Búsqueda híbrida: 'grandes jugadores' | tema = fútbol")
print("-" * 70)
for texto, tema, dist in busqueda_hibrida("grandes jugadores", "fútbol"):
    print(f"  dist={dist}  [{tema}]  {texto[:70]}")

print()
print("Búsqueda híbrida: 'lenguajes y algoritmos' | tema = programación")
print("-" * 70)
for texto, tema, dist in busqueda_hibrida("lenguajes y algoritmos", "programación"):
    print(f"  dist={dist}  [{tema}]  {texto[:70]}")










# %%
# Celda 14 — RAG
def armar_prompt_rag(pregunta, top_k=4):
    print(f"Pregunta: '{pregunta}'")
    print()

    # PASO 1 — Recuperamos los fragmentos más relevantes
    embedding_query = modelo.encode(pregunta).tolist()
    cur.execute("""
        SELECT texto, tema, ROUND((embedding <=> %s::vector)::numeric, 4) AS distancia
        FROM frases
        WHERE texto NOT LIKE 'Frase sintética%%'
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (embedding_query, embedding_query, top_k))
    fragmentos = cur.fetchall()

    print(f"Fragmentos recuperados de pgvector:")
    for i, (texto, tema, dist) in enumerate(fragmentos, 1):
        print(f"  [{i}] dist={dist} [{tema}] {texto}")
    print()

    # PASO 2 — Armamos el contexto
    contexto = "\n".join(f"- {texto}" for texto, _, _ in fragmentos)

    # PASO 3 — El prompt final
    prompt = f"""Eres un asistente que responde basándote únicamente en el contexto provisto.
Si la respuesta no está en el contexto, decí que no lo sabés.

CONTEXTO:
{contexto}

PREGUNTA: {pregunta}

RESPUESTA:"""

    print("Prompt que se enviaría al LLM:")
    print("=" * 60)
    print(prompt)
    print("=" * 60)

    return prompt


armar_prompt_rag("¿Cuáles son los logros más importantes del fútbol uruguayo?")













# %%
# Celda 15 — Cierre
cur.close()
conn.close()
print("Conexión cerrada")


