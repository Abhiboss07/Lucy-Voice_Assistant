from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
# import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os
import re
import json
import time
import datetime
import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote

# from Backend.RealtimeSearchEngine import RealtimeSearchEngine
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
GroqModel = env_vars.get("GroqModel") or "llama-3.3-70b-versatile"
GeminiAPIKey = env_vars.get("GeminiAPIKey")
GeminiModel = env_vars.get("GeminiModel") or "gemini-2.5-flash-lite"
Username = env_vars.get("Username") or "User"
AssistantLanguage = env_vars.get("AssistantLanguage") or "English unless the user speaks Hindi or Hinglish"
ContentMaxResponseTokens = int(env_vars.get("ContentMaxResponseTokens") or 900)

# classes = [ "zCubwf", "hgKElc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta", 
#             "IZ6rdc", "O5uR6d LTKOO", "vlzY6d", "webanswers-webanswers_table__webanswers-table", "dDoNo ikb4Bb gsrt", "sXLaOe", 
#             "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"

client = Groq(api_key=GroqAPIKey) if GroqAPIKey else None


# professional_responses = [
#     "Your satisfaction is my top priority; feel free to reach out if there's anything else I can assist you with.",
#     "I'm at your service for any additional questions or support you may need-don't hesitate to ask.",
# ]
# 
# messages = []

WEBSITE_ALIASES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "reddit": "https://www.reddit.com",
    "stackoverflow": "https://stackoverflow.com",
    "flipkart": "https://www.flipkart.com",
    "amazon": "https://www.amazon.in",
}

SystemChatBot = [{"role": "system", "content": f"You are a content writer. Write professionally. Default to English. If the user's request is in Hindi, write in Hindi. If the request is Hinglish or mixes Hindi and English, write naturally in Hinglish. Language preference: {AssistantLanguage}. Do not address the user by name or title unless explicitly requested for that exact response."}]
SystemText = SystemChatBot[0]["content"]


