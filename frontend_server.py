#!/usr/bin/env python3
"""
Simple HTTP server for MommyShops frontend
Serves the HTML frontend on port 10888
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

LANDING_PATH = Path("frontend/landing/index.html")
APP_PATH = Path("frontend.html")
API_TEST_PATH = Path("api_test.html")


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve HTML files with proper MIME types"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def serve_file(self, file_path):
        """Serve a file directly from the given path"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            if file_path.suffix == '.html':
                content_type = 'text/html; charset=utf-8'
            elif file_path.suffix == '.css':
                content_type = 'text/css'
            elif file_path.suffix == '.js':
                content_type = 'application/javascript'
            elif file_path.suffix == '.svg':
                content_type = 'image/svg+xml'
            else:
                content_type = 'application/octet-stream'
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error serving file: {e}")
    
    def get_file_for_path(self):
        """Determine which file to serve for the current path"""
        # Serve landing page as entry point
        if self.path in {'/', '/index.html'}:
            if LANDING_PATH.exists():
                return LANDING_PATH
            else:
                # Fallback to app if landing page doesn't exist
                return APP_PATH
        # Serve app interface
        elif self.path in {'/app', '/app/', '/app/index.html'}:
            return APP_PATH
        # Serve API test page
        elif self.path == '/test':
            if API_TEST_PATH.exists():
                return API_TEST_PATH
            else:
                return None
        
        # Handle static assets (CSS, JS, images, etc.)
        if self.path.startswith('/frontend/'):
            # Try to serve from frontend directory
            asset_path = Path(self.path.lstrip('/'))
            if asset_path.exists() and asset_path.is_file():
                return asset_path
        
        return None
    
    def do_HEAD(self):
        """Handle HEAD requests"""
        file_to_serve = self.get_file_for_path()
        
        if file_to_serve and file_to_serve.exists():
            try:
                # Send headers only for HEAD request
                content_type = 'text/html; charset=utf-8'
                if file_to_serve.suffix == '.css':
                    content_type = 'text/css'
                elif file_to_serve.suffix == '.js':
                    content_type = 'application/javascript'
                elif file_to_serve.suffix == '.svg':
                    content_type = 'image/svg+xml'
                
                size = file_to_serve.stat().st_size
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(size))
                self.end_headers()
                return
            except Exception as e:
                self.send_error(500, f"Error: {e}")
                return
        elif file_to_serve:
            self.send_error(404, f"File not found: {file_to_serve}")
            return
        
        # Default behavior for other paths
        return super().do_HEAD()
    
    def do_GET(self):
        """Handle GET requests"""
        file_to_serve = self.get_file_for_path()
        
        # If we determined a file to serve, serve it directly
        if file_to_serve and file_to_serve.exists():
            self.serve_file(file_to_serve)
            return
        elif file_to_serve:
            self.send_error(404, f"File not found: {file_to_serve}")
            return
        
        # Default behavior for other paths - try to serve as static file
        return super().do_GET()

def start_frontend_server(port=10888):
    """Start the frontend server"""
    
    # Only APP_PATH is required, others are optional
    required_files = [APP_PATH]
    missing_files = [path for path in required_files if not path.exists()]
    if missing_files:
        print("❌ Error: required frontend assets not found:")
        for path in missing_files:
            print(f"   - {path}")
        print("Please make sure the static files are present in the project directory.")
        return False
    
    # Warn about optional files
    optional_files = [LANDING_PATH, API_TEST_PATH]
    missing_optional = [path for path in optional_files if not path.exists()]
    if missing_optional:
        print("⚠️  Warning: optional frontend assets not found (server will still work):")
        for path in missing_optional:
            print(f"   - {path}")
    
    try:
        # Create server
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print("🚀 MommyShops Frontend Server Starting...")
            print("=" * 50)
            print(f"📱 Landing URL:  http://localhost:{port}/")
            print(f"🌐 App URL:      http://localhost:{port}/app")
            print(f"🧪 API tester:  http://localhost:{port}/test")
            print(f"📁 Serving files from: {os.getcwd()}")
            print("=" * 50)
            print("✨ Features:")
            print("   📸 Image upload and analysis")
            print("   📝 Text ingredient analysis")
            print("   🧪 Safety scoring")
            print("   💡 Personalized recommendations")
            print("=" * 50)
            print("🔗 Backend API: http://localhost:8000")
            print("📚 API Docs: http://localhost:8000/docs")
            print("=" * 50)
            print("Press Ctrl+C to stop the server")
            print()
            
            # Try to open browser automatically
            try:
                webbrowser.open(f'http://localhost:{port}')
                print("🌐 Browser opened automatically!")
            except:
                print("⚠️  Could not open browser automatically")
                print(f"   Please open http://localhost:{port} manually")
            
            print()
            print("🟢 Server is running...")
            
            # Start serving
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Error: Port {port} is already in use!")
            print(f"   Try a different port or stop the process using port {port}")
        else:
            print(f"❌ Error starting server: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True

def main():
    """Main function"""
    port = 10888
    
    # Check for custom port argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number. Using default port 10888")
    
    print("🧴 MommyShops Frontend Server")
    print("=" * 30)
    
    success = start_frontend_server(port)
    
    if success:
        print("✅ Server stopped successfully")
    else:
        print("❌ Server failed to start")
        sys.exit(1)

if __name__ == "__main__":
    main()
