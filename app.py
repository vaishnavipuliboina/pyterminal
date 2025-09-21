from flask import Flask, render_template, request, jsonify
import os
import shutil
import psutil
import subprocess
import sys
import json
from datetime import datetime

app = Flask(__name__)

# Import the natural language parser from terminal.py
from terminal import parse_natural_language

# Global variable to track current working directory
current_dir = os.getcwd()

def execute_command(command):
    """Execute a command and return the output"""
    global current_dir
    
    # Parse natural language command first
    parsed_command = parse_natural_language(command)
    
    parts = parsed_command.split()
    cmd = parts[0] if parts else ""
    args = parts[1:] if len(parts) > 1 else []
    
    output_lines = []
    
    try:
        # Exit
        if cmd in ("exit", "quit"):
            return {"output": "Goodbye!", "parsed_command": parsed_command, "cwd": current_dir}
        
        # pwd
        elif cmd == "pwd":
            output_lines.append(current_dir)
        
        # ls
        elif cmd == "ls":
            target = args[0] if args else "."
            target_path = os.path.join(current_dir, target) if not os.path.isabs(target) else target
            
            if os.path.isdir(target_path):
                items = os.listdir(target_path)
                for item in items:
                    item_path = os.path.join(target_path, item)
                    if os.path.isdir(item_path):
                        output_lines.append(f"📁 {item}/")
                    else:
                        output_lines.append(f"📄 {item}")
            else:
                output_lines.append(f"No such directory: {target}")
        
        # cd
        elif cmd == "cd":
            if not args:
                output_lines.append("Usage: cd <directory>")
            else:
                target = " ".join(args)  # combine multiple words
                try:
                    if not os.path.isabs(target):
                        new_dir = os.path.join(current_dir, target)
                    else:
                        new_dir = target
                    
                    if os.path.isdir(new_dir):
                        current_dir = os.path.abspath(new_dir)
                        output_lines.append(f"Changed to: {current_dir}")
                    else:
                        output_lines.append(f"No such directory: {target}")
                except Exception as e:
                    output_lines.append(f"Error: {e}")
        
        # mkdir
        elif cmd == "mkdir":
            if not args:
                output_lines.append("Usage: mkdir <directory>")
            else:
                folder_name = " ".join(args)  # combine multiple words
                try:
                    dir_path = os.path.join(current_dir, folder_name)
                    os.mkdir(dir_path)
                    output_lines.append(f"Directory created: {folder_name}")
                except FileExistsError:
                    output_lines.append(f"Directory already exists: {folder_name}")
                except Exception as e:
                    output_lines.append(f"Error: {e}")
        
        # touch (create empty file)
        elif cmd == "touch":
            if not args:
                output_lines.append("Usage: touch <file>")
            else:
                file_name = " ".join(args)  # combine multiple words
                try:
                    file_path = os.path.join(current_dir, file_name)
                    with open(file_path, 'a'):
                        pass  # Create empty file
                    output_lines.append(f"File created: {file_name}")
                except Exception as e:
                    output_lines.append(f"Error creating file: {e}")
        
        # rm
        elif cmd == "rm":
            if not args:
                output_lines.append("Usage: rm <file_or_directory>")
            else:
                target = " ".join(args)  # combine multiple words
                target_path = os.path.join(current_dir, target) if not os.path.isabs(target) else target
                
                try:
                    if os.path.isfile(target_path):
                        os.remove(target_path)
                        output_lines.append(f"File removed: {target}")
                    elif os.path.isdir(target_path):
                        shutil.rmtree(target_path)
                        output_lines.append(f"Directory removed: {target}")
                    else:
                        output_lines.append(f"Not found: {target}")
                except Exception as e:
                    output_lines.append(f"Error removing {target}: {e}")
        
        # System monitor
        elif cmd == "sysinfo":
            output_lines.append(f"🖥️  CPU Usage: {psutil.cpu_percent()}%")
            output_lines.append(f"💾 Memory Usage: {psutil.virtual_memory().percent}%")
            output_lines.append(f"💽 Disk Usage: {psutil.disk_usage('/').percent}%")
            output_lines.append(f"🌐 Network: {len(psutil.net_connections())} active connections")
        
        # Fallback system command
        else:
            try:
                # Change to current directory before executing
                result = subprocess.run(
                    parsed_command, 
                    shell=True, 
                    cwd=current_dir,
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                if result.stdout:
                    output_lines.extend(result.stdout.strip().split('\n'))
                if result.stderr:
                    output_lines.extend([f"Error: {line}" for line in result.stderr.strip().split('\n')])
                    
            except subprocess.TimeoutExpired:
                output_lines.append("Command timed out after 10 seconds")
            except Exception as e:
                output_lines.append(f"Error: {e}")
    
    except Exception as e:
        output_lines.append(f"Unexpected error: {e}")
    
    return {
        "output": "\n".join(output_lines),
        "parsed_command": parsed_command if parsed_command != command else None,
        "cwd": current_dir,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

@app.route('/')
def index():
    """Serve the main terminal interface"""
    return render_template('terminal.html')

@app.route('/execute', methods=['POST'])
def execute():
    """Execute a command and return the result"""
    data = request.get_json()
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({"error": "No command provided"})
    
    result = execute_command(command)
    return jsonify(result)

@app.route('/status')
def status():
    """Get current status information"""
    return jsonify({
        "cwd": current_dir,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == '__main__':
    print("🚀 Starting Web Terminal...")
    print(f"📁 Current directory: {current_dir}")
    print("🌐 Open your browser and go to: http://127.0.0.1:5000")
    print("💡 Try commands like:")
    print("   - ls")
    print("   - create folder MyProject")
    print("   - sysinfo")
    print("   - go to Desktop")
    print("\n" + "="*50)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
