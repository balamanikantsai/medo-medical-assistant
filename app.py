import torch
from utils.auth import init_user_storage, hash_password, check_password, get_user, add_user
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import ollama
import time
import json
import re
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from google.cloud import translate_v2 as translate
from google.cloud import speech
from google.cloud import texttospeech
from werkzeug.utils import secure_filename
from create_event import create_calendar_event
import base64

# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
FIRECRAWL_API_KEY = "fc-0126c9f027574e3897a696c7517ca00b"
load_dotenv()

# Initialize Google Translate client
try:
    translate_client = translate.Client.from_service_account_json("translate.json")
    print("✅ Google Translate Client Initialized Successfully")
except Exception as e:
    print(f"⚠️ Error initializing Google Translate client: {e}")
    translate_client = None

# Configuration for Speech-to-Text and Text-to-Speech
SPEECH_CREDENTIALS_FILE = 'speech-credentials.json'

# Initialize Google Speech client
speech_client = None
try:
    if os.path.exists(SPEECH_CREDENTIALS_FILE):
        speech_client = speech.SpeechClient.from_service_account_json(SPEECH_CREDENTIALS_FILE)
        print("✅ Google Speech Client (STT) Initialized Successfully")
    else:
        print(f"⚠️ Warning: Speech credentials file '{SPEECH_CREDENTIALS_FILE}' not found. Speech-to-text will be disabled.")
except Exception as e:
    print(f"⚠️ Error initializing Google Speech client (STT): {e}")
    speech_client = None

# Initialize Google Text-to-Speech client
tts_client = None
try:
    if os.path.exists(SPEECH_CREDENTIALS_FILE):
        tts_client = texttospeech.TextToSpeechClient.from_service_account_json(SPEECH_CREDENTIALS_FILE)
        print("✅ Google Text-to-Speech Client (TTS) Initialized Successfully")
    else:
        print(f"⚠️ Warning: Speech credentials file '{SPEECH_CREDENTIALS_FILE}' not found. Text-to-speech will be disabled.")
except Exception as e:
    print(f"⚠️ Error initializing Google Text-to-Speech client (TTS): {e}")
    tts_client = None

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_user_language(username):
    try:
        df = pd.read_excel("users.xlsx")
        user_row = df[df['username'] == username]
        return user_row['language'].values[0] if not user_row.empty else "en"
    except FileNotFoundError:
        print("Warning: users.xlsx not found. Defaulting to English.")
        return "en"
    except Exception as e:
        print(f"Error reading user language: {e}. Defaulting to English.")
        return "en"

def translate_text(texts, src_lang="en", tgt_lang="hi"):
    if src_lang == tgt_lang:
        return texts

    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        return []

    try:
        translations = translate_client.translate(
            texts, source_language=src_lang, target_language=tgt_lang
        )
        results = [t['translatedText'] if t else orig for t, orig in zip(translations, texts)]
        return results if len(results) > 1 else results[0]
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return texts

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def synthesize_speech(text, language_code="en-US", voice_gender="NEUTRAL"):
    """Synthesizes speech from the input string of text."""
    if not tts_client:
        print("⚠️ TTS client not available. Cannot synthesize speech.")
        return None

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender[voice_gender]
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    try:
        print(f"Synthesizing speech for text (Lang: {language_code}): {text[:50]}...")
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        print("✅ Speech synthesized successfully.")
        return base64.b64encode(response.audio_content).decode('utf-8')
    except Exception as e:
        print(f"⚠️ Error during speech synthesis: {e}")
        return None