def _gemini_content(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GeminiModel}:generateContent"
    response = requests.post(
        url,
        params={"key": GeminiAPIKey},
        json={
            "systemInstruction": {"parts": [{"text": SystemText}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 1,
                "maxOutputTokens": ContentMaxResponseTokens,
            },
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates") or []
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    return "".join(part.get("text", "") for part in parts).strip()


def _groq_content(prompt):
    if client is None:
        raise RuntimeError("No content API key is configured. Add GeminiAPIKey or GroqAPIKey to .env.")

    local_messages = [{"role": "user", "content": prompt}]
    completion = client.chat.completions.create(
        model=GroqModel,
        messages=SystemChatBot + local_messages,
        max_tokens=ContentMaxResponseTokens,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None,
    )

    answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            answer += chunk.choices[0].delta.content

    return answer.replace("</s>", "").strip()


def GoogleSearch(Topic):
    topic_lower = Topic.lower().strip()
    match = re.search(r"(.+?)\s+on\s+(flipkart|amazon|youtube|github|wikipedia|reddit|google)", topic_lower)
    if match:
        query_val = match.group(1).strip()
        website_val = match.group(2).strip()
        
        SEARCH_URLS = {
            "google": "https://www.google.com/search?q={query}",
            "youtube": "https://www.youtube.com/results?search_query={query}",
            "flipkart": "https://www.flipkart.com/search?q={query}",
            "amazon": "https://www.amazon.in/s?k={query}",
            "github": "https://github.com/search?q={query}",
            "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search={query}",
            "reddit": "https://www.reddit.com/search/?q={query}",
        }
        
        url_template = SEARCH_URLS.get(website_val)
        if url_template:
            from urllib.parse import quote
            url = url_template.format(query=quote(query_val))
            webopen(url)
            return f"No problem! I've searched for '{query_val}' on {website_val.capitalize()} for you."
            
    search(Topic)
    return f"Sure thing! I've run a search for '{Topic}' on Google."

def Content(Topic):
    if not GeminiAPIKey and client is None:
        print("No content API key is configured. Add GeminiAPIKey or GroqAPIKey to .env.")
        return False

    def OpenNotepad(File):
        deafult_text_editor = 'notepad.exe'
        subprocess.Popen([deafult_text_editor, File])


    def ContentWriterAI(prompt):
        if GeminiAPIKey:
            return _gemini_content(prompt)
        return _groq_content(prompt)
    
    Topic: str = Topic.replace("Content", "").strip()
    if not Topic:
        return False

    ContentByAI = ContentWriterAI(Topic)
    safe_topic = "".join(ch for ch in Topic.lower().replace(" ", "") if ch.isalnum() or ch in ("-", "_"))
    if not safe_topic:
        return False

    os.makedirs("Data", exist_ok=True)
    file_path = os.path.join("Data", f"{safe_topic}.txt")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(ContentByAI)

    OpenNotepad(file_path)
    return True

def YoutubeSearch(Topic):
    UrlSearch = f"https://www.youtube.com/results?search_query={Topic}"
    webopen(UrlSearch)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

def _clean_target(target):
    target = str(target or "").strip()
    for prefix in ["website ", "site ", "app ", "application "]:
        if target.lower().startswith(prefix):
            return target[len(prefix):].strip()
    return target


def _looks_like_url(target):
    target = str(target or "").strip().lower()
    return target.startswith(("http://", "https://", "www."))


def _looks_like_domain(target):
    target = str(target or "").strip().lower()
    if " " in target or "." not in target:
        return False
    return re.match(r"^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(/.*)?$", target) is not None


def _normalize_url(target):
    target = _clean_target(target)
    alias = WEBSITE_ALIASES.get(target.lower())
    if alias:
        return alias
    if _looks_like_url(target):
        return target if target.startswith(("http://", "https://")) else f"https://{target}"
    if _looks_like_domain(target):
        return f"https://{target}"
    return ""


def OpenWebsite(target):
    url = _normalize_url(target)
    if not url:
        query = _clean_target(target).replace(" ", "+")
        url = f"https://www.google.com/search?q={query}"
    webopen(url)
    return True


def OpenApp(app, sess=None):
    sess = sess or requests.session()
    app = _clean_target(app)

    # 1. Try opening it as a local system application first (App priority!)
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception as e:
        print(f"AppOpener failed to open local app '{app}': {e}. Falling back to system start...")
        try:
            os.startfile(app)
            return True
        except Exception as start_error:
            print(f"System start fallback failed: {start_error}. Falling back to web/domain...")

    # 2. If local app failed, try to resolve to a website and open it
    url = _normalize_url(app)
    if url:
        webopen(url)
        return True

    # 3. If no direct website alias or domain, perform Google Search fallback to find the link
    try:
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', {'jsname': 'UWckNb'})
            return [link.get('href') for link in links]
        
        def search_google(query):
            url = f"https://www.google.com/search?q={query}"
            headers = {'User-Agent': useragent}
            response = sess.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.text
            else:
                print("Failed to retrieve search results.")
            return None
        
        html = search_google(app)
        if html:
            links = extract_links(html)
            if links:
                webopen(links[0])
                return True
    except Exception as search_err:
        print(f"Web search fallback failed: {search_err}")

    return False

def CloseApp(app):
    if "chrome" in app:
        pass
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        except Exception as e:
            print(f"Close app failed: {e}")
            return False

def System(command):

    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume unmute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    
    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()

    return True


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}

def _call_llm_extraction(prompt):
    system_instruction = "You are a strict data extraction tool. You must respond only with a raw, valid JSON object and absolutely nothing else. No markdown, no triple backticks, no conversational text, no preambles."
    
    raw_response = ""
    try:
        if GeminiAPIKey:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{GeminiModel}:generateContent"
                response = requests.post(
                    url,
                    params={"key": GeminiAPIKey},
                    json={
                        "systemInstruction": {"parts": [{"text": system_instruction}]},
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "topP": 1,
                            "maxOutputTokens": 300,
                        },
                    },
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()
                candidates = data.get("candidates") or []
                parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
                raw_response = "".join(part.get("text", "") for part in parts).strip()
            except Exception as gemini_err:
                print(f"Gemini extraction failed, trying Groq fallback: {gemini_err}")
                if client is not None:
                    completion = client.chat.completions.create(
                        model=GroqModel,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=300,
                        temperature=0.1,
                        top_p=1,
                    )
                    raw_response = completion.choices[0].message.content.strip()
                else:
                    raise gemini_err
        elif client is not None:
            completion = client.chat.completions.create(
                model=GroqModel,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1,
                top_p=1,
            )
            raw_response = completion.choices[0].message.content.strip()
        else:
            raise RuntimeError("No API keys available.")
    except Exception as e:
        print(f"Extraction LLM call failed completely: {e}")
        return None

    try:
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
    except Exception as parse_err:
        print(f"Failed to parse extraction response as JSON: {parse_err}. Response was: {raw_response}")
        try:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return None

def _extract_clean_email(text):
    text = " ".join(text.lower().split())
    text = text.replace("at the rate", "@").replace(" at ", "@").replace(" dot ", ".")
    text = re.sub(r"\s*@\s*", "@", text)
    text = re.sub(r"\s*\.\s*", ".", text)
    
    if "@" not in text:
        return ""
        
    words = text.split()
    email_word_idx = -1
    for i, word in enumerate(words):
        if "@" in word:
            email_word_idx = i
            break
            
    if email_word_idx == -1:
        return ""
        
    stop_words = {"to", "email", "send", "for", "message", "subject", "saying", "is", "and", "the", "a", "an", "about", "with", "write"}
    collected_words = []
    collected_words.append(words[email_word_idx])
    
    for i in range(email_word_idx - 1, -1, -1):
        word = words[i].strip(".,!?")
        if word in stop_words:
            break
        if not re.match(r"^[a-zA-Z0-9._-]+$", word):
            break
        collected_words.insert(0, words[i])
        
    full_email_candidate = "".join(collected_words)
    full_email_candidate = full_email_candidate.rstrip(".,!?")
    
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", full_email_candidate)
    if match:
        return match.group(0)
        
    return ""

def _call_llm_text(prompt, default_fallback=""):
    try:
        if GeminiAPIKey:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{GeminiModel}:generateContent"
                response = requests.post(
                    url,
                    params={"key": GeminiAPIKey},
                    json={
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.5,
                            "topP": 1,
                            "maxOutputTokens": 450,
                        },
                    },
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()
                candidates = data.get("candidates") or []
                parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
                return "".join(part.get("text", "") for part in parts).strip()
            except Exception as gemini_err:
                print(f"Gemini text call failed, trying Groq fallback: {gemini_err}")
                if client is not None:
                    completion = client.chat.completions.create(
                        model=GroqModel,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=450,
                        temperature=0.5,
                        top_p=1,
                    )
                    return completion.choices[0].message.content.strip()
                else:
                    raise gemini_err
        elif client is not None:
            completion = client.chat.completions.create(
                model=GroqModel,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=450,
                temperature=0.5,
                top_p=1,
            )
            return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM text call failed completely: {e}")
    return default_fallback

def resolve_contact_or_email(text):
    text_clean = text.lower().strip()
    
    # 1. Use custom clean email extraction first
    extracted = _extract_clean_email(text)
    if extracted:
        return extracted
        
    # 2. Read the conversation history for context!
    chat_history = []
    chat_file = os.path.join("Data", "ChatLog.json")
    if os.path.exists(chat_file):
        try:
            with open(chat_file, "r", encoding="utf-8") as f:
                chat_history = json.load(f)
        except Exception:
            pass
            
    # Keep only the last 10 messages for context
    history_context = ""
    if chat_history:
        for msg in chat_history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_context += f"{role.capitalize()}: {content}\n"
            
    # 3. Use LLM to extract or correct misspelled email/contact based strictly on conversation history & context!
    prompt = f"""
    The user is trying to specify an email recipient.
    User input: "{text}"
    
    Recent Conversation History:
    {history_context}
    
    Tasks:
    1. If a valid email address is present in the user input, clean and return it.
    2. If no explicit email address is present, check the Conversation History. Resolve what email address they are referring to based on previous context, pronoun references, or corrections.
       For example, if they say "dad email" or "send to dad instead", and the history shows they were discussing "sameersingh9259@gmail.com" as dad's email, return "sameersingh9259@gmail.com".
    3. If they say a name or misspelled phrase (e.g. "summit singh" vs "sameer singh"), use the conversational context to determine which correct email address is intended.
    
    Respond in strict JSON format:
    {{
        "email": "resolved_email_address_or_null"
    }}
    """
    data = _call_llm_extraction(prompt)
    if data and isinstance(data, dict):
        resolved = data.get("email")
        if resolved and "@" in resolved:
            return resolved
            
    # 4. Direct search using regex as absolute fallback
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text.replace(" ", ""))
    if match:
        return match.group(0)
        
    return ""

def re_compose_email(email_state, tone, regenerate_subject=True):
    is_professional = "professional" in tone or "pro" in tone or "formal" in tone
    email_state["tone"] = "professional" if is_professional else "casual"
    
    message = email_state.get("message")
    recipient = email_state.get("recipient")
    
    if is_professional:
        prompt_body = f"""
        Reconstruct this email message to make it sound professional and formal. 
        Do NOT change the core meaning, add new facts, or remove important context.
        Message: "{message}"
        
        Respond only with the reconstructed professional email body. No preamble, no quotes, no salutations at the start, just the body text.
        """
        body = _call_llm_text(prompt_body, default_fallback=message)
        body = body.strip('\'"')
    else:
        body = message
        
    if regenerate_subject or not email_state.get("subject"):
        prompt_subject = f"""
        Generate a concise, {'professional' if is_professional else ''} subject line for an email with this body:
        "{body}"
        
        Respond only with the subject line. No quotes, no subject prefix.
        """
        subject = _call_llm_text(prompt_subject, default_fallback="Message from Lucy").strip('\'"')
    else:
        subject = email_state.get("subject")
        
    email_state["subject"] = subject
    email_state["body"] = body
    email_state["state"] = "composed"
    email_state["last_active"] = time.time()
    
    # Save the state
    state_file = os.path.join("Data", "email_state.json")
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(email_state, f, indent=4)
        
    # Send or open
    smtp_email = env_vars.get("SMTP_EMAIL")
    smtp_password = env_vars.get("SMTP_PASSWORD")
    smtp_server = env_vars.get("SMTP_SERVER") or "smtp.gmail.com"
    smtp_port = int(env_vars.get("SMTP_PORT") or 587)

    sent_via_smtp = False
    if smtp_email and smtp_password:
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = smtp_email
            msg['To'] = recipient

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [recipient], msg.as_string())
            server.quit()
            sent_via_smtp = True
            send_result = "Email sent successfully in the background via SMTP!"
        except Exception as e:
            print(f"SMTP failed in re_compose_email: {e}")

    if not sent_via_smtp:
        try:
            mailto_url = f"mailto:{recipient}?subject={quote(subject)}&body={quote(body)}"
            webopen(mailto_url)
            
            gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={recipient}&su={quote(subject)}&body={quote(body)}"
            webopen(gmail_url)
            send_result = "Opened pre-filled Gmail compose tab in your browser."
        except Exception as e:
            print(f"Mail fallback failed: {e}")
            send_result = "Failed to launch mail client."

    tone_label = "Reconstructed professionally" if is_professional else "Kept casual"
    ans = f"{tone_label}. Subject: '{subject}'. Message: '{body}'. {send_result}"
    return ans, email_state

