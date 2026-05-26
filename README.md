## HoneyLlama: Smart AI-Driven SSH Honeypot

  Standard honeypots usually rely on rigid, pre-written text scripts that automated botnets or smart attackers spot right away. I built HoneyLlama on Kali Linux to fix that problem by introducing dynamic deception.

Instead of saying "Command not found," HoneyLlama takes whatever the attacker types, runs it through a local, completely isolated Llama 3.2 (1B) model via Ollama, and serves a hyper-realistic terminal response on the fly.

## Live Execution (How it Works)

  Here is a side-by-side look at the system trapping an active attacker loop:

Left Terminal (Defender Logs): Runs a custom Python socket server (app.py) listening on port 2222. It instantly waves in brute-force attempts (root:root) and secretly logs every command without the attacker ever knowing.

Right Terminal (Attacker Perspective): Shows the attacker verifying local models with "ollama list", then connecting via SSH. They are completely contained inside a dynamic, AI-generated Ubuntu 22.04 LTS environment that tricks them into thinking they have a real shell.

## Core Features

  Instant Access Trap: Built using Python and Paramiko to drop traditional handshake restrictions, immediately trapping bots regardless of what username/password they try.

Persistent Session Memory: Programmed a rolling state array in Python so the local AI remembers context over time. If an attacker types "mkdir tools" and then "cd tools", the AI tracks the directory state flawlessly.

Local & Isolated Brain: Backed entirely by Ollama, running the lightweight Llama 3.2 (1B) model 100% locally on the virtual machine. Zero cloud costs, zero data leaks.

AI-Assisted Development: Designed the framework myself, while using generative AI as an advanced technical mentor to help debug socket behaviors and streamline prompt engineering limits.

## Tech Stack

Python, Paramiko, Ollama, Llama 3.2 (1B), Network Security, Defensive Deception (Blue Teaming), Linux Administration