def parse_prescription_with_llm(prescription_text):
    prompt = f"""
    You are an expert medical prescription parser. Analyze the following prescription text and extract the diagnosis (if present) and medication details.
    Return the information ONLY as a valid JSON object with the following structure:
    {{
      "diagnosis": "...",
      "medications": [
        {{
          "name": "...",
          "dosage": "...",
          "frequency": "...",
          "timing": "..." // Extract specific times (e.g., "9:00 AM", "14:30"), keywords (e.g., "breakfast", "lunch", "dinner", "night", "morning", "afternoon", "evening"), and instructions (e.g., "before food", "after food", "with meals"). Keep this as a descriptive string. Example: "morning before breakfast", "8:00 AM and 6:00 PM", "lunch and dinner after food"
        }}
      ]
    }}
    If information is missing for a field, use null or an empty string. Be precise with the timing details extracted.

    Prescription Text:
    ---
    {prescription_text}
    ---

    JSON Output:
    """
    try:
        response = ollama.chat(
            model='llama3.2:latest',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.1}
        )
        content = response['message']['content'].strip()
        if content.startswith("```json"):
            content = content[len("```json"):].strip()
        elif content.startswith("```"):
             content = content[len("```"):].strip()
        if content.endswith("```"):
            content = content[:-len("```")].strip()
            
        parsed_data = json.loads(content)
        print("✅ Prescription Parsed Successfully by LLM.")
        
        if not isinstance(parsed_data, dict):
             print("⚠️ LLM output was not a JSON object.")
             return None
        if 'medications' not in parsed_data:
             if 'diagnosis' not in parsed_data or not parsed_data.get('diagnosis'):
                 print("⚠️ LLM output missing 'medications' and 'diagnosis'.")
                 return None
             else:
                 parsed_data['medications'] = [] 
        elif not isinstance(parsed_data.get('medications'), list):
             print("⚠️ LLM 'medications' field is not a list.")
             return None
             
        return parsed_data
        
    except json.JSONDecodeError as e:
        print(f"Error decoding LLM JSON response: {e}")
        print(f"LLM Raw Output:\n{content}")
        return None
    except ollama.ResponseError as e:
        print(f"Ollama API Error during parsing: {e.status_code} - {e.error}")
        return None
    except Exception as e:
        print(f"Error parsing prescription with LLM: {e}")
        return None

def firecrawl_search(query, num_of_searches=10):
    """Searches the web using Firecrawl API and returns results with sources."""
    url = "https://api.firecrawl.dev/v1/search"
    payload = {
        "limit": num_of_searches,
        "query": query,
        "extractorOptions": {
            "mode": "llm-extraction",
            "extractionSchema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "source": {"type": "string"}
                }
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        results = response.json().get('data', [])
        
        sources = []
        for result in results:
            if 'llm_extraction' in result:
                sources.append({
                    "text": result['llm_extraction']['summary'],
                    "url": result['llm_extraction']['source']
                })
        return sources[:4]
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return []
    

    
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session.pop('user', None)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and len(user) > 2:
            stored_hash = user[2]
            if check_password(password, stored_hash):
                session['user'] = username
                return redirect(url_for('chat'))
            else:
                flash('Invalid username or password.', 'error')
        else:
            flash('Invalid username or password.', 'error')

    return render_template('index.html')

@app.route('/chat', methods=['GET'])
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
            flash('Password must be at least 8 characters long and include an uppercase letter and a digit.', 'error')
            return redirect(url_for('register'))

        success = add_user(email, username, password)
        if not success:
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET'])
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    current_lang = get_user_language(session['user'])
    supported_languages = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "te": "Telugu",
        "ko": "Korean"
    }
    return render_template('settings.html', current_lang=current_lang, languages=supported_languages)

@app.route('/update_language', methods=['POST'])
def update_language():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    new_language = request.form['language']

    try:
        df = pd.read_excel("users.xlsx")
        if username in df['username'].values:
            df.loc[df['username'] == username, 'language'] = new_language
            df.to_excel("users.xlsx", index=False)
            flash("Language updated successfully!", "success")
        else:
            flash("User not found in database.", "error")
    except FileNotFoundError:
        flash("Error: User database file not found.", "error")
    except Exception as e:
        flash(f"Error updating language: {str(e)}", "error")

    return redirect(url_for('settings'))

