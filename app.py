# -*- coding: utf-8 -*-
import json
import os
import requests
from flask import Flask, request, jsonify, render_template_string

# Initialize the Flask application
app = Flask(__name__)

# --- Gemini API Configuration ---
# The API key is handled by the execution environment.
API_KEY = "AIzaSyB_gwuGTYO-vw1WQwC_FA-h6aIDCcPhgOU" 
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"


# --- In-Memory Database for Chatbot Responses ---
# This dictionary stores predefined responses in multiple languages.
DATABASE = {
    "languages": {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish"
    },
    "responses": {
        "en": {
            "welcome": "Welcome to the HealthBot! How can I assist you today? You can ask about 'preventive healthcare', 'disease symptoms', or 'vaccination schedule'.",
            "fallback": "I'm sorry, I can only provide information on 'preventive healthcare', 'disease symptoms', and 'vaccination schedule'. How can I help with one of these topics?",
            "api_error": "I'm having trouble connecting to my knowledge base right now. Please try again later or ask me about core health topics.",
            "preventive_healthcare": "Preventive healthcare includes: \n1. A balanced diet (fruits, vegetables). \n2. Regular exercise (30 mins daily). \n3. Good hygiene (wash hands frequently). \n4. Avoiding tobacco and excessive alcohol.",
            "vaccination_schedule": "Standard vaccination schedule includes: \n- BCG, OPV 0, Hep B at Birth. \n- DTP, IPV, Hep B, HiB, Rotavirus, PCV at 6, 10, 14 weeks. \n- MMR at 9 months. \nConsult a doctor for a personalized schedule.",
            "symptoms_prompt": "Sure, which symptoms are you interested in? For example: 'symptoms of fever'.",
            "symptoms": {
                "fever": "Common symptoms of fever include high body temperature, sweating, chills, headache, and muscle aches. It's important to rest and stay hydrated.",
                "cough": "A cough can be dry or productive (with mucus). It can be a symptom of a cold, flu, or more serious conditions. See a doctor if it persists for more than a week.",
                "headache": "Headaches can be caused by stress, dehydration, or underlying health issues. Rest, drink water, and take pain relievers if necessary. See a doctor for severe or frequent headaches."
            },
            "outbreak_alert": "Fetching outbreak data... Currently, there are heightened reports of {disease} in the {location} area. Please take necessary precautions like wearing masks and maintaining hygiene."
        },
        "hi": {
            "welcome": "हेल्थ-बॉट में आपका स्वागत है! मैं आज आपकी कैसे सहायता कर सकता हूँ? आप 'निवारक स्वास्थ्य देखभाल', 'रोग के लक्षण', या 'टीकाकरण अनुसूची' के बारे में पूछ सकते हैं।",
            "fallback": "मुझे खेद है, मैं केवल 'निवारक स्वास्थ्य देखभाल', 'रोग के लक्षण', और 'टीकाकरण अनुसूची' पर जानकारी प्रदान कर सकता हूँ। मैं इनमें से किसी एक विषय पर आपकी कैसे मदद कर सकता हूँ?",
            "api_error": "मुझे अभी अपने नॉलेज बेस से जुड़ने में समस्या आ रही है। कृपया बाद में फिर प्रयास करें या मुझसे मुख्य स्वास्थ्य विषयों के बारे में पूछें।",
            "preventive_healthcare": "निवारक स्वास्थ्य देखभाल में शामिल हैं: \n1. संतुलित आहार (फल, सब्जियां)। \n2. नियमित व्यायाम (रोजाना 30 मिनट)। \n3. अच्छी स्वच्छता (बार-बार हाथ धोना)। \n4. तम्बाकू और अत्यधिक शराब से बचना।",
            "vaccination_schedule": "मानक टीकाकरण अनुसूची में शामिल हैं: \n- जन्म के समय बीसीजी, ओपीवी 0, हेप बी। \n- 6, 10, 14 सप्ताह में डीपीटी, आईपीवी, हेप बी, एचआईबी, रोटावायरस, पीसीवी। \n- 9 महीने में एमएमआर। \nव्यक्तिगत अनुसूची के लिए डॉक्टर से परामर्श करें।",
            "symptoms_prompt": "ज़रूर, आप किन लक्षणों में रुचि रखते हैं? उदाहरण के लिए: 'बुखार के लक्षण' पूछें।",
            "symptoms": {
                "fever": "बुखार के सामान्य लक्षणों में शरीर का उच्च तापमान, पसीना, ठंड लगना, सिरदर्द और मांसपेशियों में दर्द शामिल हैं। आराम करना और हाइड्रेटेड रहना महत्वपूर्ण है।",
                "cough": "खांसी सूखी या उत्पादक (बलगम के साथ) हो सकती है। यह सर्दी, फ्लू, या अधिक गंभीर स्थितियों का लक्षण हो सकता है। यदि यह एक सप्ताह से अधिक समय तक बना रहता है तो डॉक्टर से मिलें।",
                "headache": "सिरदर्द तनाव, निर्जलीकरण, या अंतर्निहित स्वास्थ्य समस्याओं के कारण हो सकता है। आराम करें, पानी पिएं, और यदि आवश्यक हो तो दर्द निवारक लें। गंभीर या बार-बार होने वाले सिरदर्द के लिए डॉक्टर से मिलें।"
            },
            "outbreak_alert": "प्रकोप डेटा प्राप्त हो रहा है... वर्तमान में, {location} क्षेत्र में {disease} की रिपोर्ट में वृद्धि हुई है। कृपया मास्क पहनने और स्वच्छता बनाए रखने जैसी आवश्यक सावधानी बरतें।"
        },
        "es": {
            "welcome": "¡Bienvenido al HealthBot! ¿Cómo puedo ayudarte hoy? Puedes preguntar sobre 'atención médica preventiva', 'síntomas de enfermedades' o 'calendario de vacunación'.",
            "fallback": "Lo siento, solo puedo proporcionar información sobre 'atención médica preventiva', 'síntomas de enfermedades' y 'calendario de vacunación'. ¿Cómo puedo ayudarte con uno de estos temas?",
            "api_error": "Tengo problemas para conectarme a mi base de conocimientos en este momento. Por favor, inténtalo de nuevo más tarde o pregúntame sobre temas de salud principales.",
            "preventive_healthcare": "La atención médica preventiva incluye: \n1. Una dieta balanceada (frutas, verduras). \n2. Ejercicio regular (30 minutos diarios). \n3. Buena higiene (lavarse las manos con frecuencia). \n4. Evitar el tabaco y el alcohol en exceso.",
            "vaccination_schedule": "El calendario de vacunación estándar incluye: \n- BCG, OPV 0, Hep B al nacer. \n- DTP, IPV, Hep B, HiB, Rotavirus, PCV a las 6, 10, 14 semanas. \n- MMR a los 9 meses. \nConsulte a un médico para un calendario personalizado.",
            "symptoms_prompt": "Claro, ¿en qué síntomas estás interesado? Por ejemplo: 'síntomas de fiebre'.",
            "symptoms": {
                "fever": "Los síntomas comunes de la fiebre incluyen temperatura corporal alta, sudoración, escalofríos, dolor de cabeza y dolores musculares. Es importante descansar y mantenerse hidratado.",
                "cough": "La tos puede ser seca o productiva (con moco). Puede ser un síntoma de un resfriado, gripe o afecciones más graves. Consulte a un médico si persiste por más de una semana.",
                "headache": "Los dolores de cabeza pueden ser causados por estrés, deshidratación o problemas de salud subyacentes. Descanse, beba agua y tome analgésicos si es necesario. Consulte a un médico si los dolores de cabeza son intensos o frecuentes."
            },
            "outbreak_alert": "Obteniendo datos de brotes... Actualmente, hay un aumento de informes de {disease} en el área de {location}. Por favor, tome las precauciones necesarias, como usar mascarillas y mantener la higiene."
        }
    }
}

