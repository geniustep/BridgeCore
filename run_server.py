#!/usr/bin/env python3
"""
Script to start BridgeCore server
"""
import subprocess
import sys
import os
import time
import signal

def kill_existing():
    """Kill existing uvicorn processes"""
    try:
        os.system('pkill -9 -f "uvicorn.*app.main:app" 2>/dev/null')
        time.sleep(2)
        print("✅ Stopped existing server processes")
    except Exception as e:
        print(f"⚠️  Error stopping processes: {e}")

def start_server():
    """Start the server"""
    log_file = open('logs/server.log', 'a')
    
    try:
        proc = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 
             'app.main:app', 
             '--host', '0.0.0.0', 
             '--port', '8000', 
             '--reload'],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd='/opt/BridgeCore'
        )
        
        print(f"✅ Server started with PID: {proc.pid}")
        print("📝 Logs: tail -f /opt/BridgeCore/logs/server.log")
        print("🌐 Server: http://0.0.0.0:8000")
        print("\nPress Ctrl+C to stop the server")
        
        # Wait for process
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            proc.terminate()
            proc.wait()
            print("✅ Server stopped")
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
    finally:
        log_file.close()

if __name__ == "__main__":
    kill_existing()
    start_server()




