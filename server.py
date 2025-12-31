import http.server
import http.cookies
import socketserver
import json
import os
import shutil
import logging
import uuid
from pathlib import Path
from datetime import datetime
from email.parser import BytesParser
from email.policy import default

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_debug.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

PORT = 8090
UPLOAD_DIR = 'public/uploads'
DATA_FILE = 'data.json'
PASSWORD = "2026"
SESSION_COOKIE_NAME = "kakomon_session"
SESSIONS = set()

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def is_authenticated(self):
        if "Cookie" in self.headers:
            c = http.cookies.SimpleCookie(self.headers["Cookie"])
            if SESSION_COOKIE_NAME in c:
                return c[SESSION_COOKIE_NAME].value in SESSIONS
        return False

    def do_GET(self):
        # Public paths
        public_paths = ['/public/login.html', '/api/login']
        is_public_resource = self.path.startswith('/public/css/') or self.path.startswith('/public/js/') or self.path.startswith('/css/') or self.path.startswith('/js/')
        
        # Check auth
        if not self.is_authenticated():
            # Allow public assets and login page
            if self.path not in public_paths and not is_public_resource and self.path != '/login.html':
                 # Redirect to login
                 self.send_response(302)
                 self.send_header('Location', '/public/login.html')
                 self.end_headers()
                 return
        
        # Serve API: List Files
        if self.path == '/api/files':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            files = []
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    try:
                        file_data = json.load(f)
                    except json.JSONDecodeError:
                        file_data = {}
            else:
                 file_data = {}
                
            real_files = set(os.listdir(UPLOAD_DIR))
            
            for fname in list(file_data.keys()):
                if fname not in real_files:
                    del file_data[fname]
            
            with open(DATA_FILE, 'w') as f:
                json.dump(file_data, f)
            
            for fname in real_files:
                if fname.startswith('.') or fname.endswith('.py') or fname.endswith('.log') or fname == 'data.json': continue
                fpath = os.path.join(UPLOAD_DIR, fname)
                try:
                    stat = os.stat(fpath)
                    meta = file_data.get(fname, {"tags": []})
                    
                    files.append({
                        "name": fname,
                        "size": stat.st_size,
                        "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "tags": meta.get("tags", [])
                    })
                except OSError:
                    continue
            
            files.sort(key=lambda x: x['date'], reverse=True)
            self.wfile.write(json.dumps(files).encode())
            return

        # Serve Static Files
        if self.path == '/' or self.path == '/index.html':
            self.path = '/public/index.html'
        elif self.path == '/login.html':
            self.path = '/public/login.html'
        
        if self.path.startswith('/public/'):
            pass # already correct
        elif not self.path.startswith('/api'):
             self.path = '/public' + self.path

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        logging.info(f"POST request to {self.path}")
        logging.debug(f"Headers: {self.headers}")

        if self.path == '/api/login':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                if data.get('password') == PASSWORD:
                    session_id = str(uuid.uuid4())
                    SESSIONS.add(session_id)
                    
                    self.send_response(200)
                    c = http.cookies.SimpleCookie()
                    c[SESSION_COOKIE_NAME] = session_id
                    c[SESSION_COOKIE_NAME]["path"] = "/"
                    self.send_header('Set-Cookie', c.output(header='').strip())
                    self.end_headers()
                    self.wfile.write(b'OK')
                    return
            except Exception:
                pass
            
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return

        if not self.is_authenticated():
             self.send_response(401)
             self.end_headers()
             return

        if self.path == '/api/upload':
            try:
                content_length = int(self.headers['Content-Length'])
                logging.info(f"Receiving upload. Content-Length: {content_length}")
                
                body = self.rfile.read(content_length)
                
                headers = b'Content-Type: ' + self.headers['Content-Type'].encode('utf-8') + b'\r\n\r\n'
                msg = BytesParser(policy=default).parsebytes(headers + body)
                
                file_data = None
                filename = None
                tags = []
                
                if msg.is_multipart():
                    for part in msg.iter_parts():
                        name = part.get_param('name', header='content-disposition')
                        
                        if name == 'file':
                            filename = part.get_filename()
                            if filename:
                                file_data = part.get_payload(decode=True)
                        elif name == 'tags':
                            tags_payload = part.get_payload(decode=True).decode('utf-8')
                            tags = [t.strip() for t in tags_payload.split(',')] if tags_payload else []

                if file_data and filename:
                    filename = os.path.basename(filename)
                    target_path = os.path.join(UPLOAD_DIR, filename)
                    
                    if os.path.exists(target_path):
                        name, ext = os.path.splitext(filename)
                        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
                        target_path = os.path.join(UPLOAD_DIR, filename)

                    with open(target_path, 'wb') as f:
                        f.write(file_data)
                    
                    logging.info(f"File saved to {target_path}")

                    current_data = {}
                    if os.path.exists(DATA_FILE):
                         with open(DATA_FILE, 'r') as f:
                            try:
                                current_data = json.load(f)
                            except json.JSONDecodeError:
                                pass
                                
                    current_data[filename] = {"tags": tags}
                    
                    with open(DATA_FILE, 'w') as f:
                        json.dump(current_data, f)

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "file": filename}).encode())
                    return

            except Exception as e:
                logging.exception("Exception in do_POST")
                pass

            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "message": "Upload failed"}).encode())
            return

with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
