import os
import time
from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ ERROR: No API key found in .env file!")
    print("Please add your Gemini API key to the .env file:")
    print("GEMINI_API_KEY=your-key-here")

client = genai.Client(api_key=GEMINI_API_KEY)

# Cache for storing responses
response_cache = {}

# Simple rate limiting
last_request_time = 0
min_request_interval = 2

def get_available_models():
    """Get list of available models from API"""
    try:
        models = client.models.list()
        available_models = []
        for model in models:
            model_name = model.name.replace('models/', '')
            available_models.append(model_name)
            print(f"  📌 Found model: {model_name}")
        return available_models
    except Exception as e:
        print(f"❌ Could not fetch models: {e}")
        return []

def find_working_model():
    """Find a working model for content generation"""
    try:
        # First, try to get models from API
        models = get_available_models()
        
        # Filter for models that might work for chat
        working_models = [m for m in models if 'flash' in m or 'pro' in m]
        
        if working_models:
            print(f"✅ Found {len(working_models)} potential models")
            return working_models[0]  # Return first working model
    except:
        pass
    
    # Fallback to known model names if API call fails
    fallback_models = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-pro",
    ]
    
    for model in fallback_models:
        try:
            test_response = client.models.generate_content(
                model=model,
                contents="test"
            )
            if test_response:
                print(f"✅ Using fallback model: {model}")
                return model
        except:
            continue
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global last_request_time
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip().lower()
        
        if not user_message:
            return jsonify({"response": "Please enter a disease name."})
        
        # Check cache first
        if user_message in response_cache:
            print(f"✅ Using cached response for: {user_message}")
            cache_entry = response_cache[user_message]
            if datetime.now() - cache_entry['timestamp'] < timedelta(hours=1):
                return jsonify({"response": cache_entry['response']})
            else:
                del response_cache[user_message]
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - last_request_time
        if time_since_last < min_request_interval:
            wait_time = min_request_interval - time_since_last
            time.sleep(wait_time)
        
        # Find working model
        working_model = find_working_model()
        if not working_model:
            return jsonify({
                "response": """⚠️ **API Connection Issue**

Unable to connect to Gemini API. This usually means:

• Your API key is invalid or expired
• You need to enable the Gemini API in Google Cloud

**Quick fixes:**
1. Get a new API key from https://aistudio.google.com/
2. Update your .env file with the new key
3. Restart the application

**Until then, try these cached suggestions:**
- Fever
- Mastitis
- Foot and mouth disease
- Anthrax"""
            })
        
        # Prepare prompt
        prompt = f"""You are a veterinary assistant. For the cow disease "{user_message}", provide:

**Withdrawal Period:** [specific time period]
**Precautions:** [specific precautions]
**Medicines:** [specific medicines]
**Dose:** [dosage information]

Keep it concise and practical."""
        
        try:
            # Generate response
            response = client.models.generate_content(
                model=working_model,
                contents=prompt
            )
            
            last_request_time = time.time()
            
            if response and response.text:
                bot_reply = response.text.strip()
                
                # Cache the response
                response_cache[user_message] = {
                    'response': bot_reply,
                    'timestamp': datetime.now()
                }
                
                return jsonify({"response": bot_reply})
            else:
                return jsonify({"response": "I couldn't generate a response. Please try again."})
                
        except Exception as e:
            error_str = str(e)
            
            if "429" in error_str:
                return jsonify({
                    "response": """⚠️ **Free API Quota Exceeded**

• Wait 30 seconds and try again
• Try a different disease (cached ones work)
• Daily quota resets at midnight PT

**Try these cached suggestions:** Fever, Mastitis, Foot & Mouth"""
                })
            elif "404" in error_str:
                return jsonify({
                    "response": """⚠️ **Model Not Found**

The model is temporarily unavailable. Using cached responses only.

**Working suggestions:** Fever, Mastitis, Foot & Mouth, Anthrax"""
                })
            else:
                return jsonify({"response": f"Error: {error_str[:200]}"})
        
    except Exception as e:
        return jsonify({"response": f"Sorry, an error occurred: {str(e)[:200]}"})

if __name__ == '__main__':
    print("🔍 Testing Gemini API connection...")
    print(f"📝 API Key: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-5:] if GEMINI_API_KEY else 'NOT FOUND'}")
    
    if not GEMINI_API_KEY:
        print("❌ No API key found!")
    else:
        working_model = find_working_model()
        if working_model:
            print(f"✅ API connected successfully using: {working_model}")
        else:
            print("❌ Could not connect to Gemini API. Please check your API key.")
            print("\nTo get a new API key:")
            print("1. Go to https://aistudio.google.com/")
            print("2. Click 'Get API Key'")
            print("3. Create a new key")
            print("4. Update your .env file")
    
    app.run(host="0.0.0.0", port=5000)