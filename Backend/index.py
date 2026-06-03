import os
import sys
import warnings
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS  # Permite la comunicación segura con React
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

# Ignorar advertencias visuales de depreciación
warnings.filterwarnings("ignore")

app = Flask(__name__)
# Habilita CORS para que React pueda consultar esta API sin bloqueos
CORS(app, resources={r"/api/*": {"origins": "*"}}) 

# 1. Intentamos cargar el entorno local por si estamos en la computadora
directorio_actual = os.path.dirname(os.path.abspath(__file__))
ruta_env = os.path.join(directorio_actual, "entorno.env")
if os.path.exists(ruta_env):
    load_dotenv(dotenv_path=ruta_env)
else:
    load_dotenv()

def analizar_correspondencia_medica(receta: str, remedios: str) -> str:
    """
    Compara el texto de una receta médica con una lista de remedios a entregar
    utilizando Llama 3.3 en Groq mediante LangChain.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "❌ ERROR de configuración: La clave GROQ_API_KEY no está registrada en el sistema."

    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.1,  
        groq_api_key=api_key  
    )

    prompt_sistema = (
        "Eres un asistente farmacéutico experto y meticuloso. Tu tarea es comparar los medicamentos "
        "solicitados en la 'Receta Médica' con los 'Medicamentos Entregados'. "
        "Debes verificar si coinciden en nombre del fármaco, miligramos y cantidades requeridas para el tratamiento. "
        "Si hay diferencias, sustituciones no autorizadas, medicamentos faltantes o excedentes, "
        "debes señalarlo claramente mediante advertencias. Sé conciso, riguroso y directo."
    )

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
# NUEVA FUNCIÓN: INTERPRETACIÓN DE IMÁGENES CON GROK VISION
# ==========================================================
@app.route("/api/interpretar-imagen", methods=["POST"])
def interpretar_imagen_grok():
    """
    Recibe una imagen desde React, la convierte a Base64 y usa Groq Vision
    para identificar productos entregados y sus cantidades.
    """
    # 1. Verificar la API Key de xAI (Grok) encargada de la visión
    # Puedes usar la misma de Groq si la plataforma lo unifica, o almacenar XAI_API_KEY
    xai_api_key = os.getenv("XAI_API_KEY") or os.getenv("GROQ_API_KEY")
    
    if not xai_api_key:
        return jsonify({"error": "Falta la clave de API para Grok (XAI_API_KEY / GROQ_API_KEY)"}), 500

    # 2. Validar que la petición contenga un archivo
    if 'imagen' not in request.files:
        return jsonify({"error": "No se subió ninguna imagen en el campo 'imagen'"}), 400
        
    archivo_imagen = request.files['imagen']
    
    if archivo_imagen.filename == '':
        return jsonify({"error": "El nombre del archivo está vacío"}), 400

    try:
        # 3. Leer los bytes de la imagen y convertirlos a Base64 string
        bytes_imagen = archivo_imagen.read()
        base64_imagen = base64.b64encode(bytes_imagen).decode('utf-8')
        mimetype = archivo_imagen.mimetype or "image/jpeg"

        # 4. Construir la petición HTTP directa a la API de Vision de Grok
        url_grok = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {xai_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "grok-2-vision-1212", # Modelo multimodal oficial de Grok
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analiza detalladamente esta imagen de productos médicos o mercancías entregadas. "
                                "Identifica con precisión qué productos se están entregando y la cantidad de cada uno. "
                                "Devuelve la respuesta EXCLUSIVAMENTE en formato JSON plano (un arreglo de objetos). "
                                "Cada objeto debe tener la estructura: {\"producto\": \"nombre del producto\", \"cantidad\": 2}. "
                                "No agregues texto extra, saludos ni bloques de código markdown."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mimetype};base64,{base64_imagen}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1 # Temperatura muy baja para conteos y lecturas rigurosas
        }

        # 5. Realizar la solicitud a Grok
        response = requests.post(url_grok, json=payload, headers=headers)
        
        if response.status_code != 200:
            return jsonify({"error": f"Error de Grok API: {response.text}"}), response.status_code

        # 6. Procesar y limpiar la respuesta JSON de la IA
        contenido_ia = response.json()["choices"][0]["message"]["content"].strip()
        
        # Limpieza de seguridad por si Grok devuelve el JSON envuelto en ```json ... ```
        if contenido_ia.startswith("```"):
            contenido_ia = contenido_ia.replace("```json", "").replace("```", "").strip()

        # Retornamos directamente el JSON estructurado al frontend
        return contenido_ia, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return jsonify({"error": f"Error interno al procesar la imagen: {str(e)}"}), 500


# ==========================================================
#  ENDPOINT API PARA COMPARAR RECETA TEXTUAL VS REMEDIOS
# ==========================================================
@app.route("/api/validar", methods=["POST"])
def validar_receta():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No se recibieron datos en la petición"}), 400
        
    receta_texto = data.get("receta", "")
    remedios_texto = data.get("remedios", "")
    
    if not receta_texto or not remedios_texto:
        return jsonify({"error": "Faltan datos obligatorios. Asegúrate de completar receta y remedios."}), 400
        
    resultado_ia = analizar_correspondencia_medica(receta_texto, remedios_texto)
    return jsonify({"resultado": resultado_ia})


if __name__ == "__main__":
    print("🚀 Servidor Flask corriendo en [http://127.0.0.1:5000](http://127.0.0.1:5000)")
    app.run(debug=True, port=5000)