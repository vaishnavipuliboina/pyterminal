import os
import shutil
import psutil
import subprocess
import sys
import atexit

# ---------------------------
# Natural Language Parser
# ---------------------------

def parse_natural_language(command):
    """
    Convert natural language commands to terminal commands.
    Examples:
    - "create folder test" -> "mkdir test"
    - "delete file example.txt" -> "rm example.txt"
    - "list files" -> "ls"
    - "show current directory" -> "pwd"
    """
    command_lower = command.lower().strip()
    
    # Define natural language mappings
    mappings = {
        # Directory operations
        "create folder": "mkdir",
        "make folder": "mkdir",
        "new folder": "mkdir",
        "delete folder": "rm",
        "remove folder": "rm",
        "list folders": "ls",
        "list files": "ls",
        "show files": "ls",
        "show folders": "ls",
        "list directory": "ls",
        "show directory": "ls",
        
        # File operations
        "delete file": "rm",
        "remove file": "rm",
        "erase file": "rm",
        
        # Navigation
        "go to": "cd",
        "change to": "cd",
        "navigate to": "cd",
        "enter": "cd",
        "show current directory": "pwd",
        "where am i": "pwd",
        "current location": "pwd",
        
        # System info
        "system info": "sysinfo",
        "show system": "sysinfo",
        "computer info": "sysinfo",
        "system status": "sysinfo",
        
        # Exit commands
        "close": "exit",
        "end": "exit",
        "stop": "exit",
        "finish": "exit",
    }
    
    # Check for exact matches first
    for natural_cmd, terminal_cmd in mappings.items():
        if command_lower.startswith(natural_cmd):
            # Extract the remaining part after the natural command
            remaining = command[len(natural_cmd):].strip()
            if remaining:
                return f"{terminal_cmd} {remaining}"
            else:
                return terminal_cmd
    
    # Check for partial matches and handle common patterns
    words = command_lower.split()
    
    # Handle "create" commands
    if len(words) >= 2 and words[0] == "create":
        if words[1] in ["folder", "directory", "dir"]:
            folder_name = " ".join(words[2:])
            return f"mkdir {folder_name}"
        elif words[1] in ["file"]:
            file_name = " ".join(words[2:])
            return f"touch {file_name}"
    
    # Handle "delete" commands
    if len(words) >= 2 and words[0] in ["delete", "remove", "erase"]:
        if words[1] in ["folder", "directory", "dir"]:
            folder_name = " ".join(words[2:])
            return f"rm -rf {folder_name}"
        elif words[1] in ["file"]:
            file_name = " ".join(words[2:])
            return f"rm {file_name}"
        else:
            # If no specific type mentioned, try to determine from context
            target = " ".join(words[1:])
            return f"rm {target}"
    
    # Handle "list" commands
    if len(words) >= 1 and words[0] in ["list", "show", "display"]:
        if len(words) > 1:
            target = " ".join(words[1:])
            return f"ls {target}"
        else:
            return "ls"
    
    # Handle "go" commands
    if len(words) >= 2 and words[0] in ["go", "navigate", "change"]:
        if words[1] in ["to"] and len(words) > 2:
            target = " ".join(words[2:])
            return f"cd {target}"
        elif len(words) > 1:
            target = " ".join(words[1:])
            return f"cd {target}"
    
    # If no match found, return original command
    return command

# ---------------------------
# Command history & tab completion
# ---------------------------

# Determine platform and setup readline accordingly
WINDOWS = sys.platform.startswith('win')

if WINDOWS:
    try:
        import pyreadline3 as readline
        # pyreadline3 has different API, so we'll handle it separately
        READLINE_AVAILABLE = True
        READLINE_TYPE = 'pyreadline3'
    except ImportError:
        try:
            import readline
            READLINE_AVAILABLE = True
            READLINE_TYPE = 'readline'
        except ImportError:
            READLINE_AVAILABLE = False
            READLINE_TYPE = None
else:
    try:
        import readline
        READLINE_AVAILABLE = True
        READLINE_TYPE = 'readline'
    except ImportError:
        READLINE_AVAILABLE = False
        READLINE_TYPE = None

# Tab completion setup
COMMANDS = ["ls", "cd", "pwd", "mkdir", "touch", "rm", "sysinfo", "exit", "quit"]
NATURAL_COMMANDS = [
    "create folder", "make folder", "new folder", "delete folder", "remove folder",
    "list folders", "list files", "show files", "show folders", "list directory", "show directory",
    "delete file", "remove file", "erase file",
    "go to", "change to", "navigate to", "enter",
    "show current directory", "where am i", "current location",
    "system info", "show system", "computer info", "system status",
    "close", "end", "stop", "finish"
]