def HandleDraftModification(Query, email_state):
    prompt = f"""
    The user recently composed an email with the following details:
    - Recipient: "{email_state.get('recipient')}"
    - Message/Body: "{email_state.get('message')}"
    - Subject: "{email_state.get('subject')}"
    - Tone: "{email_state.get('tone')}"
    
    The user's new query is: "{Query}"
    
    Task:
    Analyze if the user's query is a request to modify or send this email draft.
    Valid modifications include:
    1. Changing the body/message (e.g. "change the message to...", "change body to...").
    2. Changing the recipient (e.g. "change email to...", "send to... instead").
    3. Changing the subject (e.g. "change subject to...").
    4. Changing the tone (e.g. "make it professional", "change it to casual").
    5. Sending the email (e.g. "send it", "send the email").
    
    If it is NOT a modification/send request for the email draft (e.g. they are asking about weather, smart home, or general questions), set "is_modification" to false.
    
    Respond in strict JSON format:
    {{
        "is_modification": true,
        "type": "message" | "recipient" | "subject" | "tone" | "send" | null,
        "value": "extracted new value or null"
    }}
    """
    data = _call_llm_extraction(prompt)
    if not data or not data.get("is_modification"):
        return None, email_state
        
    mod_type = data.get("type")
    value = data.get("value")
    
    if mod_type == "message":
        cleaned_msg = value
        msg_prefixes = ["change the message to ", "change message to ", "change the body to ", "change body to ", "the message is ", "message is ", "the body is ", "body is "]
        for pref in msg_prefixes:
            if cleaned_msg.lower().startswith(pref):
                cleaned_msg = cleaned_msg[len(pref):].strip(" ,.!?")
                break
        email_state["message"] = cleaned_msg
        tone = email_state.get("tone") or "casual"
        return re_compose_email(email_state, tone)
        
    elif mod_type == "recipient":
        resolved_email = resolve_contact_or_email(value)
        if resolved_email:
            email_state["recipient"] = resolved_email
            tone = email_state.get("tone") or "casual"
            return re_compose_email(email_state, tone)
        else:
            return "I couldn't resolve that email address/contact. Who would you like to send it to?", email_state
            
    elif mod_type == "subject":
        email_state["subject"] = value
        return re_compose_email(email_state, email_state.get("tone") or "casual", regenerate_subject=False)
        
    elif mod_type == "tone":
        tone = value.lower()
        return re_compose_email(email_state, tone)
        
    elif mod_type == "send":
        tone = email_state.get("tone") or "casual"
        return re_compose_email(email_state, tone)
        
    return None, email_state

