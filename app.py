import os
import json
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv #Para buscar el .env
from openai import OpenAI

# Cargo las variables de entorno (mi clave de OpenAI) del archivo .env
load_dotenv()

# Inicializo mi aplicación Flask
app = Flask(__name__)

# Configuro el cliente de OpenAI
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("[INFO] Cliente de OpenAI inicializado.")
except Exception as e:
    print(f"[ERROR] No se pudo inicializar el cliente de OpenAI. ¿Falta la clave en .env? Error: {e}")
    client = None


def obtener_rutina_ia(datos_usuario):
    
    # Uso .get() para que no falle si el dato no existe
    objetivo = datos_usuario.get('objetivo', 'general')
    nivel = datos_usuario.get('nivel', 'principiante')
    dias_lista = datos_usuario.get('dias_disponibles', [])
    dias_str = ", ".join(dias_lista) if dias_lista else "Cualquier día"
    lesiones = datos_usuario.get('lesiones', [])
    edad = datos_usuario.get('edad', 'N/A')

    # Prioridad muscular
    prioridad_raw = datos_usuario.get('musculo_prioridad', [])
    if not isinstance(prioridad_raw, list): prioridad_raw = [prioridad_raw]
    musculos_prioridad = ", ".join(prioridad_raw)

    # ---------------------------------------------------------
    # DIRECTRICES SEGUN OBJETIVO DESEADO
    # ---------------------------------------------------------
    filosofias = {
        "hipertrofia": """
            - Tu prioridad es el VOLUMEN DE ENTRENAMIENTO efectivo.
            - Busca el 'Sweet Spot': suficiente para estimular, pero recuperable.
            - Prioriza la tensión mecánica y el estrés metabólico.
            - Usa rangos de repeticiones variados (Desde 5-6 hasta 12 repeticiones -limitar fatiga-).
            - Descansos deseables para recuperacion (3-5 minutos)
        """,
        "fuerza": """
            - Tu prioridad es la INTENSIDAD (% del 1RM).
            - El volumen debe ser bajo para evitar fatiga excesiva del SNC.
            - Descansos completos (3-5 min) en ejercicios principales.
        """,
        "perdida_peso": """
            - Tu prioridad es el GASTO CALÓRICO manteninedo masa magra.
            - Diseña la rutina para mantener la frecuencia cardiaca elevada (descansos cortos).
            - Usa superseries o circuitos si es posible.
        """,
        "principiante": """
            - Tu prioridad es el APRENDIZAJE MOTOR y la ADAPTACIÓN DE TEJIDOS.
            - La intensidad debe ser moderada para garantizar una ejecución perfecta (Calidad del Input).
            - Prioriza ejercicios que se realizan en maquinas para no sobrecargar con la estabilizacion.
            - Frecuencia alta por patrón de movimiento (Full Body) para reiterar la 'programación' neural.
            - Descansos suficientes para mantener la frescura mental y técnica (2-3 min).
        """
    }
    
    # Seleccionamos la filosofía correcta. Si no hay, usamos una genérica.
    directriz_base = filosofias.get(objetivo, "Enfoque general.")

    # B. Lógica de Priorización (Lo que tú pedías)
    directriz_prioridad = ""
    if musculos_prioridad:
        directriz_prioridad = f"""
        PRINCIPIO DE PRIORIZACIÓN: El usuario quiere mejorar específicamente: {musculos_prioridad}.
        - Estructura la rutina para trabajar este músculo AL PRINCIPIO de la sesión o semana.
        - Asigna un volumen ligeramente mayor a este grupo muscular (no excesivamente mayor, no se desean desequilibrios).
        - Asegúrate de que no tenga fatiga previa cuando lo entrene.
        """

    # C. Lógica de Seguridad (Lesiones)
    directriz_seguridad = ""
    if lesiones:
        directriz_seguridad = f"""
        ADVERTENCIAS MÉDICAS: El usuario reporta: {', '.join(lesiones)}.
        - Eres responsable de filtrar CUALQUIER ejercicio biomecánicamente comprometedor para esas zonas.
        - Si hay duda, sustituye por una variante más estable (ej. máquinas o poleas).
        """

    # ---------------------------------------------------------
    # PROMPT SISTEMA
    # ---------------------------------------------------------
    
    sistema_prompt = f"""
    Actúa como un Entrenador de Élite con un PhD en Ciencias del Deporte.
    No usas plantillas genéricas; aplicas principios científicos de periodización.
    
    TUS DIRECTRICES PARA ESTE CLIENTE:
    1. FILOSOFÍA: {directriz_base}
    2. PRIORIDADES: {directriz_prioridad}
    3. SEGURIDAD: {directriz_seguridad}
    
    Tu objetivo es generar una rutina perfecta para {nivel}, entrenando los días: {dias_str}.
    
    IMPORTANTE: Responde SOLO con un JSON válido con la siguiente estructura para que mi app lo entienda:
    {{
      "nombre_rutina": "Texto",
      "consejo_experto": "Explica por qué diseñaste esto así basándote en sus datos",
      "dias": [
        {{
          "dia": "Lunes",
          "musculos": "Pecho / Tríceps",
          "ejercicios": [
            {{ "nombre": "Press Banca", "series": 4, "repes": "6-8", "tip": "Retrae escápulas" }}
          ]
        }}
      ]
    }}
    """

    # ---------------------------------------------------------
    # PROMPT USUARIO
    # ---------------------------------------------------------

    usuario_prompt = f"""
    Hola entrenador. Soy un usuario de nivel {nivel} y tengo {datos_usuario.get('edad', 'desconocida')} años.
    
    Mis datos de entrenamiento son:
    - Días disponibles: {dias_str}
    - Mi objetivo principal: {objetivo}
    
    Por favor, genérame la rutina completa en formato JSON siguiendo estrictamente tus directrices de seguridad y prioridad.
    """


    # LLAMADA A LA API
    print(f"[IA] Enviando petición a OpenAI para objetivo: {objetivo}...")
    
    try:
        # 1. Enviamos
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo", # Modelo estándar y económico
            messages=[
                # Rol SYSTEM: Contexto y las reglas
                {"role": "system", "content": sistema_prompt},
                # Rol USER: La petición específica (Los datos del usuario)
                {"role": "user", "content": usuario_prompt}
            ],
            temperature=0.7, # Creatividad equilibrada (0.0 es robot, 1.0 es muy creativo)
        )

        # 2. Recibimos y Limpiamos

        """Se pueden pedir varias respuestas (n=3)
        Al haber hecho solo 1 peticion, el tamaño de la lista será 1 ( posicion 0)"""

        texto_respuesta = respuesta.choices[0].message.content
        texto_limpio = texto_respuesta.replace("```json", "").replace("```", "").strip()
        
        # 3. Convertimos a Diccionario y devolvemos
        return json.loads(texto_limpio)
    
    except Exception as e:
        print(f"[ERROR IA] Hubo un fallo al hablar con OpenAI: {e}")
        return None



#Si se visita la URL raíz, se ejecuta la funcion home()
@app.route("/")
def home():
    return send_from_directory('.', 'index.html')

@app.route("/generar_rutina", methods=['POST'])
def generar_rutina_api():
    
    # 1. Validación Cliente
    if not client:
        return jsonify({"error": "Error de servidor: Sin clave API."}), 500

    # 2. Recepción de datos
    try:
        datos_usuario = request.json
    except Exception:
        return jsonify({"error": "Datos inválidos."}), 400

    # 3. LLAMADA A LA FUNCIÓN QUE ACABAMOS DE DEFINIR ARRIBA
    # Esta es la línea que te faltaba o estaba mal colocada
    rutina_generada = obtener_rutina_ia(datos_usuario)
    
    # 4. Respuesta al Frontend
    if rutina_generada:
        return jsonify(rutina_generada)
    else:
        return jsonify({"error": "La IA no pudo generar la rutina."}), 500
    

# --- Arranque del Servidor ---
if __name__ == '__main__':
    # 'debug=True' hace que el servidor se reinicie solo cada vez que guardo cambios
    app.run(host='0.0.0.0', port=5000, debug=True)