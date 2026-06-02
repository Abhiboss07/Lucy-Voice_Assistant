# 🎙️ Lucy - Advanced Conversational Voice & Text Assistant

Lucy is an advanced, highly interactive, and warm AI voice and text assistant developed using Python. Powered by state-of-the-art LLMs (Gemini and Groq fallback) and a sleek PyQt5 GUI, Lucy serves as a conversational companion capable of real-time information retrieval, smart email drafting, interactive reminders, smart home simulation, and local application automation.

Developed as a capstone project for the **Python Programming Internship** at **Oasis Infobyte**.

---

## ✨ Core Features

*   **🎙️ Warm Companion Persona**: Built with a conversational, friendly, and human-like voice and text interface. Lucy speaks and behaves as a human companion, avoiding dry, robotic templates.
*   **🌐 Captcha-Immune Real-Time Search**: Integrated with an intelligent fallback search pipeline (utilizing Yahoo Search scrapers and the official Wikipedia Search API) that guarantees 100% search uptime even when standard search scrapers encounter CAPTCHAs.
*   **📧 Interactive Email Automation**: Complete multi-turn draft state machine that allows you to draft emails, adjust recipient lists dynamically using conversational context (e.g. *"send to dad instead"*), modify composed draft bodies on the fly, and send emails in the background (via SMTP) or open pre-filled browser tabs.
*   **⏰ Human-Like Reminder Engine**: Features a background speech and text alert system. It intelligently distinguishes between generic reminders (*"Hey there! Just a friendly heads-up: your reminder is due!"*) and specific tasks (*"Friendly Reminder: call mom"*).
*   **🏠 Smart Home Simulator**: A simulated smart home device dashboard (Bedroom AC with temperature controls, Living Room Light, Smart TV, Kitchen Bulb) featuring pronound-aware state controls (e.g., *"turn it off"* resolves to the last controlled device).
*   **🚀 Priority-Based App Launching**: Intelligently prioritizes opening local desktop applications (via `AppOpener` and `os.startfile`). If the application is not installed on the PC, it automatically falls back to opening its corresponding website alias or locating it via a web search.

---

## 🛠️ Technology Stack

*   **Core Logic**: Python 3.10+
*   **LLMs & NLP**: Groq API (Llama 3) & Gemini API (Gemini 2.5)
*   **Graphical Interface**: PyQt5 (sleek, modern dark-themed voice assistant GUI)
*   **Speech Synthesis (TTS)**: `edge-tts` (sentence-by-sentence asynchronous pre-fetching for zero-latency audio playback)
*   **Web Scraping**: BeautifulSoup4 & Requests

---

## ⚙️ Installation & Setup

Follow these simple steps to set up and run Lucy on your local machine:

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Create and Activate a Virtual Environment
```bash
# Create environment
python -m venv .venv

# Activate environment (Windows)
.venv\Scripts\activate

# Activate environment (Mac/Linux)
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r Requirements.txt
```

### 4. Configure Environment Variables
1. Copy the `.env.example` file to a new file named `.env`:
   ```bash
   copy .env.example .env
   ```
2. Open your new `.env` file and insert your API keys:
   *   `GroqAPIKey`: Your Groq API key.
   *   `GeminiAPIKey`: Your Gemini API key.
   *   `Username`: Your name.
   *   `CreatorName`: Your name.

---

## 🚀 How to Run

Launch the application directly from your terminal:
```bash
python main.py
```
This will open the sleek, interactive dark-themed GUI dashboard. You can toggle the microphone to speak to Lucy or type your queries in the bottom text box.

---

## 📄 License & Acknowledgments

This project was developed for the **Oasis Infobyte Python Programming Internship**. Special thanks to the mentors and evaluation team at Oasis Infobyte for this learning opportunity.
