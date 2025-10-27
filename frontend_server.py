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

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve HTML files with proper MIME types"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Serve frontend.html as the main page
        if self.path == '/' or self.path == '/index.html':
            self.path = '/frontend.html'
        # Serve API test page
        elif self.path == '/test':
            self.path = '/api_test.html'
        return super().do_GET()

def start_frontend_server(port=10888):
    """Start the frontend server"""
    
    # Check if frontend.html exists
    if not os.path.exists('frontend.html'):
        print("❌ Error: frontend.html not found!")
        print("Please make sure frontend.html is in the current directory.")
        return False
    
    try:
        # Create server
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print("🚀 MommyShops Frontend Server Starting...")
            print("=" * 50)
            print(f"📱 Frontend URL: http://localhost:{port}")
            print(f"📁 Serving files from: {os.getcwd()}")
            print(f"🌐 Main page: http://localhost:{port}/frontend.html")
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
