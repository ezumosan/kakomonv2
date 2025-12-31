import http.server
import socketserver
import json
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from email.parser import BytesParser
from email.policy import default

# Configure logging
logging.basicConfig(
    filename='server_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

PORT = 8080
UPLOAD_DIR = 'public/uploads'
DATA_FILE = 'data.json'

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
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
                if fname.startswith('.'): continue
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
        if self.path == '/':
            self.path = '/public/index.html'
        elif self.path.startswith('/public/'):
            pass # already correct
        else:
            if not self.path.startswith('/api'):
                self.path = '/public' + self.path

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/api/upload':
            try:
                content_length = int(self.headers['Content-Length'])
                logging.info(f"Receiving upload. Content-Length: {content_length}")
                logging.debug(f"Headers: {self.headers}")
                
                body = self.rfile.read(content_length)
                logging.info("Body read successfully")
                
                # Construct a minimal message to parse headers + body
                headers = b'Content-Type: ' + self.headers['Content-Type'].encode('utf-8') + b'\r\n\r\n'
                msg = BytesParser(policy=default).parsebytes(headers + body)
                
                file_data = None
                filename = None
                tags = []
                
                if msg.is_multipart():
                    logging.info("Message is multipart")
                    for part in msg.iter_parts():
                        name = part.get_param('name', header='content-disposition')
                        logging.debug(f"Processing part: name={name}")
                        
                        if name == 'file':
                            filename = part.get_filename()
                            logging.debug(f"Found file part: filename={filename}")
                            if filename:
                                file_data = part.get_payload(decode=True)
                        elif name == 'tags':
                            tags_payload = part.get_payload(decode=True).decode('utf-8')
                            tags = [t.strip() for t in tags_payload.split(',')] if tags_payload else []
                            logging.debug(f"Found tags: {tags}")
                else:
                    logging.error("Message is NOT multipart")

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
                else:
                    logging.error("Missing file_data or filename")

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
