# 🤖 AI Conversations: gpt-oss:20b vs smollm2:135M

An experimental project showcasing conversations between two AI language models: **gpt-oss:20b** and **smollm2:135M**.

## 🌐 Live Demo

Visit the live conversations at: [https://bali0531-rc.github.io/smollm2-vs-gpt-oss20b/](https://bali0531-rc.github.io/smollm2-vs-gpt-oss20b/)

## 📖 About

This project explores how different AI models interact with each other. The larger model (gpt-oss:20b) engages in conversation with the smaller model (smollm2:135M), creating interesting dialogues that showcase their different capabilities.

### Key Features

- 🧠 **Thinking Process Separation**: The gpt-oss:20b model's reasoning is captured but not sent to smollm2, ensuring cleaner conversations
- 🎨 **Modern Dark UI**: Beautiful, responsive interface with collapsible thinking sections
- 📱 **Mobile Friendly**: Fully responsive design works on all devices
- 🔍 **Searchable Archive**: Browse and search through all conversations
- ⚡ **Interactive**: Click to expand/collapse AI thinking processes

## 🛠️ Technical Details

### Models Used

- **gpt-oss:20b**: A 20 billion parameter model with advanced reasoning capabilities
- **smollm2:135M**: A compact 135 million parameter model

### Technology Stack

- **Backend**: Python with subprocess calls to Ollama
- **Frontend**: Pure HTML, CSS, and JavaScript
- **Hosting**: GitHub Pages
- **Models**: Ollama local inference

## 🚀 Running Locally

### Prerequisites

- Python 3.7+
- [Ollama](https://ollama.ai) installed
- Models pulled: `ollama pull gpt-oss:20b` and `ollama pull smollm2:135M`

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Bali0531-RC/smollm2-vs-gpt-oss20b.git
cd smollm2-vs-gpt-oss20b
```

2. Run a conversation:
```bash
python sim.py
```

3. View conversations locally:
```bash
python -m http.server 8000
# Then open http://localhost:8000 in your browser
```

## 📝 Generating New Conversations

Edit `sim.py` to customize:
- Starting message (`last_message`)
- Number of turns (`TURNS`)
- Model prompts

Run the script to generate a new conversation HTML file in the `convs/` directory.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Submit interesting conversation topics
- Improve the UI/UX
- Optimize the conversation generation
- Add new features

## 📄 License

MIT License - feel free to use this project for your own experiments!

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for making local AI inference accessible
- The open-source AI community

---

Made with ❤️ and 🤖
