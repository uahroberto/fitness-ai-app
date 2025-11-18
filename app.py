import os
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv #Para buscar el .env
from openai import OpenAI

# Cargo las variables de entorno (mi clave de OpenAI) del archivo .env
load_dotenv()

# Inicializo mi aplicación Flask
app = Flask(__name__)

# Configuro el cliente de OpenAI
# El cliente leerá automáticamente la variable OPENAI_API_KEY que cargué
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("[INFO] Cliente de OpenAI inicializado.")
except Exception as e:
    print(f"[ERROR] No se pudo inicializar el cliente de OpenAI. ¿Falta la clave en .env? Error: {e}")
    client = None

#Si se visita la URL raíz, se ejecuta la funcion home()
@app.route("/")
def home():
    # Simplemente envío el archivo index.html que está en la misma carpeta
    return send_from_directory('.', 'index.html')



# Esta es la URL que mi JavaScript está llamando con 'fetch'
@app.route("/generar_rutina", methods=['POST'])
def generar_rutina_api():
    
    # Primero, verifico que el cliente de OpenAI esté listo
    if not client:
        # Si la clave falló al inicio, devuelvo un error 500
        return jsonify({"error": "El servidor no pudo conectarse a OpenAI. Revisa la clave API."}), 500

    # Segundo, leo el JSON que me envió el JavaScript
    try:
        datos_usuario = request.json
        print(f"[INFO] Datos recibidos: {datos_usuario}")
    except Exception as e:
        # Si el JS envía algo que no es JSON, devuelvo un error 400
        print(f"[ERROR] Petición no era JSON válido: {e}")
        return jsonify({"error": "Petición mal formada."}), 400

    #
    # --- AQUÍ VA LA MAGIA (El Prompt Engineering) ---
    #
    
    # (Por ahora, para probar, solo devuelvo los datos que recibí)
    # (En el siguiente paso, aquí llamaremos a OpenAI)
    
    # Simulación de una respuesta de IA
    respuesta_simulada = {
        "mensaje_de_prueba": "He recibido tus datos correctamente.",
        "datos_recibidos": datos_usuario
    }
    
    # Devuelvo la respuesta simulada como un JSON
    return jsonify(respuesta_simulada)


# --- Arranque del Servidor ---
if __name__ == '__main__':
    # 'debug=True' hace que el servidor se reinicie solo cada vez que guardo cambios
    app.run(host='0.0.0.0', port=5000, debug=True)