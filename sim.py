import subprocess
from datetime import datetime
import re
from collections import Counter
import sys

BIG = "gpt-oss:20b"
SMOL = "smollm2:135M"

TURNS = 10  # hány forduló legyen
MAX_THINKING_LINES = 150  # Max gondolkodási sorok a gpt-oss számára

# Nyelv választék
LANGUAGES = {
    "1": {"name": "Magyar", "code": "hu", "instruction": "magyarul"},
    "2": {"name": "English", "code": "en", "instruction": "in English"},
    "3": {"name": "Deutsch", "code": "de", "instruction": "auf Deutsch"},
    "4": {"name": "Español", "code": "es", "instruction": "en español"},
    "5": {"name": "Français", "code": "fr", "instruction": "en français"},
}

# Interaktív menü
def show_menu():
    print("\n" + "="*60)
    print("🤖 AI Beszélgetés Generátor")
    print("="*60)
    
    # Nyelv választás
    print("\n📝 Válassz nyelvet:")
    for key, lang in LANGUAGES.items():
        print(f"  {key}. {lang['name']}")
    
    while True:
        lang_choice = input("\nNyelv (1-5): ").strip()
        if lang_choice in LANGUAGES:
            selected_lang = LANGUAGES[lang_choice]
            break
        print("❌ Érvénytelen választás, próbáld újra!")
    
    # Téma választás
    print(f"\n💡 Milyen témáról beszélgessenek a modellek?")
    print("   (Példák: 'technológia', 'sport', 'zene', 'tudomány', stb.)")
    
    topic = input("\nTéma: ").strip()
    while not topic:
        print("❌ A téma nem lehet üres!")
        topic = input("Téma: ").strip()
    
    # Fordulók száma
    print(f"\n🔄 Hány fordulót szeretnél? (alapértelmezett: 10)")
    turns_input = input("Fordulók száma: ").strip()
    turns = int(turns_input) if turns_input.isdigit() and int(turns_input) > 0 else 10
    
    print(f"\n✅ Beállítások:")
    print(f"   Nyelv: {selected_lang['name']}")
    print(f"   Téma: {topic}")
    print(f"   Fordulók: {turns}")
    print("="*60 + "\n")
    
    return selected_lang, topic, turns

# Kezdő üzenet generálása
def generate_initial_message(lang, topic):
    templates = {
        "hu": f"Szia! Beszélgessünk a következő témáról: {topic}",
        "en": f"Hi! Let's talk about: {topic}",
        "de": f"Hallo! Lass uns über {topic} sprechen",
        "es": f"¡Hola! Hablemos sobre: {topic}",
        "fr": f"Salut ! Parlons de : {topic}"
    }
    return templates.get(lang['code'], templates['en'])

# Menü megjelenítése
selected_language, conversation_topic, TURNS = show_menu()
initial_message = generate_initial_message(selected_language, conversation_topic)
last_message = initial_message