@app.route('/upload_prescription', methods=['POST'])
def upload_prescription():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    if 'prescriptionFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['prescriptionFile']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            print(f"File saved to {filepath}")

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    prescription_text = f.read()
            except Exception as read_err:
                 print(f"Error reading file {filepath}: {read_err}")
                 if os.path.exists(filepath): os.remove(filepath)
                 return jsonify({'error': f'Could not read file content: {read_err}'}), 500

            if not prescription_text.strip():
                 print(f"Warning: File {filepath} is empty.")
                 if os.path.exists(filepath): os.remove(filepath)
                 return jsonify({'error': 'File content is empty.'}), 400

            parsed_data = parse_prescription_with_llm(prescription_text)

            if not parsed_data:
                if os.path.exists(filepath): os.remove(filepath)
                return jsonify({'error': 'Failed to parse prescription using LLM. Check logs.'}), 500

            success, message = create_calendar_event(parsed_data)

            try:
                os.remove(filepath)
                print(f"Removed uploaded file: {filepath}")
            except OSError as e:
                print(f"Warning: Error removing file {filepath}: {e.strerror}")

            if success:
                return jsonify({'message': message, 'parsed_data': parsed_data}), 200
            else:
                return jsonify({'error': message, 'parsed_data': parsed_data}), 500

        except Exception as e:
            print(f"Error processing upload: {e}")
            if 'filepath' in locals() and os.path.exists(filepath):
                 try: os.remove(filepath)
                 except OSError as e_rem: print(f"Error removing file {filepath} after error: {e_rem.strerror}")
            return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    else:
        return jsonify({'error': 'File type not allowed. Please upload a .txt file.'}), 400

@app.route('/get_response', methods=['POST'])
def get_response():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    start_time = time.time()
    username = session['user']
    user_lang = get_user_language(username)
    user_prompt = request.json.get('prompt', '')

    if not user_prompt:
        return jsonify({'error': 'Empty prompt received'}), 400

    processing_prompt = user_prompt
    if user_lang != "en":
        translated_input = translate_text(user_prompt, src_lang=user_lang, tgt_lang="en")
        if isinstance(translated_input, str) and translated_input != user_prompt:
            processing_prompt = translated_input
        elif isinstance(translated_input, list) and translated_input and translated_input[0] != user_prompt:
            processing_prompt = translated_input[0]
        else:
            print(f"Warning: Translation to English might have failed for prompt: {user_prompt}")

    print(f"Processing Prompt (EN): {processing_prompt}")

    search_decision_prompt = f"""You are Medo, a helpful medical assistant. Analyze the following user query:
    "{processing_prompt}"

    Is external web search REQUIRED to provide an accurate, up-to-date, and safe medical answer?
    - If YES, respond ONLY with: [SEARCH_NEEDED] followed by the best search query (e.g., "[SEARCH_NEEDED] side effects of ibuprofen").
    - If NO (e.g., greeting, simple definition, non-medical), respond ONLY with: [NO_SEARCH_NEEDED].
    """
    search_context = ""
    sources = []
    english_answer = "Sorry, I encountered an issue. Please try again."

    try:
        decision_response = ollama.chat(
            model='llama3.2:latest',
            messages=[{"role": "user", "content": search_decision_prompt}],
            options={'temperature': 0.1}
        )
        decision_text = decision_response['message']['content'].strip()
        print(f"LLM Search Decision: {decision_text}")

        if decision_text.startswith("[SEARCH_NEEDED]"):
            search_query = decision_text.replace("[SEARCH_NEEDED]", "").strip()
            if search_query:
                print(f"Performing search for: {search_query}")
                search_context, sources = firecrawl_search(search_query)
                if not search_context:
                    print("Search performed but returned no usable context.")
                    search_context = "No specific context found from web search."
                else:
                    print(f"Search Context Found ({len(sources)} sources).")
            else:
                print("LLM indicated search needed but provided no query.")
                search_context = "Search was indicated but no query was provided."
                decision_text = "[NO_SEARCH_NEEDED]"

        if decision_text.startswith("[NO_SEARCH_NEEDED]") or search_context:
            final_prompt_parts = [
                f"You are Medo, an expert medical assistant. Provide a clear, concise, empathetic, and safe response to the user's query using simple language.",
                f"User Query: \"{processing_prompt}\"",
            ]
            if search_context:
                final_prompt_parts.append(f"\nUse the following information from a web search if relevant:\n---\n{search_context}\n---")
            else:
                final_prompt_parts.append("\nAnswer based on your general medical knowledge. No external search context was available or deemed necessary.")

            final_prompt_parts.extend([
                "IMPORTANT:",
                "- If the query is NOT medical, politely state you only handle medical questions.",
                "- Prioritize safety. Advise seeking professional medical help for serious concerns.",
                "- Keep the response concise (ideally under 10-12 lines) and use clear paragraphs.",
                "- Use 'Medo' when referring to yourself.",
                "- Include relevant emojis if appropriate. 😊"
            ])
            final_prompt = "\n".join(final_prompt_parts)

            print("Generating final response...")
            answer_response = ollama.chat(
                model='llama3.2:latest',
                messages=[{"role": "user", "content": final_prompt}],
                options={'temperature': 0.5}
            )
            english_answer = answer_response['message']['content']
            print(f"Generated English Answer: {english_answer[:100]}...")
        else:
            english_answer = "I determined that a search was needed, but encountered an issue retrieving the information. Please try rephrasing your query."

    except ollama.ResponseError as e:
        print(f"Ollama API Error: {e.status_code} - {e.error}")
        english_answer = f"Sorry, I couldn't connect to the AI model (Error: {e.status_code}). Please try again later."
    except Exception as e:
        print(f"Error during LLM interaction or processing: {str(e)}")
        english_answer = f"Sorry, an unexpected error occurred: {str(e)}"

    final_answer = english_answer
    if user_lang != "en":
        translated_output = translate_text(english_answer, src_lang="en", tgt_lang=user_lang)
        if isinstance(translated_output, str) and translated_output != english_answer:
            final_answer = translated_output
        elif isinstance(translated_output, list) and translated_output and translated_output[0] != english_answer:
            final_answer = translated_output[0]
        else:
            print(f"Warning: Translation from English might have failed for answer.")

    audio_content_base64 = None
    if final_answer and tts_client:
        tts_lang_map = {
            'en': 'en-US',
            'hi': 'hi-IN',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'te': 'te-IN',
            'ko': 'ko-KR'
        }
        tts_language_code = tts_lang_map.get(user_lang, 'en-US')
        audio_content_base64 = synthesize_speech(final_answer, language_code=tts_language_code)

    inference_time = round(time.time() - start_time, 2)
    print(f"Total processing time: {inference_time}s")

    return jsonify({
        'response': final_answer,
        'inference_time': inference_time,
        'sources': sources,
        'audio_content': audio_content_base64,
        'debug_en_prompt': processing_prompt,
        'debug_en_answer': english_answer
    })

