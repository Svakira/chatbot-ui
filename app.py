from flask import Flask, render_template, request, jsonify, session
import json
import requests
from datetime import datetime
import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import secrets
import pickle
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

SESSION_FOLDER = 'sessions'
if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER)

# Threshold for storing files on server vs browser (100KB)
STORAGE_THRESHOLD = 100 * 1024  # 100KB in bytes

DEFAULT_CONFIG = {
    'max_tokens': int(os.getenv('MAX_TOKENS', 4000)),
    'temperature': float(os.getenv('TEMPERATURE', 0.3)),
    'model_name': os.getenv('MODEL_NAME', 'RedHatAI/Llama-4-Scout-17B-16E-Instruct-FP8-dynamic'),
    'context_limit': int(os.getenv('CONTEXT_LIMIT', 1000000)),
    'api_url': os.getenv('MODEL_API_URL', 'http://154.54.100.200:8090/v1/chat/completions')
}

DEFAULT_SYSTEM_PROMPT = """You must primarily use and rely only on the information supplied in the context documents. Do NOT provide general knowledge or information unless explicitly asked. In your reasoning and answers, cite or ground everything in the supplied context. Ignore any knowledge from your training that is not present in the context.

CRITICAL RULES:
1. Answer ONLY based on the context documents provided
2. ALWAYS cite your source using the format: [Source N: filename]
3. If information is not in the context, respond: "I don't have that information in the provided context"
4. When quoting, use exact text from the source
5. If context is ambiguous, state that clearly
6. You can reference previous messages in the conversation for continuity

CITATION FORMAT:
- When answering, always include: [Source 1: book.epub] or [Source 2: document.txt]
- When quoting: "exact quote here" [Source 1: book.epub]

Your purpose is to help extract and understand information from the provided documents with proper attribution."""

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'epub', 'md', 'json', 'csv', 'log'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_size(size):
    for unit in ['B', 'KB', 'MB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} GB"

def count_tokens_estimate(text):
    if not text:
        return 0
    return len(text) // 4

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    return text.strip()

def extract_text_from_epub(epub_path):
    try:
        book = epub.read_epub(epub_path)
        chapters = []
        items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        
        for item in items:
            try:
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')
                
                for script in soup(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                
                text = soup.get_text(separator='\n', strip=True)
                
                if text and len(text.strip()) > 100:
                    cleaned_text = clean_text(text)
                    if cleaned_text:
                        chapters.append(cleaned_text)
                        
            except Exception as e:
                print(f"Warning: Could not process item: {e}")
                continue
        
        if not chapters:
            raise Exception("No text content could be extracted from EPUB")
        
        full_text = '\n\n=== CHAPTER BREAK ===\n\n'.join(chapters)
        return full_text
    
    except Exception as e:
        raise Exception(f"Error reading EPUB: {e}")

def read_file_content(filepath):
    _, ext = os.path.splitext(filepath.lower())
    
    if ext == '.epub':
        return extract_text_from_epub(filepath)
    elif ext in ['.txt', '.md', '.json', '.csv', '.log', '']:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            raise Exception(f"Unsupported file type: {ext}")

def build_context_section(context_files):
    if not context_files:
        return ""
    
    context_parts = ["=== CONTEXT DOCUMENTS ===\n"]
    
    for i, f in enumerate(context_files, 1):
        context_parts.append(f"=== SOURCE {i}: {f['name']} ===")
        context_parts.append(f"{f['content']}")
        context_parts.append(f"=== END SOURCE {i} ===\n")
    
    context_parts.append("=== END OF CONTEXT DOCUMENTS ===\n")
    
    return '\n\n'.join(context_parts)

def get_session_id():
    """Get or create session ID"""
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    return session['session_id']

def get_session_file():
    """Get session file path"""
    session_id = get_session_id()
    return os.path.join(SESSION_FOLDER, f'{session_id}.pkl')

def load_session_data():
    """Load session data from file"""
    session_file = get_session_file()
    if os.path.exists(session_file):
        try:
            with open(session_file, 'rb') as f:
                return pickle.load(f)
        except:
            pass
    return {
        'context_files': [],
        'conversation_history': [],
        'config': DEFAULT_CONFIG.copy(),
        'query_history': [],
        'system_prompt': DEFAULT_SYSTEM_PROMPT
    }

def save_session_data(data):
    """Save session data to file"""
    session_file = get_session_file()
    with open(session_file, 'wb') as f:
        pickle.dump(data, f)

def send_prompt_to_model(user_message, system_prompt, permanent_context, conversation_history, config):
    messages = [{'role': 'system', 'content': system_prompt}]
    
    if permanent_context:
        messages.append({'role': 'system', 'content': permanent_context})
    
    messages.extend(conversation_history)
    messages.append({'role': 'user', 'content': user_message})
    
    payload = {
        "model": config['model_name'],
        "messages": messages,
        "max_tokens": config['max_tokens'],
        "temperature": config['temperature']
    }
    
    start_time = datetime.now()
    timeout = int(os.getenv('REQUEST_TIMEOUT', 3600))
    
    try:
        response = requests.post(
            config['api_url'],
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = response.json()
        result['duration'] = duration
        
        return result
        
    except requests.exceptions.Timeout:
        raise Exception(f"Request timed out after {timeout} seconds")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")

def init_session():
    """Initialize session - now just ensures session_id exists"""
    get_session_id()

@app.route('/')
def index():
    init_session()
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    init_session()
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        content = read_file_content(filepath)
        
        if not content or len(content.strip()) < 10:
            os.remove(filepath)
            return jsonify({'success': False, 'error': 'File appears to be empty'}), 400
        
        content_size = len(content.encode('utf-8'))
        use_server_storage = content_size > STORAGE_THRESHOLD
        
        _, ext = os.path.splitext(filename.lower())
        file_info = {
            'name': filename,
            'content': content if not use_server_storage else None,
            'type': ext[1:] if ext else 'txt',
            'added': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'size': content_size,
            'tokens': count_tokens_estimate(content),
            'stored_on_server': use_server_storage,
            'server_path': filepath if use_server_storage else None
        }
        
        # If using browser storage, delete server file
        if not use_server_storage:
            os.remove(filepath)
        
        data = load_session_data()
        data['context_files'].append(file_info)
        save_session_data(data)
        
        return jsonify({
            'success': True,
            'file': {
                'name': file_info['name'],
                'type': file_info['type'],
                'size': format_size(file_info['size']),
                'tokens': file_info['tokens'],
                'added': file_info['added'],
                'stored_on_server': use_server_storage,
                'content': content if not use_server_storage else None
            }
        })
        
    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    init_session()
    
    request_data = request.json
    user_message = request_data.get('message', '').strip()
    use_conversation_history = request_data.get('use_conversation_history', True)
    
    if not user_message:
        return jsonify({'success': False, 'error': 'Message is empty'}), 400
    
    try:
        data = load_session_data()
        config = data.get('config', DEFAULT_CONFIG)
        system_prompt = data.get('system_prompt', DEFAULT_SYSTEM_PROMPT)
        context_files = data.get('context_files', [])
        
        # Load content from server if needed
        context_files_with_content = []
        for f in context_files:
            if f.get('stored_on_server') and f.get('server_path'):
                # Load from server file
                content = read_file_content(f['server_path'])
                file_copy = f.copy()
                file_copy['content'] = content
                context_files_with_content.append(file_copy)
            else:
                context_files_with_content.append(f)
        
        permanent_context = build_context_section(context_files_with_content)
        
        conversation_history = data.get('conversation_history', []) if use_conversation_history else []
        
        result = send_prompt_to_model(
            user_message,
            system_prompt,
            permanent_context,
            conversation_history,
            config
        )
        
        assistant_response = result['choices'][0]['message']['content']
        
        conversation_history.append({'role': 'user', 'content': user_message})
        conversation_history.append({'role': 'assistant', 'content': assistant_response})
        data['conversation_history'] = conversation_history
        
        query_history = data.get('query_history', [])
        query_history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'prompt': user_message,
            'prompt_tokens': result['usage']['prompt_tokens'],
            'completion_tokens': result['usage']['completion_tokens'],
            'duration': result.get('duration', 0)
        })
        data['query_history'] = query_history
        
        save_session_data(data)
        
        return jsonify({
            'success': True,
            'response': assistant_response,
            'usage': result['usage'],
            'duration': result.get('duration', 0),
            'finish_reason': result['choices'][0]['finish_reason']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/context', methods=['GET'])
def get_context():
    init_session()
    data = load_session_data()
    context_files = data.get('context_files', [])
    
    files = []
    for i, f in enumerate(context_files):
        files.append({
            'index': i,
            'name': f['name'],
            'type': f['type'],
            'size': format_size(f['size']),
            'tokens': f['tokens'],
            'added': f['added'],
            'stored_on_server': f.get('stored_on_server', False)
        })
    
    total_tokens = sum(f['tokens'] for f in context_files)
    total_size = sum(f['size'] for f in context_files)
    
    return jsonify({
        'files': files,
        'total_files': len(context_files),
        'total_tokens': total_tokens,
        'total_size': format_size(total_size)
    })

@app.route('/api/context/<int:index>', methods=['DELETE'])
def remove_context(index):
    init_session()
    data = load_session_data()
    context_files = data.get('context_files', [])
    
    if 0 <= index < len(context_files):
        removed = context_files.pop(index)
        
        # Delete server file if it was stored there
        if removed.get('stored_on_server') and removed.get('server_path'):
            try:
                if os.path.exists(removed['server_path']):
                    os.remove(removed['server_path'])
            except Exception as e:
                print(f"Warning: Could not delete server file: {e}")
        
        data['context_files'] = context_files
        save_session_data(data)
        return jsonify({'success': True, 'removed': removed['name']})
    
    return jsonify({'success': False, 'error': 'Invalid index'}), 400

@app.route('/api/context/clear', methods=['POST'])
def clear_context():
    init_session()
    data = load_session_data()
    context_files = data.get('context_files', [])
    
    # Delete all server-stored files
    for f in context_files:
        if f.get('stored_on_server') and f.get('server_path'):
            try:
                if os.path.exists(f['server_path']):
                    os.remove(f['server_path'])
            except Exception as e:
                print(f"Warning: Could not delete server file: {e}")
    
    data['context_files'] = []
    save_session_data(data)
    return jsonify({'success': True})

@app.route('/api/conversation', methods=['GET'])
def get_conversation():
    init_session()
    data = load_session_data()
    conversation_history = data.get('conversation_history', [])
    
    messages = []
    for i, msg in enumerate(conversation_history):
        messages.append({
            'index': i,
            'role': msg['role'],
            'content': msg['content'],
            'tokens': count_tokens_estimate(msg['content'])
        })
    
    return jsonify({
        'messages': messages,
        'total_messages': len(conversation_history),
        'turns': len(conversation_history) // 2
    })

@app.route('/api/conversation/clear', methods=['POST'])
def clear_conversation():
    init_session()
    data = load_session_data()
    data['conversation_history'] = []
    save_session_data(data)
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    init_session()
    data = load_session_data()
    
    context_files = data.get('context_files', [])
    conversation_history = data.get('conversation_history', [])
    query_history = data.get('query_history', [])
    config = data.get('config', DEFAULT_CONFIG)
    
    # Calculate context tokens (handling server-stored files)
    context_tokens = 0
    for f in context_files:
        if f.get('stored_on_server'):
            context_tokens += f.get('tokens', 0)
        else:
            context_tokens += count_tokens_estimate(f.get('content', ''))
    
    # Calculate conversation tokens
    conv_tokens = sum(count_tokens_estimate(m['content']) for m in conversation_history)
    
    stats = {
        'context_files': len(context_files),
        'context_tokens': context_tokens,
        'conversation_turns': len(conversation_history) // 2,
        'conversation_tokens': conv_tokens,
        'total_tokens': context_tokens + conv_tokens,
        'queries_made': len(query_history),
        'context_limit': config['context_limit'],
        'percentage_used': (context_tokens + conv_tokens) / config['context_limit'] * 100
    }
    
    if query_history:
        stats['total_prompt_tokens'] = sum(h['prompt_tokens'] for h in query_history)
        stats['total_completion_tokens'] = sum(h['completion_tokens'] for h in query_history)
        stats['total_time'] = sum(h['duration'] for h in query_history)
        if stats['total_time'] > 0:
            stats['avg_tokens_per_second'] = stats['total_completion_tokens'] / stats['total_time']
    
    return jsonify(stats)

@app.route('/api/config', methods=['GET', 'POST'])
def get_or_update_config():
    init_session()
    data = load_session_data()
    
    if request.method == 'GET':
        return jsonify(data.get('config', DEFAULT_CONFIG))
    
    request_data = request.json
    config = data.get('config', DEFAULT_CONFIG.copy())
    
    if 'max_tokens' in request_data:
        config['max_tokens'] = int(request_data['max_tokens'])
    if 'temperature' in request_data:
        config['temperature'] = float(request_data['temperature'])
    if 'context_limit' in request_data:
        config['context_limit'] = int(request_data['context_limit'])
    
    data['config'] = config
    save_session_data(data)
    return jsonify({'success': True, 'config': config})

@app.route('/api/system-prompt', methods=['GET', 'POST'])
def get_or_update_system_prompt():
    init_session()
    data = load_session_data()
    
    if request.method == 'GET':
        return jsonify({'prompt': data.get('system_prompt', DEFAULT_SYSTEM_PROMPT)})
    
    request_data = request.json
    prompt = request_data.get('prompt', '').strip()
    
    if not prompt:
        return jsonify({'success': False, 'error': 'Prompt is empty'}), 400
    
    data['system_prompt'] = prompt
    save_session_data(data)
    return jsonify({'success': True})

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': 'File too large'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"\n{'='*70}")
    print(f"Starting server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Debug: {debug}")
    print(f"  Model API: {DEFAULT_CONFIG['api_url']}")
    print(f"{'='*70}\n")
    
    app.run(host=host, port=port, debug=debug)
