import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from utils.auth import init_user_storage, hash_password, check_password, get_user, add_user
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import ollama
import time
import json
import re
import pandas as pd
import requests
import os
from dotenv import load_dotenv  # Corrected import
from google.cloud import translate_v2 as translate

# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
FIRECRAWL_API_KEY = "fc-0126c9f027574e3897a696c7517ca00b"
load_dotenv()
# Initialize Google Translate client
translate_client = translate.Client.from_service_account_json("translate.json")

print("✅ Translation Model Loaded Successfully")


def get_user_language(username):
    """Fetch user language preference from users.xlsx."""
    df = pd.read_excel("users.xlsx")
    user_row = df[df['username'] == username]
    return user_row['language'].values[0] if not user_row.empty else "en"  # Default to English


def translate(texts, src_lang="en", tgt_lang="hi"):
    """Translates text using Google Translate API."""
    if src_lang == tgt_lang:
        return texts  # No translation needed if languages match

    if isinstance(texts, str):
        texts = [texts]

    try:
        translations = translate_client.translate(
            texts, source_language=src_lang, target_language=tgt_lang
        )
        return [translation['translatedText'] for translation in translations]
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return texts  # Return original text in case of error


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = get_user(username)
        if user:
            stored_password = user[2]  # Assuming [email, username, password,language] structure
            if check_password(password, stored_password):
                session['user'] = username
                return redirect(url_for('chat'))
        
        return 'Invalid Credentials', 401
    
    return render_template('index.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
            return 'Weak Password', 400

        success = add_user(email, username, password)
        if not success:
            return 'Username already exists', 400

        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/chat', methods=['GET'])
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET'])
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/update_language', methods=['POST'])
def update_language():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    new_language = request.form['language']

    try:
        # Update the language in users.xlsx
        df = pd.read_excel("users.xlsx")
        if username in df['username'].values:
            df.loc[df['username'] == username, 'language'] = new_language
            df.to_excel("users.xlsx", index=False)
            flash("Language updated successfully!", "success")
        else:
            flash("User not found in database.", "error")
    except Exception as e:
        flash(f"Error updating language: {str(e)}", "error")

    # Redirect back to the previous page (e.g., ongoing chat)
    return redirect(request.referrer or url_for('chat'))

def firecrawl_search(query, num_of_searches=5):
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
        return sources[:4]  # Return top 3 sources
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return []


def restructure(user_prompt):
    """Enhances prompt clarity and determines if web search is necessary."""
    system_prompt = """You are a medical prompt optimizer. Your tasks:
    1. Correct grammar and spelling while preserving meaning.
    2. Make it concise.
    3. Identify if external medical information is required:
       - Return 1 for fact-based medical queries.
       - Return 0 for greetings or non-medical topics.
       
    Respond ONLY in JSON format: {"digit": 0 or 1, "restructured_prompt": "..."}"""
    
    try:
        response = ollama.chat(model='llama3.2:latest', messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        raw_json = re.sub(r'```json|```', '', response['message']['content']).strip()
        result = json.loads(raw_json)
        
        return {
            "digit": int(result["digit"]),
            "restructured_prompt": result["restructured_prompt"][:150]  # Limit length
        }
    
    except Exception as e:
        print(f"Restructure error: {str(e)}")
        return {"digit": 0, "restructured_prompt": user_prompt}




@app.route('/get_response', methods=['POST'])
def get_response():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    username = session['user']
    user_lang = get_user_language(username)
    user_prompt = request.json['prompt']

    # Step 1: Translate non-English input to English
    original_language = user_lang
    if original_language != "en":
        try:
            translated_input = translate(user_prompt, src_lang=original_language, tgt_lang="en")
            if isinstance(translated_input, list):
                translated_input = translated_input[0]
            processing_prompt = translated_input
        except Exception as e:
            print(f"Translation error: {str(e)}")
            processing_prompt = user_prompt
    else:
        processing_prompt = user_prompt

    # Step 2: Restructure the translated prompt
    restructured = restructure(processing_prompt)
    digit, modified_prompt = restructured['digit'], restructured['restructured_prompt']

    # Step 3: Web search with English query
    sources = []
    if digit == 1:
        try:
            sources = firecrawl_search(modified_prompt)
            context = "\n".join([f"{s['text']}" for s in sources])
        except Exception as e:
            print(f"Search error: {str(e)}")
            context = ""
    else:
        context = ""

    # Step 4: Generate English response
    try:
        start_time = time.time()
        response = ollama.chat(
            model='llama3.2:latest',
            messages=[{"role": "user", "content": f"""
                As a medical expert, respond to this query: {modified_prompt}
                Context: {context}
                - Keep response under 12 lines
                - Use simple language
                - Include emojis where appropriate
                - Format with clear paragraphs"""}],
            options={'temperature': 0.4}
        )
        english_answer = response['message']['content']

        # Step 5: Translate response to user's language
        if user_lang != "en":
            translated_answer = translate(english_answer, 
                                       src_lang="en", 
                                       tgt_lang=user_lang)
            if isinstance(translated_answer, list):
                translated_answer = translated_answer[0]
        else:
            translated_answer = english_answer

        return jsonify({
            'response': translated_answer,
            'inference_time': round(time.time() - start_time, 2),
            'sources': [s['url'] for s in sources],
            'original_response': english_answer  # For debugging
        })
    
    except Exception as e:
        error_msg = translate(f"Error: {str(e)}", "en", user_lang) if user_lang != "en" else str(e)
        return jsonify({'error': error_msg}), 500
'''
@app.route('/get_response', methods=['POST'])
def get_response():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    username = session['user']
    user_lang = get_user_language(username)  # Fetch user language preference
    user_prompt = request.json['prompt']
    
    # Restructure the user query
    restructured = restructure(user_prompt)
    digit, modified_prompt = restructured['digit'], restructured['restructured_prompt']
    print(f"Restructured Prompt: {modified_prompt}")
    print(f"Digit: {digit}")
    # Fetch search results if needed
    sources = []
    if digit == 1:
        sources = firecrawl_search(modified_prompt)
        context = "\n".join([f"{s['text']}" for s in sources])
        print("search completed")
    else:
        context = ""

    # Generate the response
    prompt = f"""You are Medo, an expert medical assistant who provides accurate health information and guidance.
         you are trained to give accurate information and support to users. you answer only to medical queries.
    Your task is to provide a clear and concise response to the user's query, using the information provided in the context if available.
    If the user query is not medical, respond with "I can only assist with medical queries."
    If the user query is medical, provide a detailed response based on the context and your knowledge.
    Your response should be informative, empathetic, and supportive. Avoid using complex medical jargon.
    If the user query is about a specific medical condition, provide relevant information and resources.
    If the user query is about a medication, provide information about its uses, side effects, and precautions.
    If the user query is about a symptom, provide information about possible causes and when to seek medical attention.
    If the user query is about a treatment, provide information about its effectiveness and potential risks.
    If the user query is about a procedure, provide information about what to expect and how to prepare.
    If the user query is about a test, provide information about its purpose and what the results may indicate.
    If the user query is about a health concern, provide information about its causes, symptoms, and treatment options.
    If the user query is about a health topic, provide information about its causes, symptoms, and treatment options.
    if you are mentioning about yourselves, please use "Medo" instead of "I" or "me" and mention you are a medical assistant and specialized in providing health information and guidance. dont tell you are not specialized, believe in yourself and be confident.
    Write in clear paragraphs or bullet points if necessary. Use simple language and focus on essential details.
     keep the response under 12 lines.
    answer the user query below.
    User Query: {modified_prompt}

    Relevant Information: {context if context else "No additional context available."}
     
    """
    
    
    try:
        start_time = time.time()
        response = ollama.chat(
            model='llama3.2:latest',
            messages=[{"role": "user", "content": prompt}],
            options={'temperature': 0.4}
        )
        answer = response['message']['content']
        print(f"Answer: {answer}")
        # Translate response if necessary
        translated_answer = translate(answer, src_lang="en", tgt_lang=user_lang) if user_lang != "en" else answer
        print
        return jsonify({
            'response': translated_answer if isinstance(translated_answer, str) else translated_answer[0],
            'inference_time': round(time.time() - start_time, 2),
            'sources': [s['url'] for s in sources]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

'''



if __name__ == '__main__':
    app.run(debug=True)
