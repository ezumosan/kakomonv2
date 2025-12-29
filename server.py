import http.server
import socketserver
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from email.parser import BytesParser
from email.policy import default

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
                
            # Scan directory to sync (in case files were deleted manually)
            real_files = set(os.listdir(UPLOAD_DIR))
            
            # Clean up data for missing files
            for fname in list(file_data.keys()):
                if fname not in real_files:
                    del file_data[fname]
            
            # Save cleaned data
            with open(DATA_FILE, 'w') as f:
                json.dump(file_data, f)
            
            # Build response list
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
            
            # Sort by date
            files.sort(key=lambda x: x['date'], reverse=True)
            self.wfile.write(json.dumps(files).encode())
            return

        # Serve Static Files
        # Redirect root to index.php (or index.html if we rename it)
        if self.path == '/':
            self.path = '/public/index.html'
        elif self.path.startswith('/public/'):
            pass # already correct
        else:
            # Map top-level requests to public/ folder
            if not self.path.startswith('/api'):
                self.path = '/public' + self.path

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/api/upload':
            try:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                
                # Construct a minimal message to parse headers + body
                # We need to prepend the Content-Type header so BytesParser knows how to split it
                headers = b'Content-Type: ' + self.headers['Content-Type'].encode('utf-8') + b'\r\n\r\n'
                msg = BytesParser(policy=default).parsebytes(headers + body)
                
                file_data = None
                filename = None
                tags = []
                
                if msg.is_multipart():
                    for part in msg.iter_parts():
                        # shipping content-disposition
                        cdisp = part.get('Content-Disposition')
                        if cdisp is None:
                            continue
                            
                        # Parse content-disposition manually or via email params
                        # part.get_params() returns list of (name, value) from header
                        # But simpler to look at accessible properties if policy=default
                        
                        name = part.get_param('name', header='content-disposition')
                        
                        if name == 'file':
                            filename = part.get_filename()
                            if filename:
                                file_data = part.get_payload(decode=True)
                        elif name == 'tags':
                            # payload is bytes, decode to string
                            tags_payload = part.get_payload(decode=True).decode('utf-8')
                            tags = [t.strip() for t in tags_payload.split(',')] if tags_payload else []

                if file_data and filename:
                    filename = os.path.basename(filename)
                    target_path = os.path.join(UPLOAD_DIR, filename)
                    
                    # Avoid overwrite
                    if os.path.exists(target_path):
                        name, ext = os.path.splitext(filename)
                        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
                        target_path = os.path.join(UPLOAD_DIR, filename)

                    with open(target_path, 'wb') as f:
                        f.write(file_data)
                    
                    # Update metadata
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
                print(f"Error handling upload: {e}")
                pass

            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "message": "Upload failed"}).encode())
            return

with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
