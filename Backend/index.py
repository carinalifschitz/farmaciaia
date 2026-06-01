import os
import sys
import warnings
from flask import Flask, request, jsonify
from flask_cors import CORS  # Permite la comunicación segura con React
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

# Ignorar advertencias visuales de depreciación
warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Habilita CORS para que React pueda consultar esta API sin bloqueos

def analizar_correspondencia_medica(receta: str, remedios: str) -> str:
    """
    Compara el texto de una receta médica con una lista de remedios a entregar
    utilizando Llama 3.3 en Groq mediante LangChain.
    """
    # 1. Intentamos cargar el entorno local por si estamos en la computadora
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_env = os.path.join(directorio_actual, "entorno.env")
    if os.path.exists(ruta_env):
        load_dotenv(dotenv_path=ruta_env)
    else:
        # Si no existe (como en Vercel), cargamos el load_dotenv genérico del sistema
        load_dotenv()

    # 2. Buscamos la API KEY (Vercel la inyecta directo acá)
    api_key = os.getenv("GROQ_API_KEY")

    # Si sigue sin aparecer, devolvemos un mensaje que no rompa el JSON de React
    if not api_key:
        return "❌ ERROR de configuración: La clave GROQ_API_KEY no está registrada en el sistema."

    # Inicialización del modelo
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.1,  
        groq_api_key=api_key  
    )

    # Diseño del prompt del sistema (Rol experto)
    prompt_sistema = (
        "Eres un asistente farmacéutico experto y meticuloso. Tu tarea es comparar los medicamentos "
        "solicitados en la 'Receta Médica' con los 'Medicamentos Entregados'. "
        "Debes verificar si coinciden en nombre del fármaco, miligramos y cantidades requeridas para el tratamiento. "
        "Si hay diferencias, sustituciones no autorizadas, medicamentos faltantes o excedentes, "
        "debes señalarlo claramente mediante advertencias. Sé conciso, riguroso y directo."
    )

    # Estructura de la consulta del usuario
    prompt_usuario = """
    Por favor, analiza si estos remedios corresponden a la receta:

    ---
    RECETA MÉDICA:
    {receta}
    ---
    MEDICAMENTOS ENTREGADOS:
    {remedios}
    ---

    Formato de respuesta deseado:
    - **Estado:** (COINCIDE / NO COINCIDE / COINCIDE PARCIALMENTE)
    - **Análisis:** (Breve explicación de qué coincide y qué no)
    - **Advertencias:** (Si aplica)
    """

    chat_template = ChatPromptTemplate.from_messages([
        ("system", prompt_sistema),
        ("human", prompt_usuario)
    ])

    # Orquestación de la cadena (Chain) LCEL
    chain = chat_template | llm
    
    try:
        respuesta = chain.invoke({
            "receta": receta,
            "remedios": remedios
        })
        return respuesta.content
    except Exception as e:
        return f"❌ Error al procesar la solicitud con la IA: {str(e)}"

# ==========================================================
#  ENDPOINT API PARA CONECTAR CON EL FETCH DE REACT
# ==========================================================
@app.route("/api/validar", methods=["POST"])
def validar_receta():
    # Recibimos el objeto JSON que nos envía el frontend
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No se recibieron datos en la petición"}), 400
        
    # Extraemos los textos de los textareas de React
    receta_texto = data.get("receta", "")
    remedios_texto = data.get("remedios", "")
    
    # Validación básica de campos vacíos
    if not receta_texto or not remedios_texto:
        return jsonify({"error": "Faltan datos obligatorios. Asegúrate de completar receta y remedios."}), 400
        
    # Ejecutamos la lógica de LangChain
    resultado_ia = analizar_correspondencia_medica(receta_texto, remedios_texto)
    
    # Devolvemos el resultado en un formato JSON legible para React
    return jsonify({"resultado": resultado_ia})


if __name__ == "__main__":
    # Ejecuta el servidor Flask en el puerto 5000 en modo desarrollo
    print("🚀 Servidor Flask corriendo en http://127.0.0.1:5000")
    app.run(debug=True, port=5000)