# --- Mock Government Health Database API ---
def get_mock_outbreak_data(location):
    """Simulates an API call to a government health database."""
    mock_database = {
        "mumbai": {"disease": "Dengue", "status": "alert"},
        "delhi": {"disease": "Influenza", "status": "warning"},
        "chennai": {"disease": "Cholera", "status": "alert"},
    }
    location_key = location.lower()
    if location_key in mock_database:
        return mock_database[location_key]
    return {"disease": "no specific outbreaks", "status": "normal"}

# --- Core Chatbot Logic ---

def get_generative_response(user_query, lang="en"):
    """
    Calls the Gemini API to get a response for non-predefined queries.
    """
    system_prompt = """You are a helpful AI assistant for a healthcare chatbot. Your primary goal is to provide accurate health information.
    If the user asks a question unrelated to health, answer it concisely and politely. Then, gently guide them back to health-related topics.
    For example, if they ask about the weather, you could say: 'The weather today is sunny. By the way, I can also provide information on preventive healthcare or vaccination schedules.'
    Always respond in the language of the user's query. The user is speaking {language}."""

    language_map = {"en": "English", "hi": "Hindi", "es": "Spanish"}
    language_name = language_map.get(lang, "English")

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {
            "parts": [{"text": system_prompt.format(language=language_name)}]
        },
    }

    try:
        response = requests.post(API_URL, json=payload, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        result = response.json()
        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        return text if text else DATABASE["responses"][lang]["fallback"]
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return DATABASE["responses"][lang]["api_error"]
    except (KeyError, IndexError):
        print("Error parsing API response.")
        return DATABASE["responses"][lang]["fallback"]

def detect_language(message):
    """A very simple language detection based on keywords."""
    message_lower = message.lower()
    if any(word in message_lower for word in ['नमस्ते', 'धन्यवाद', 'बुखार']):
        return "hi"
    if any(word in message_lower for word in ['hola', 'gracias', 'fiebre']):
        return "es"
    return "en"

def generate_response(message):
    """Processes the user's message and generates a response."""
    lang = detect_language(message)
    responses = DATABASE["responses"][lang]
    message_lower = message.lower()

    # --- Step 1: Check for predefined health topics ---
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'नमस्ते', 'hola']):
        return responses["welcome"]
    if any(word in message_lower for word in ['preventive', 'health', 'care', 'निवारक', 'preventiva']):
        return responses["preventive_healthcare"]
    if any(word in message_lower for word in ['vaccination', 'vaccine', 'टीकाकरण', 'vacunación']):
        return responses["vaccination_schedule"]

    if "outbreak alert in" in message_lower:
        location = message_lower.split("outbreak alert in")[-1].strip()
        if location:
            data = get_mock_outbreak_data(location)
            return responses["outbreak_alert"].format(disease=data['disease'], location=location.capitalize())
    
    if any(word in message_lower for word in ['symptoms', 'लक्षण', 'síntomas']):
        for disease, info in responses["symptoms"].items():
            if disease in message_lower:
                return info
        return responses["symptoms_prompt"]
    
    # --- Step 2: If no match, use the generative model ---
    return get_generative_response(message, lang)