def completer(text, state):
    # Combine regular commands and natural language commands
    all_commands = COMMANDS + NATURAL_COMMANDS
    options = [cmd for cmd in all_commands if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    return None

# Setup readline functionality based on available module
if READLINE_AVAILABLE:
    if READLINE_TYPE == 'pyreadline3':
        # pyreadline3 setup - check for available methods
        if hasattr(readline, 'set_completer'):
            readline.set_completer(completer)
        elif hasattr(readline, 'SetCompleter'):
            readline.SetCompleter(completer)
        
        if hasattr(readline, 'parse_and_bind'):
            readline.parse_and_bind("tab: complete")
        elif hasattr(readline, 'ParseAndBind'):
            readline.ParseAndBind("tab: complete")
    else:
        # Standard readline setup
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

# Command history file
HISTFILE = os.path.join(os.path.expanduser("~"), ".terminal_history")

def load_history():
    """Load command history from file"""
    if READLINE_AVAILABLE and READLINE_TYPE == 'readline':
        try:
            readline.read_history_file(HISTFILE)
        except FileNotFoundError:
            pass  # History file doesn't exist yet, that's okay
    elif READLINE_AVAILABLE and READLINE_TYPE == 'pyreadline3':
        # pyreadline3 might have different history methods
        if hasattr(readline, 'read_history_file'):
            try:
                readline.read_history_file(HISTFILE)
            except (FileNotFoundError, AttributeError):
                pass

def save_history():
    """Save command history to file"""
    if READLINE_AVAILABLE and READLINE_TYPE == 'readline':
        try:
            readline.write_history_file(HISTFILE)
        except Exception:
            pass  # Ignore errors when saving history
    elif READLINE_AVAILABLE and READLINE_TYPE == 'pyreadline3':
        # pyreadline3 might have different history methods
        if hasattr(readline, 'write_history_file'):
            try:
                readline.write_history_file(HISTFILE)
            except Exception:
                pass

# ---------------------------
# Main terminal loop
# ---------------------------
def main():
    # Load command history
    load_history()
    
    # Register function to save history on exit
    atexit.register(save_history)
    
    while True:
        try:
            cwd = os.getcwd()
            cmd_input = input(f"{cwd}$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting terminal...")
            break

        if not cmd_input:
            continue

        # Parse natural language command first
        parsed_command = parse_natural_language(cmd_input)
        
        # Show what command was parsed (optional - can be commented out)
        if parsed_command != cmd_input:
            print(f"→ {parsed_command}")
        
        parts = parsed_command.split()
        cmd = parts[0]
        args = parts[1:]

        # Exit
        if cmd in ("exit", "quit"):
            print("Goodbye!")
            break

        # pwd
        elif cmd == "pwd":
            print(os.getcwd())

        # ls
        elif cmd == "ls":
            target = args[0] if args else "."
            if os.path.isdir(target):
                for item in os.listdir(target):
                    print(item)
            else:
                print(f"No such directory: {target}")

        # cd
        elif cmd == "cd":
            if not args:
                print("Usage: cd <directory>")
            else:
                target = " ".join(args)  # combine multiple words
                try:
                    os.chdir(target)
                except FileNotFoundError:
                    print(f"No such directory: {target}")

        # mkdir
        elif cmd == "mkdir":
            if not args:
                print("Usage: mkdir <directory>")
            else:
                folder_name = " ".join(args)  # combine multiple words
                try:
                    os.mkdir(folder_name)
                    print(f"Directory created: {folder_name}")
                except FileExistsError:
                    print(f"Directory already exists: {folder_name}")
                except Exception as e:
                    print(f"Error creating directory: {e}")

        # touch (create empty file)
        elif cmd == "touch":
            if not args:
                print("Usage: touch <file>")
            else:
                file_name = " ".join(args)  # combine multiple words
                try:
                    with open(file_name, 'a'):
                        pass  # Create empty file
                    print(f"File created: {file_name}")
                except Exception as e:
                    print(f"Error creating file: {e}")

        # rm
        elif cmd == "rm":
            if not args:
                print("Usage: rm <file_or_directory>")
            else:
                target = " ".join(args)  # combine multiple words
                try:
                    if os.path.isfile(target):
                        os.remove(target)
                        print(f"File removed: {target}")
                    elif os.path.isdir(target):
                        shutil.rmtree(target)
                        print(f"Directory removed: {target}")
                    else:
                        print(f"Not found: {target}")
                except Exception as e:
                    print(f"Error removing {target}: {e}")

        # System monitor
        elif cmd == "sysinfo":
            print(f"CPU Usage: {psutil.cpu_percent()}%")
            print(f"Memory Usage: {psutil.virtual_memory().percent}%")

        # Fallback system command
        else:
            try:
                subprocess.run(cmd_input, shell=True)
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
