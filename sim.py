import subprocess
from datetime import datetime
import re
from collections import Counter
import sys

BIG = "gpt-oss:20b"
SMOL = "smollm2:135M"

TURNS = 10  # hány forduló legyen
MAX_THINKING_LINES = 50  # Max gondolkodási sorok a gpt-oss számára

def stream_output(process, prefix="", color_code=""):
    """Stream subprocess output in real-time."""
    output_lines = []
    
    for line in iter(process.stdout.readline, ''):
        if line:
            output_lines.append(line)
            # Print with color if provided
            if color_code:
                sys.stdout.write(f"{color_code}{prefix}{line}\033[0m")
            else:
                sys.stdout.write(f"{prefix}{line}")
            sys.stdout.flush()
    
    process.wait()
    return ''.join(output_lines).strip()

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

def remove_repetitions(text, max_repeats=3):
    """Eltávolítja az ismétlődő sorokat, max 3 példányt hagy meg."""
    lines = text.split('\n')
    
    # Csoportosítjuk az egymás utáni azonos sorokat
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        count = 1
        
        # Számoljuk, hányszor ismétlődik ugyanaz a sor
        while i + count < len(lines) and lines[i + count].strip() == line.strip():
            count += 1
        
        # Maximum max_repeats példányt tartunk meg
        if count > max_repeats:
            for _ in range(max_repeats):
                result.append(line)
            result.append(f"[... {count - max_repeats} ismétlődés kihagyva ...]")
        else:
            for _ in range(count):
                result.append(line)
        
        i += count
    
    return '\n'.join(result)

def detect_spam_pattern(text):
    """Detektálja, ha a szöveg túl sok ismétlődést tartalmaz."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 5:
        return False
    
    # Számoljuk a leggyakoribb sorokat
    line_counts = Counter(lines)
    most_common = line_counts.most_common(1)[0]
    
    # Ha egy sor több mint 5x ismétlődik, az spam
    return most_common[1] > 5

for turn in range(TURNS):
    print(f"\n{'='*60}")
    print(f"  Forduló {turn+1}/{TURNS}")
    print(f"{'='*60}")

    # gpt-oss:20b válasz
    print(f"\n\033[94m🧠 gpt-oss:20b gondolkodik...\033[0m")
    big_prompt = f"""Te vagy a gpt-oss:20b. Csak a saját nevedben beszélj.
Válaszolj röviden, magyarul a következő üzenetre. GONDOLKOZZ RÖVIDEN, max {MAX_THINKING_LINES} sor!
{last_message}"""
    
    # Stream output in real-time
    process = subprocess.Popen(
        ["ollama", "run", BIG, big_prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    big_out_raw = stream_output(process, color_code="\033[96m")
    
    # Thinking rész kivágása és limitálása
    thinking_match = re.search(r'Thinking\.\.\.(.*?)\.\.\.done thinking\.', big_out_raw, re.DOTALL)
    if thinking_match:
        thinking_content = thinking_match.group(1).strip()
        # Limitáljuk a thinking sorok számát
        thinking_lines = thinking_content.split('\n')
        if len(thinking_lines) > MAX_THINKING_LINES:
            thinking_content = '\n'.join(thinking_lines[:MAX_THINKING_LINES]) + f"\n\n[... {len(thinking_lines) - MAX_THINKING_LINES} további sor kihagyva ...]"
        big_out = re.sub(r'Thinking\.\.\..*?\.\.\.done thinking\.\s*', '', big_out_raw, flags=re.DOTALL).strip()
    else:
        thinking_content = None
        big_out = big_out_raw
    
    print(f"\n\033[92m✓ gpt-oss:20b válasza rögzítve\033[0m")
    
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
    print(f"\n\033[93m🐥 smollm2:135M válaszol...\033[0m")
    smol_prompt = f"""Te vagy a smollm2:135M. Csak a saját nevedben beszélj.
Válaszolj röviden (max 2-3 mondat), magyarul a következő üzenetre.
Bemenet:
{last_message}"""
    
    # Stream output in real-time
    process = subprocess.Popen(
        ["ollama", "run", SMOL, smol_prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    smol_out_raw = stream_output(process, color_code="\033[93m")
    
    # Ellenőrizzük, van-e spam/ismétlődés
    is_spam = detect_spam_pattern(smol_out_raw)
    
    if is_spam:
        # Ha spam, tisztítjuk és jelezzük
        smol_out_clean = remove_repetitions(smol_out_raw, max_repeats=2)
        smol_out_display = smol_out_clean
        # A kontextbe csak egy rövid összefoglalót küldünk
        smol_out = "smollm2: [A válasz ismétlődéseket tartalmazott, összefoglalva: Nem értettem pontosan a kérdést.]"
        print(f"\n\033[91m⚠️  Ismétlődések észlelve - tisztítva és lerövidítve\033[0m")
    else:
        smol_out = smol_out_raw
        smol_out_display = smol_out_raw
        print(f"\n\033[92m✓ smollm2:135M válasza rögzítve\033[0m")
    
    # HTML-be a tisztított változat kerül
    repetition_notice = ""
    if is_spam:
        repetition_notice = '<div style="margin-top: 8px; padding: 8px; background: #3d2b2b; border-left: 3px solid #ff6b6b; border-radius: 4px; font-size: 0.85em; color: #ffb3b3;">⚠️ Megjegyzés: Az eredeti válasz túl sok ismétlődést tartalmazott. A kontextbe egy egyszerűsített verzió került továbbítva.</div>'
    
    messages_html.append(f"""
            <div class="message small">
                <div class="message-header">
                    <span class="icon">🐥</span>
                    <span>smollm2:135M</span>
                </div>
                <div class="message-content">{smol_out_display}</div>
                {repetition_notice}
            </div>
""")
    
    # A következő fordulóba a tisztított/egyszerűsített verzió megy
    last_message = smol_out

# HTML összeállítás
print(f"\n{'='*60}")
print("💾 Beszélgetés mentése...")
timestamp = datetime.now().strftime("%Y. %m. %d. %H:%M:%S")
html_output = html_template_start + "".join(messages_html) + html_template_end.format(timestamp=timestamp)

# mentés timestamp-nel a convs/ mappába
timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"convs/conversation_{timestamp_file}.html"
with open(filename, "w", encoding="utf-8") as f:
    f.write(html_output)

print(f"✓ Beszélgetés mentve: {filename}")

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

print(f"✓ Index frissítve: {len(index_data['conversations'])} beszélgetés")
print(f"{'='*60}\n")
print("\033[92m🎉 Kész! A beszélgetés sikeresen elkészült.\033[0m\n")