def SendEmail(Topic):
    # Try using the LLM to extract any present email/contact and message/body/subject from the initial query.
    contacts = {}
    contacts_file = os.path.join("Data", "contacts.json")
    if os.path.exists(contacts_file):
        try:
            with open(contacts_file, "r", encoding="utf-8") as f:
                contacts = json.load(f)
        except Exception:
            pass
            
    contacts_str = json.dumps(contacts, indent=2)
    prompt = f"""
    The user wants to send an email. Extract details from their query: "{Topic}"
    
    Available Contacts Database:
    {contacts_str}
    
    Tasks:
    1. Extract the recipient. If they mention a contact, resolve it to their email address. If they mention a raw email address (even with spaces like "sameer singh 7379 @ gmail.com"), clean and extract it.
    2. Extract the message/body of the email if they provided it (e.g. in "send email to dad saying hi", the message is "hi"). If not provided, return null.
    3. Extract a subject if they provided it. If not, return null.
    
    Respond in strict JSON format:
    {{
        "recipient": "resolved_email_or_null",
        "message": "extracted_message_or_null",
        "subject": "extracted_subject_or_null"
    }}
    """
    
    data = _call_llm_extraction(prompt)
    to_email = None
    initial_message = None
    initial_subject = None
    
    if data and isinstance(data, dict):
        to_email = data.get("recipient")
        initial_message = data.get("message")
        initial_subject = data.get("subject")
        
        # Defensive check: clear placeholder texts returned by LLM
        placeholders = ["null", "none", "not provided", "not mentioned", "n/a", "no message", "no subject", "unspecified", ""]
        if to_email and str(to_email).lower().strip() in placeholders:
            to_email = None
        if initial_message and str(initial_message).lower().strip() in placeholders:
            initial_message = None
        if initial_subject and str(initial_subject).lower().strip() in placeholders:
            initial_subject = None
        
    if not to_email:
        to_email = resolve_contact_or_email(Topic)
        
    state_file = os.path.join("Data", "email_state.json")
    
    if not to_email:
        email_state = {
            "state": "awaiting_recipient",
            "recipient": None,
            "message": None,
            "subject": None
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(email_state, f, indent=4)
        return "Sure. Who would you like to send the email to?"
    
    if to_email and initial_message:
        email_state = {
            "state": "awaiting_tone",
            "recipient": to_email,
            "message": initial_message,
            "subject": initial_subject
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(email_state, f, indent=4)
        return f"I've got the recipient: {to_email} and the message: '{initial_message}'. Should this email be casual or professional?"
        
    email_state = {
        "state": "awaiting_message",
        "recipient": to_email,
        "message": None,
        "subject": None
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(email_state, f, indent=4)
    return f"I've got the recipient: {to_email}. What is the message you are trying to send?"

def HandleEmailState(Query, email_state):
    state = email_state.get("state")
    recipient = email_state.get("recipient")
    message = email_state.get("message")
    state_file = os.path.join("Data", "email_state.json")
    
    # 1. Check if the user is correcting the recipient in ANY state!
    has_negation = any(word in Query.lower() for word in ["no", "not", "wrong", "change", "correct", "instead", "is actually", "email is", "send to", "send the message to"])
    resolved_email = resolve_contact_or_email(Query) if has_negation else ""
    if has_negation and resolved_email:
        email_state["recipient"] = resolved_email
        email_state["state"] = "awaiting_message"
        ans = f"My apologies. I've updated the recipient to: {resolved_email}. What is the message you are trying to send?"
        return ans, email_state
        
    # 2. Check if the user is correcting/changing the message body in ANY state!
    has_msg_change = any(pref in Query.lower() for pref in ["change the message to", "change message to", "change the body to", "change body to", "the message is", "message is"])
    if has_msg_change:
        cleaned_msg = Query
        msg_prefixes = ["change the message to ", "change message to ", "change the body to ", "change body to ", "the message is ", "message is ", "the body is ", "body is "]
        for pref in msg_prefixes:
            if cleaned_msg.lower().startswith(pref):
                cleaned_msg = cleaned_msg[len(pref):].strip(" ,.!?")
                break
        email_state["message"] = cleaned_msg
        email_state["state"] = "awaiting_tone"
        ans = f"I've updated the message to: '{cleaned_msg}'. Should this email be casual or professional?"
        return ans, email_state

    # 3. Proceed with standard state machine
    if state == "awaiting_recipient":
        to_email = resolve_contact_or_email(Query)
        if to_email:
            email_state["recipient"] = to_email
            email_state["state"] = "awaiting_message"
            ans = f"I've got the recipient: {to_email}. What is the message you are trying to send?"
        else:
            ans = "I couldn't parse a valid email address. Please say the email address clearly, for example, 'sameer at gmail dot com'."
            
        return ans, email_state
 
    elif state == "awaiting_message":
        cleaned_msg = Query
        msg_prefixes = ["the message is ", "message is ", "the body is ", "body is ", "saying "]
        for pref in msg_prefixes:
            if cleaned_msg.lower().startswith(pref):
                cleaned_msg = cleaned_msg[len(pref):].strip(" ,.!?")
                break
                
        email_state["message"] = cleaned_msg
        email_state["state"] = "awaiting_tone"
        ans = "Should this email be casual or professional?"
        return ans, email_state
 
    elif state == "awaiting_tone":
        tone = Query.lower()
        return re_compose_email(email_state, tone)
 
    return "Email state error.", {"state": None}

def get_windows_gps():
    import subprocess
    ps_code = """
    Add-Type -AssemblyName System.Device
    $GeoWatcher = New-Object System.Device.Location.GeoCoordinateWatcher
    $GeoWatcher.Start()
    $i = 0
    while (($GeoWatcher.Status -ne 'Ready') -and ($GeoWatcher.Permission -ne 'Denied') -and ($i -lt 50)) {
        Start-Sleep -Milliseconds 100
        $i++
    }
    if ($GeoWatcher.Permission -eq 'Denied') {
        Write-Output "Denied"
    } else {
        $location = $GeoWatcher.Position.Location
        if ($location.IsUnknown) {
            Write-Output "Unknown"
        } else {
            Write-Output "$($location.Latitude),$($location.Longitude)"
        }
    }
    $GeoWatcher.Stop()
    """
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_code],
            capture_output=True,
            text=True,
            timeout=10,
            startupinfo=startupinfo
        )
        output = res.stdout.strip()
        if output and "Denied" not in output and "Unknown" not in output and "," in output:
            parts = output.split(",")
            return float(parts[0]), float(parts[1])
    except Exception as e:
        print(f"Error getting Windows GPS: {e}")
    return None

def GetWeather(Topic):
    query = Topic.lower()
    
    prompt = f"""
    Analyze this weather request: "{Topic}"
    Extract:
    1. The specific city or location name mentioned (e.g. "Delhi", "New York", "London"). 
       - If they ask for "my location", "here", "me", "current location", or if they do not specify any city/location, return null.
    2. The day of interest: "today" | "tomorrow" | "daily" (if general or this week).
    
    Respond in JSON format:
    {{
        "city": "extracted location or null",
        "day": "today" | "tomorrow" | "daily"
    }}
    """
    data = _call_llm_extraction(prompt)
    city = None
    day = "today"
    if data:
        city = data.get("city")
        day = data.get("day", "today")

    # Clean generic phrases
    if city:
        city_clean = city.lower().strip()
        if city_clean in ["me", "my location", "here", "current location", "local", "null", "none"]:
            city = None

    lat = None
    lon = None
    full_city_name = None
    country = ""

    # If no specific city is requested, find the user's local weather
    if not city:
        print("Weather request has no specific location. Attempting GPS location...")
        gps = get_windows_gps()
        if gps:
            lat, lon = gps
            print(f"GPS location found: {lat}, {lon}")
            try:
                geo_resp = requests.get("http://ip-api.com/json/", timeout=5)
                if geo_resp.status_code == 200:
                    geo_data = geo_resp.json()
                    full_city_name = geo_data.get("city", "Current Location")
                    country = geo_data.get("country", "")
            except Exception:
                pass
            if not full_city_name:
                full_city_name = "Your Location"
        else:
            print("GPS location unavailable. Falling back to IP geolocation...")
            try:
                geo_resp = requests.get("http://ip-api.com/json/", timeout=5)
                if geo_resp.status_code == 200:
                    geo_data = geo_resp.json()
                    lat = geo_data.get("lat")
                    lon = geo_data.get("lon")
                    full_city_name = geo_data.get("city", "Unknown City")
                    country = geo_data.get("country", "")
            except Exception as e:
                print(f"IP Geolocation failed: {e}")
                
            if lat is None or lon is None:
                # Absolute fallback
                lat, lon = 51.5074, -0.1278  # London
                full_city_name = "London"
                country = "United Kingdom"
    else:
        # A specific city was requested. Use geocoding API to find coordinates.
        try:
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
            geo_res = requests.get(geocode_url, timeout=10)
            geo_res.raise_for_status()
            geo_data = geo_res.json()
            
            results = geo_data.get("results")
            if not results:
                return f"I couldn't find coordinates for '{city}'."
    
            lat = results[0]["latitude"]
            lon = results[0]["longitude"]
            full_city_name = results[0]["name"]
            country = results[0].get("country", "")
        except Exception as e:
            print(f"Geocoding failed for {city}: {e}")
            return f"I was unable to search for coordinates of {city} right now."

    # Now fetch the weather from Open-Meteo using the resolved lat/lon
    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto"
        w_res = requests.get(weather_url, timeout=10)
        w_res.raise_for_status()
        w_data = w_res.json()
    
        if day == "tomorrow":
            daily = w_data.get("daily", {})
            max_temp = daily.get("temperature_2m_max", [None, None])[1]
            min_temp = daily.get("temperature_2m_min", [None, None])[1]
            code = daily.get("weathercode", [None, None])[1]
            description = WEATHER_CODES.get(code, "Unknown conditions")
            
            return f"Tomorrow in {full_city_name}, the forecast is {description} with a high of {max_temp}°C and a low of {min_temp}°C."
        else:
            current = w_data.get("current_weather", {})
            temp = current.get("temperature")
            wind = current.get("windspeed")
            code = current.get("weathercode")
            description = WEATHER_CODES.get(code, "Unknown conditions")
    
            weather_state = {
                "city": f"{full_city_name}, {country}" if country else full_city_name,
                "temp": f"{temp}°C",
                "desc": description,
                "wind": f"{wind} km/h"
            }
            os.makedirs("Data", exist_ok=True)
            with open(os.path.join("Data", "weather_state.json"), "w", encoding="utf-8") as f:
                json.dump(weather_state, f, indent=4)
    
            return f"The weather in {full_city_name} is {description} with a temperature of {temp}°C."
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        return f"I was unable to retrieve the weather forecast for {full_city_name or city} right now."

def ControlSmartHome(Topic):
    state_file = os.path.join("Data", "smart_home.json")
    last_device_file = os.path.join("Data", "last_device.json")
    
    devices = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                devices = json.load(f)
        except Exception:
            pass
            
    if not devices:
        devices = {
            "living_room_light": {
                "name": "Living Room Light",
                "state": "off",
                "type": "light"
            },
            "bedroom_ac": {
                "name": "Bedroom AC",
                "state": "off",
                "temperature": 24,
                "type": "ac"
            },
            "kitchen_bulb": {
                "name": "Kitchen Bulb",
                "state": "off",
                "type": "light"
            },
            "smart_tv": {
                "name": "Smart TV",
                "state": "off",
                "type": "tv"
            }
        }
        try:
            os.makedirs("Data", exist_ok=True)
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(devices, f, indent=4)
        except Exception as e:
            print(f"Failed to initialize smart_home.json: {e}")

    last_device_key = None
    try:
        if os.path.exists(last_device_file):
            with open(last_device_file, "r", encoding="utf-8") as f:
                last_device_key = json.load(f).get("last_device")
    except Exception:
        pass

    last_device_info = f"The last controlled device was: '{last_device_key}'." if last_device_key else "No device was controlled recently."

    prompt = f"""
    The user wants to control simulated smart home devices. We have these devices:
    - living_room_light (Living Room Light)
    - bedroom_ac (Bedroom AC, supports state, temperature)
    - kitchen_bulb (Kitchen Bulb)
    - smart_tv (Smart TV)
    
    {last_device_info}
    
    User query: "{Topic}"
    
    Analyze the user's intent. Output a strictly formatted JSON object with:
    - "device": "living_room_light" | "bedroom_ac" | "kitchen_bulb" | "smart_tv" | null
    - "action": "turn_on" | "turn_off" | "set_temp" | null
    - "value": integer (if setting AC temperature, else null)
    
    If the user implies a device (e.g. says "turn it off", "turn it on", "switch off", "turn off the ac", or "turn off ac"), resolve the device using the last controlled device or context.
    For example:
    - "turn it off" -> resolve to last controlled device ("{last_device_key or 'bedroom_ac'}")
    - "turn off ac" or "turn off the ac" -> resolve to "bedroom_ac"
    """
    
    data = _call_llm_extraction(prompt)
    if not data or not data.get("device") or not data.get("action"):
        return "I didn't recognize which smart device or action you wanted."

    device_key = data.get("device")
    action = data.get("action")
    value = data.get("value")

    if device_key not in devices:
        return f"Sorry, I couldn't find the smart device '{device_key}'."

    device = devices[device_key]
    device_name = device["name"]

    if action == "turn_on":
        device["state"] = "on"
        response = f"I've turned on the {device_name}."
    elif action == "turn_off":
        device["state"] = "off"
        response = f"I've turned off the {device_name}."
    elif action == "set_temp":
        if device_key == "bedroom_ac" and value:
            device["state"] = "on"
            device["temperature"] = int(value)
            response = f"I've set the Bedroom AC temperature to {value} degrees."
        else:
            response = "I can only adjust temperatures on the Bedroom AC."
    else:
        response = "I wasn't sure what action to perform."

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(devices, f, indent=4)

    # Save last controlled device
    try:
        with open(last_device_file, "w", encoding="utf-8") as f:
            json.dump({"last_device": device_key}, f, indent=4)
    except Exception as e:
        print(f"Failed to save last device: {e}")

    return response

def SetReminder(Topic):
    topic_lower = Topic.lower().strip()
    if any(word in topic_lower for word in ["clear", "delete", "remove", "cancel"]):
        reminders_file = os.path.join("Data", "reminders.json")
        try:
            with open(reminders_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)
            return "No problem! I've cleared all your reminders."
        except Exception as e:
            print(f"Failed to clear reminders: {e}")
            return "I ran into a small issue while trying to clear your reminders."

    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"""
    The user wants to set a reminder. Extract the reminder's description/message and the delay until it should fire.
    User query: "{Topic}"
    Current Date/Time: {current_time_str}
    
    Output a strictly formatted JSON object with keys:
    - "message": "What the user wants to be reminded of"
    - "delay_seconds": integer (the delay in seconds from the current time)
    
    If they didn't specify a time, default delay_seconds to 60.
    """
    
    data = _call_llm_extraction(prompt)
    if not data or data.get("delay_seconds") is None:
        return "I couldn't parse the reminder time."

    message = data.get("message")
    is_generic = False
    
    generic_words = [
        "reminder", "nothing", "none", "something", "reminder for nothing", 
        "no description", "no message", "unspecified", "not specified", "no description provided"
    ]
    
    if (not message or not message.strip() or 
        message.lower().strip() in generic_words or 
        any(word in message.lower() for word in ["no description", "no message", "not specified"])):
        message = "Reminder"
        is_generic = True
    else:
        message = message.strip()
        
    delay = int(data.get("delay_seconds", 60))
    
    trigger_timestamp = time.time() + delay
    trigger_time_str = datetime.datetime.fromtimestamp(trigger_timestamp).strftime("%I:%M %p")

    reminders_file = os.path.join("Data", "reminders.json")
    try:
        with open(reminders_file, "r", encoding="utf-8") as f:
            reminders = json.load(f)
            if not isinstance(reminders, list):
                reminders = []
    except Exception:
        reminders = []

    reminders.append({
        "time": trigger_timestamp,
        "message": message,
        "is_generic": is_generic,
        "notified": False
    })

    with open(reminders_file, "w", encoding="utf-8") as f:
        json.dump(reminders, f, indent=4)

    if delay < 60:
        time_text = f"{delay} seconds"
    elif delay < 3600:
        time_text = f"{delay // 60} minute" if delay // 60 == 1 else f"{delay // 60} minutes"
    else:
        time_text = f"{delay // 3600} hour" if delay // 3600 == 1 else f"{delay // 3600} hours"

    if is_generic:
        return f"Sure! I've set a reminder for you in {time_text} (at {trigger_time_str})."
    else:
        return f"No problem, I'll remind you to {message} in {time_text} (at {trigger_time_str})."


async def TranslateAndExecute(commamds: list[str]):

    funcs = []

    for command in commamds:

        if command.startswith("open "):

            if "open it" in command or "open file" == command:
                continue
            fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))
            funcs.append(fun)

        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)

        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play "))
            funcs.append(fun)

        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)

        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)

        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YoutubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)

        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)

        elif command.startswith("reminder "):
            fun = asyncio.to_thread(SetReminder, command.removeprefix("reminder "))
            funcs.append(fun)

        elif command.startswith("email "):
            fun = asyncio.to_thread(SendEmail, command.removeprefix("email "))
            funcs.append(fun)

        elif command.startswith("weather "):
            fun = asyncio.to_thread(GetWeather, command.removeprefix("weather "))
            funcs.append(fun)

        elif command.startswith("smarthome "):
            fun = asyncio.to_thread(ControlSmartHome, command.removeprefix("smarthome "))
            funcs.append(fun)

        else:
            print(f"No function Found For {command}")

    if not funcs:
        return

    results = await asyncio.gather(*funcs, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            print(f"Automation task failed: {result}")
            yield False
            continue

        if isinstance(result, str):
            yield result
        else:
            yield result

async def Automation(commands: list[str]):
    last_res = None
    async for result in TranslateAndExecute(commands):
        if isinstance(result, str):
            last_res = result

    return last_res