@app.route('/transcribe_audio', methods=['POST'])
def transcribe_audio():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    if not speech_client:
        return jsonify({'error': 'Speech-to-Text service not configured or available.'}), 503

    if 'audio_blob' not in request.files:
        return jsonify({'error': 'No audio data received.'}), 400

    audio_file = request.files['audio_blob']
    
    user_lang_code = get_user_language(session['user'])
    lang_map = {
        'en': 'en-US',
        'hi': 'hi-IN',
        'es': 'es-ES',
        'fr': 'fr-FR',
        'te': 'te-IN',
        'ko': 'ko-KR'
    }
    bcp47_language_code = lang_map.get(user_lang_code, 'en-US')

    try:
        content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            language_code=bcp47_language_code,
        )

        print(f"Sending audio for transcription (Language: {bcp47_language_code})...")
        response = speech_client.recognize(config=config, audio=audio)
        print("Transcription response received.")

        transcript = ""
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            print(f"Transcription: {transcript}")
        else:
            print("No transcription results found.")

        return jsonify({'transcript': transcript})

    except Exception as e:
        print(f"Error during transcription: {e}")
        if "requires an encoding" in str(e):
             return jsonify({'error': 'Audio encoding issue. Please ensure audio is in a supported format.'}), 500
        return jsonify({'error': f'Failed to transcribe audio: {str(e)}'}), 500

if __name__ == '__main__':
    if not os.path.exists('token.json'):
        print("\n" + "="*60)
        print("⚠️ Google Calendar token.json not found.")
        print("Please run 'python create_event.py' once manually from your terminal to authorize Google Calendar access.")
        print("The web server might not be able to add events until authorized.")
        print("="*60 + "\n")

    if not os.path.exists(SPEECH_CREDENTIALS_FILE):
         print("\n" + "="*60)
         print(f"⚠️ Google Speech credentials file '{SPEECH_CREDENTIALS_FILE}' not found.")
         print("   Speech-to-text AND Text-to-Speech functionality will be disabled.")
         print("   Follow the steps in the README to set it up.")
         print("="*60 + "\n")
    else:
        if not speech_client:
            print("⚠️ Speech-to-Text client failed to initialize despite credentials file existing.")
        if not tts_client:
            print("⚠️ Text-to-Speech client failed to initialize despite credentials file existing.")

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
