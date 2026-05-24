import socket
import threading
import paramiko
import ollama

# Load the host key we just generated
HOST_KEY = paramiko.RSAKey(filename='test_rsa.key')

# Strict instructions for Llama3.2:1b to act like an Ubuntu server terminal
SYSTEM_PROMPT = """
You are a medium-interaction honeypot emulating an Ubuntu 22.04 LTS server terminal.
- Treat all inputs as shell commands executed by a root user.
- Provide ONLY the realistic Linux command-line output.
- Do NOT explain the commands, do NOT use markdown formatting (like ```bash), and do NOT apologize.
- If a command is missing or invalid, output the exact Ubuntu bash error (e.g., 'bash: command not found').
- Maintain a fake filesystem context based on history.
"""

class HoneypotSSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    # Trap door: Accept ANY username and password the attacker throws at us!
    def check_auth_password(self, username, password):
        print(f"[!] BRUTE FORCE ATTEMPT - Username: {username} | Password: {password}")
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def handle_attacker(client_socket):
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        server = HoneypotSSHServer()
        transport.start_server(server=server)
        
        channel = transport.accept(10)
        if channel is None:
            return

        server.event.wait(10)
        if not server.event.is_set():
            return

        # Welcome banner to fool automated bots and script kiddies
        channel.send("Welcome to Ubuntu 22.04.2 LTS (GNU/Linux 5.15.0-72-generic x86_64)\r\n\r\n")
        
        # Keep track of this specific attacker's session history
        history = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        while True:
            channel.send("root@ubuntu-srv:~# ")
            command = ""
            
            # Read character by character until the attacker hits Enter
            while True:
                char = channel.recv(1).decode('utf-8', errors='ignore')
                if char == '\r' or char == '\n':
                    channel.send("\r\n")
                    break
                elif char == '\x7f': # Handle backspace cleanly
                    if len(command) > 0:
                        command = command[:-1]
                        channel.send("\b \b")
                else:
                    command += char
                    channel.send(char) # Echo character back to attacker's screen

            command = command.strip()
            if command.lower() in ['exit', 'logout']:
                channel.send("logout\r\nConnection closed.\r\n")
                break
                
            if not command:
                continue

            print(f"[->] Attacker executed: {command}")

            # Send command + history to Llama 3 via Ollama
            history.append({"role": "user", "content": command})
            
            try:
                response = ollama.chat(model='llama3.2:1b', messages=history)
                ai_output = response['message']['content'].strip()
                
                # Append AI response to maintain stateful filesystem memory
                history.append({"role": "assistant", "content": ai_output})
                
                # Format raw text newlines for SSH compatibility (\r\n)
                formatted_output = ai_output.replace('\n', '\r\n') + "\r\n"
                channel.send(formatted_output)
                
            except Exception as e:
                print(f"[-] Ollama Error: {e}")
                channel.send("bash: internal error processing command\r\n")

    except Exception as e:
        print(f"[-] Connection error: {e}")
    finally:
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 2222)) # Listening on port 2222
    server_socket.listen(100)
    print("[*] AI Honeypot listening for hackers on port 2222...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[+] Incoming connection from {addr[0]}:{addr[1]}")
        threading.Thread(target=handle_attacker, args=(client_socket,)).start()

if __name__ == "__main__":
    main()
