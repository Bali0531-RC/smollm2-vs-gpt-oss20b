import subprocess
from datetime import datetime
import re

BIG = "gpt-oss:20b"
SMOL = "smollm2:135M"

TURNS = 10  # hány forduló legyen

# kezdő üzenet a felhasználótól
initial_message = "Szia! Kezdjünk el beszélgetni."
last_message = initial_message

# HTML sablon kezdete
html_template_start = """<!DOCTYPE html>
<html lang='hu'>
<head>
    <meta charset='UTF-8'>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Beszélgetés</title>
    <style>
        :root {
            --bg-primary: #1e1e1e;
            --bg-secondary: #2d2d2d;
            --bg-hover: #3d3d3d;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --accent-big: #4a9eff;
            --accent-small: #ffa94a;
            --accent-user: #4aff8a;
            --border: #404040;
            --thinking-bg: #252525;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: var(--text-primary);
            font-size: 2em;
            border-bottom: 2px solid var(--accent-big);
            padding-bottom: 10px;
        }
        
        .message {
            background: var(--bg-secondary);
            border-left: 4px solid var(--accent-user);
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .message:hover {
            background: var(--bg-hover);
            transform: translateX(5px);
        }
        
        .message.big {
            border-left-color: var(--accent-big);
        }
        
        .message.small {
            border-left-color: var(--accent-small);
        }
        
        .message-header {
            font-weight: bold;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .message-header .icon {
            font-size: 1.2em;
        }
        
        .message-content {
            color: var(--text-primary);
        }
        
        .thinking-wrapper {
            margin-top: 10px;
        }
        
        .thinking-toggle {
            background: var(--thinking-bg);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 8px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.2s ease;
            display: inline-block;
            margin-top: 5px;
        }
        
        .thinking-toggle:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }
        
        .thinking-toggle::before {
            content: '▶ ';
            display: inline-block;
            transition: transform 0.2s ease;
        }
        
        .thinking-toggle.open::before {
            transform: rotate(90deg);
        }
        
        .thinking-content {
            display: none;
            background: var(--thinking-bg);
            border: 1px solid var(--border);
            padding: 12px;
            margin-top: 8px;
            border-radius: 5px;
            color: var(--text-secondary);
            font-size: 0.9em;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .thinking-content.open {
            display: block;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            
            h1 {
                font-size: 1.5em;
            }
            
            .message {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Beszélgetés</h1>
        <div class="messages">
"""

html_template_end = """
        </div>
        <div class="footer">
            <p>Generálva: {timestamp}</p>
        </div>
    </div>
    <script>
        function toggleThinking(id) {{
            const toggle = document.getElementById('toggle-' + id);
            const content = document.getElementById('thinking-' + id);
            
            if (content.classList.contains('open')) {{
                content.classList.remove('open');
                toggle.classList.remove('open');
            }} else {{
                content.classList.add('open');
                toggle.classList.add('open');
            }}
        }}
    </script>
</body>
</html>
"""

messages_html = []

# Kezdő üzenet
messages_html.append(f"""
            <div class="message">
                <div class="message-header">
                    <span class="icon">💬</span>
                    <span>Felhasználó</span>
                </div>
                <div class="message-content">{last_message}</div>
            </div>
""")

thinking_counter = 0

for turn in range(TURNS):
    print(f"\n=== Forduló {turn+1} ===")

    # gpt-oss:20b válasz
    big_prompt = f"""
Te vagy a gpt-oss:20b. Csak a saját nevedben beszélj.
Válaszolj röviden, magyarul a következő üzenetre:
{last_message}
"""
    big_out_raw = subprocess.check_output(["ollama", "run", BIG, big_prompt], text=True).strip()
    
    # Thinking rész kivágása
    thinking_match = re.search(r'Thinking\.\.\.(.*?)\.\.\.done thinking\.', big_out_raw, re.DOTALL)
    if thinking_match:
        thinking_content = thinking_match.group(1).strip()
        big_out = re.sub(r'Thinking\.\.\..*?\.\.\.done thinking\.\s*', '', big_out_raw, flags=re.DOTALL).strip()
    else:
        thinking_content = None
        big_out = big_out_raw
    
    print(f"\n🧠 gpt-oss:20b:\n{big_out}")
    
    # HTML generálás thinking résszel
    thinking_html = ""
    if thinking_content:
        thinking_counter += 1
        thinking_html = f"""
                <div class="thinking-wrapper">
                    <button class="thinking-toggle" id="toggle-{thinking_counter}" onclick="toggleThinking({thinking_counter})">
                        Gondolkodási folyamat
                    </button>
                    <div class="thinking-content" id="thinking-{thinking_counter}">{thinking_content}</div>
                </div>
"""
    
    messages_html.append(f"""
            <div class="message big">
                <div class="message-header">
                    <span class="icon">🧠</span>
                    <span>gpt-oss:20b</span>
                </div>
                <div class="message-content">{big_out}</div>{thinking_html}
            </div>
""")
    
    # Csak a válasz megy tovább, a thinking nem!
    last_message = big_out

    # smollm2:135M válasz
    smol_prompt = f"""
Te vagy a smollm2:135M. Csak a saját nevedben beszélj.
Válaszolj röviden, magyarul a következő üzenetre.
Ha a bemenet nem értelmezhető, írj:
"smollm2: Nem értem a kérdést."
Bemenet:
{last_message}
"""
    smol_out = subprocess.check_output(["ollama", "run", SMOL, smol_prompt], text=True).strip()
    # Ha a modell túl kacifántosan válaszol, átírjuk rövid sablonra
    if len(smol_out) > 200 or not any(c.isalpha() for c in smol_out):
        smol_out = "smollm2: Nem értem a kérdést."
    print(f"\n🐥 smollm2:135M:\n{smol_out}")
    
    messages_html.append(f"""
            <div class="message small">
                <div class="message-header">
                    <span class="icon">🐥</span>
                    <span>smollm2:135M</span>
                </div>
                <div class="message-content">{smol_out}</div>
            </div>
""")
    
    last_message = smol_out

# HTML összeállítás
timestamp = datetime.now().strftime("%Y. %m. %d. %H:%M:%S")
html_output = html_template_start + "".join(messages_html) + html_template_end.format(timestamp=timestamp)

# mentés timestamp-nel a convs/ mappába
timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"convs/conversation_{timestamp_file}.html"
with open(filename, "w", encoding="utf-8") as f:
    f.write(html_output)

print(f"\nA beszélgetés mentve: {filename}")

# Update index.json
import json
index_path = "convs/index.json"
try:
    with open(index_path, "r", encoding="utf-8") as f:
        index_data = json.load(f)
except FileNotFoundError:
    index_data = {"conversations": []}

# Add new conversation to index
index_data["conversations"].append({
    "filename": f"conversation_{timestamp_file}.html",
    "preview": initial_message,  # Use the initial message as preview
    "turns": TURNS
})

# Sort by filename (newest first)
index_data["conversations"].sort(key=lambda x: x["filename"], reverse=True)

with open(index_path, "w", encoding="utf-8") as f:
    json.dump(index_data, f, indent=2, ensure_ascii=False)

print(f"Index frissítve: {len(index_data['conversations'])} beszélgetés")