def stream_output(process, prefix="", color_code="", timeout=30, max_total_time=120):
    """Stream subprocess output in real-time with timeout support.
    
    Args:
        timeout: Seconds of no output before killing (default 30)
        max_total_time: Maximum total execution time regardless of output (default 60)
    """
    import time
    from collections import Counter
    from difflib import SequenceMatcher
    
    def similarity(a, b):
        """Kiszámolja két string hasonlóságát (0.0 - 1.0)."""
        return SequenceMatcher(None, a, b).ratio()
    
    output_lines = []
    start_time = time.time()
    last_output_time = time.time()
    
    while True:
        line = process.stdout.readline()
        if line:
            output_lines.append(line)
            last_output_time = time.time()
            # Print with color if provided
            if color_code:
                sys.stdout.write(f"{color_code}{prefix}{line}\033[0m")
            else:
                sys.stdout.write(f"{prefix}{line}")
            sys.stdout.flush()
            
            # Real-time spam detection: check last 20 lines for patterns
            if len(output_lines) >= 20:
                recent_lines = [l.strip() for l in output_lines[-20:] if l.strip()]
                
                # Method 1: Exact line repetition (5+ times)
                line_counts = Counter(recent_lines)
                for line_text, count in line_counts.items():
                    if count >= 5 and len(line_text) > 5:
                        print(f"\n\033[91m⚠️  Real-time spam detected (exact repeat {count}x)! Killing process...\033[0m")
                        try:
                            process.kill()
                            process.wait()
                        except:
                            pass
                        return None
                
                # Method 2: Similar lines (90%+ similarity, appearing 5+ times)
                if len(recent_lines) >= 5:
                    similar_groups = []
                    for i, line1 in enumerate(recent_lines):
                        if len(line1) <= 10:  # Skip very short lines
                            continue
                        similar_count = 1
                        for j, line2 in enumerate(recent_lines):
                            if i != j and len(line2) > 10:
                                if similarity(line1, line2) >= 0.9:
                                    similar_count += 1
                        if similar_count >= 5:
                            print(f"\n\033[91m⚠️  Real-time spam detected (90%+ similar lines {similar_count}x)! Killing process...\033[0m")
                            try:
                                process.kill()
                                process.wait()
                            except:
                                pass
                            return None
                
                # Method 3: Multi-line pattern detection
                for pattern_size in [6, 8, 10]:
                    if len(output_lines) >= pattern_size * 2:
                        last_pattern = ''.join(output_lines[-pattern_size:])
                        prev_pattern = ''.join(output_lines[-pattern_size*2:-pattern_size])
                        if similarity(last_pattern, prev_pattern) >= 0.9 and len(last_pattern.strip()) > 30:
                            print(f"\n\033[91m⚠️  Real-time spam detected ({pattern_size}-line pattern)! Killing process...\033[0m")
                            try:
                                process.kill()
                                process.wait()
                            except:
                                pass
                            return None
            
            # Early detection: 3 consecutive very similar lines
            if len(output_lines) >= 3:
                last_3 = [l.strip() for l in output_lines[-3:] if l.strip()]
                if len(last_3) == 3 and all(len(l) > 10 for l in last_3):
                    if similarity(last_3[0], last_3[1]) >= 0.9 and similarity(last_3[1], last_3[2]) >= 0.9:
                        print(f"\n\033[91m⚠️  Real-time spam detected (3x consecutive similar)! Killing process...\033[0m")
                        try:
                            process.kill()
                            process.wait()
                        except:
                            pass
                        return None
        
        # Check if process finished
        if process.poll() is not None and not line:
            break
        
        # Timeout check: no output for N seconds
        if time.time() - last_output_time > timeout:
            print(f"\n\033[91m⚠️  No output timeout! Killing process...\033[0m")
            try:
                process.kill()
                process.wait()
            except:
                pass
            return None  # Indicate timeout
        
        # Absolute timeout: maximum total execution time
        if time.time() - start_time > max_total_time:
            print(f"\n\033[91m⚠️  Maximum execution time exceeded! Killing process...\033[0m")
            try:
                process.kill()
                process.wait()
            except:
                pass
            return None  # Indicate timeout
    
    return ''.join(output_lines).strip()

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

    # gpt-oss:20b válasz with retry logic
    big_regenerate_count = 0
    max_retries = 3
    big_out_raw = None
    
    while big_regenerate_count < max_retries:
        print(f"\n\033[94m🧠 gpt-oss:20b gondolkodik...\033[0m")
        if big_regenerate_count > 0:
            print(f"\033[93m⚠️  Újrapróbálás ({big_regenerate_count}/{max_retries})...\033[0m")
        
        big_prompt = f"""Te vagy a gpt-oss:20b. Csak a saját nevedben beszélj.
Válaszolj röviden, {selected_language['instruction']} a következő üzenetre. GONDOLKOZZ RÖVIDEN, max {MAX_THINKING_LINES} sor!
{last_message}"""
        
        # Stream output in real-time
        process = subprocess.Popen(
            ["ollama", "run", BIG, big_prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        big_out_raw = stream_output(process, color_code="\033[96m", timeout=30)
        
        # Check if timeout occurred
        if big_out_raw is None:
            big_regenerate_count += 1
            print(f"\n\033[91m⚠️  Timeout - nincs válasz 30 másodperce\033[0m")
            if big_regenerate_count >= max_retries:
                big_out_raw = "[ERROR: gpt-oss:20b nem válaszolt időben több próbálkozás után sem]"
                break
            continue
        else:
            # Success
            break
    
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
    
    # Regeneration notice for gpt-oss
    regen_notice_big = ""
    if big_regenerate_count > 0:
        regen_notice_big = f'<div style="margin-top: 8px; padding: 6px 10px; background: #3d2d2b; border-left: 3px solid #ffa94a; border-radius: 4px; font-size: 0.85em; color: #ffcc99;">🔄 Regenerated: {big_regenerate_count}x (timeout)</div>'
    
    messages_html.append(f"""
            <div class="message big">
                <div class="message-header">
                    <span class="icon">🧠</span>
                    <span>gpt-oss:20b</span>
                </div>
                <div class="message-content">{big_out}</div>{thinking_html}
                {regen_notice_big}
            </div>
""")
    
    # Csak a válasz megy tovább, a thinking nem!
    last_message = big_out

    # smollm2:135M válasz with retry logic
    smol_regenerate_count = 0
    max_retries = 3
    smol_out_raw = None
    is_spam = False
    
    while smol_regenerate_count < max_retries:
        print(f"\n\033[93m🐥 smollm2:135M válaszol...\033[0m")
        if smol_regenerate_count > 0:
            print(f"\033[93m⚠️  Újrapróbálás ({smol_regenerate_count}/{max_retries})...\033[0m")
        
        smol_prompt = f"""Te vagy a smollm2:135M. Csak a saját nevedben beszélj.
Válaszolj röviden (max 2-3 mondat), {selected_language['instruction']} a következő üzenetre.
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
        
        smol_out_raw = stream_output(process, color_code="\033[93m", timeout=30)
        
        # Check if timeout occurred
        if smol_out_raw is None:
            smol_regenerate_count += 1
            print(f"\n\033[91m⚠️  Timeout - nincs válasz 30 másodperce\033[0m")
            if smol_regenerate_count >= max_retries:
                smol_out_raw = "[ERROR: smollm2:135M nem válaszolt időben több próbálkozás után sem]"
                break
            continue
        
        # Ellenőrizzük, van-e spam/ismétlődés
        is_spam = detect_spam_pattern(smol_out_raw)
        
        if is_spam:
            smol_regenerate_count += 1
            print(f"\n\033[91m⚠️  Spam pattern észlelve (5+ azonos sor)\033[0m")
            if smol_regenerate_count >= max_retries:
                # Ha max retry után is spam, megtartjuk de jelezzük
                break
            continue
        else:
            # Success - no spam, no timeout
            break
    
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
    
    # Regeneration notice for smollm2
    regen_notice_smol = ""
    if smol_regenerate_count > 0:
        reason = "timeout/spam" if is_spam else "timeout"
        regen_notice_smol = f'<div style="margin-top: 8px; padding: 6px 10px; background: #3d2d2b; border-left: 3px solid #ffa94a; border-radius: 4px; font-size: 0.85em; color: #ffcc99;">🔄 Regenerated: {smol_regenerate_count}x ({reason})</div>'
    
    messages_html.append(f"""
            <div class="message small">
                <div class="message-header">
                    <span class="icon">🐥</span>
                    <span>smollm2:135M</span>
                </div>
                <div class="message-content">{smol_out_display}</div>
                {repetition_notice}
                {regen_notice_smol}
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

# Add new conversation to index with metadata
index_data["conversations"].append({
    "filename": f"conversation_{timestamp_file}.html",
    "preview": initial_message,  # Use the initial message as preview
    "turns": TURNS,
    "language": selected_language['name'],
    "topic": conversation_topic
})

# Sort by filename (newest first)
index_data["conversations"].sort(key=lambda x: x["filename"], reverse=True)

with open(index_path, "w", encoding="utf-8") as f:
    json.dump(index_data, f, indent=2, ensure_ascii=False)

print(f"✓ Index frissítve: {len(index_data['conversations'])} beszélgetés")
print(f"{'='*60}\n")
print("\033[92m🎉 Kész! A beszélgetés sikeresen elkészült.\033[0m\n")