# --- Web Application Routes ---

@app.route("/")
def index():
    """Renders the main chat interface using a template string."""
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Healthcare Chatbot</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; background-color: #f0f4f8; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
            #chat-container { width: 90%; max-width: 600px; height: 80vh; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1); display: flex; flex-direction: column; overflow: hidden; }
            #chat-header { background-color: #007bff; color: white; padding: 20px; text-align: center; border-bottom: 1px solid #ddd; }
            #chat-header h1 { margin: 0; font-size: 1.5rem; }
            #chat-box { flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; }
            .message { max-width: 80%; padding: 12px 18px; border-radius: 20px; margin-bottom: 10px; line-height: 1.5; }
            .user-message { background-color: #007bff; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
            .bot-message { background-color: #e9ecef; color: #333; align-self: flex-start; border-bottom-left-radius: 4px; }
            #input-area { display: flex; padding: 20px; border-top: 1px solid #ddd; background-color: #f8f9fa; }
            #user-input { flex-grow: 1; padding: 12px; border: 1px solid #ccc; border-radius: 25px; font-size: 1rem; margin-right: 10px; outline: none; }
            #send-button { padding: 12px 25px; border: none; background-color: #007bff; color: white; border-radius: 25px; cursor: pointer; font-size: 1rem; font-weight: 500; transition: background-color 0.3s; }
            #send-button:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <div id="chat-container">
            <div id="chat-header"><h1>AI Healthcare Chatbot</h1></div>
            <div id="chat-box"></div>
            <div id="input-area">
                <input type="text" id="user-input" placeholder="Type your message here..." autocomplete="off">
                <button id="send-button">Send</button>
            </div>
        </div>
        <script>
            const chatBox = document.getElementById('chat-box');
            const userInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');

            function addMessage(message, sender) {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
                messageElement.innerText = message;
                chatBox.appendChild(messageElement);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            async function sendMessage() {
                const messageText = userInput.value.trim();
                if (messageText === '') return;
                addMessage(messageText, 'user');
                userInput.value = '';
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: messageText })
                    });
                    const data = await response.json();
                    setTimeout(() => { addMessage(data.response, 'bot'); }, 500);
                } catch (error) {
                    console.error('Error:', error);
                    addMessage('Sorry, something went wrong. Please try again.', 'bot');
                }
            }
            sendButton.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', (event) => { if (event.key === 'Enter') sendMessage(); });
            window.onload = () => { addMessage("Welcome to the HealthBot! How can I assist you today? You can ask about 'preventive healthcare', 'disease symptoms', or 'vaccination schedule'.", 'bot'); }
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

@app.route("/chat", methods=["POST"])
def chat():
    """API endpoint to handle incoming chat messages."""
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"response": "Invalid input."}), 400
    
    bot_response = generate_response(user_message)
    return jsonify({"response": bot_response})

# --- Main execution point ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


