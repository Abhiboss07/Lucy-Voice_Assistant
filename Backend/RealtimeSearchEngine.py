from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import requests


env_vars = dotenv_values(".env")

Username = env_vars.get("Username") or "User"
Assistantname = env_vars.get("Assistantname") or "Assistant"
CreatorName = env_vars.get("CreatorName") or Username
GroqAPIKey = env_vars.get("GroqAPIKey")
GroqModel = env_vars.get("GroqModel") or "llama-3.3-70b-versatile"
GeminiAPIKey = env_vars.get("GeminiAPIKey")
GeminiModel = env_vars.get("GeminiModel") or "gemini-2.5-flash-lite"
AssistantLanguage = env_vars.get("AssistantLanguage") or "English unless the user speaks Hindi or Hinglish"
ChatHistoryLimit = int(env_vars.get("ChatHistoryLimit") or 4)
RealtimeMaxResponseTokens = int(env_vars.get("RealtimeMaxResponseTokens") or 450)

client = Groq(api_key=GroqAPIKey) if GroqAPIKey else None




System = f"""You are {Assistantname}, a warm, highly conversational, and human-like AI companion with web search context.
Be natural, warm, friendly, and engaging. Speak as a human companion would—express polite interest, use conversational transitions, and keep a friendly and natural flow. Avoid dry, robotic, or overly structured bullet points unless specifically requested. Feel free to use warm greeting terms or express polite curiosity to make interactions feel human and alive.
Reply in English unless the user uses Hindi or Hinglish; then match them naturally.
Do not address the user by name/title unless asked.
If asked who created, made, or built you, say you were created by {CreatorName}.
Prioritize answering from the provided search data when it contains relevant information. If the search data is empty, not available, or lacks the answer, you MUST answer the question accurately using your own general knowledge. Never say that the search results are not available or refuse to answer; always provide a helpful and direct answer based on your knowledge."""

# try:
#     with open(r"Data\ChatLog.json", "r") as f:
#         messages = load(f)
# except:
#     with open(r"Data\ChatLog.json", "w") as f:
#         dump([], f)
messages = []

def fallback_google_search(query):
    import urllib.parse
    from bs4 import BeautifulSoup
    
    fallback_results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"
        }
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for g in soup.find_all("div", class_="g")[:5]:
                title_elem = g.find("h3")
                desc_elem = g.find("div", class_="VwiC3b") or g.find("div", class_="kb0Bzd")
                
                if title_elem:
                    title = title_elem.get_text()
                    desc = desc_elem.get_text() if desc_elem else "No description available."
                    fallback_results.append((title, desc))
    except Exception as e:
        print(f"Fallback Google search failed: {e}")
    return fallback_results

def fallback_ddg_search(query):
    import urllib.parse
    from bs4 import BeautifulSoup
    
    fallback_results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"
        }
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for result in soup.find_all("div", class_="result")[:5]:
                title_elem = result.find("a", class_="result__a")
                desc_elem = result.find("a", class_="result__snippet")
                
                if title_elem:
                    title = title_elem.get_text().strip()
                    desc = desc_elem.get_text().strip() if desc_elem else "No description available."
                    fallback_results.append((title, desc))
    except Exception as e:
        print(f"Fallback DDG search failed: {e}")
    return fallback_results

def fallback_yahoo_search(query):
    import urllib.parse
    from bs4 import BeautifulSoup
    
    fallback_results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"
        }
        url = f"https://search.yahoo.com/search?q={urllib.parse.quote(query)}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Match any element with 'algo' in its class name (e.g. 'algo', 'dd algo')
            elements = soup.find_all(class_=lambda x: x and 'algo' in x)
            
            # Fallback if no algo class is found: search for h3 elements with links
            if not elements:
                elements = []
                for h3 in soup.find_all("h3"):
                    a_tag = h3.find("a")
                    if a_tag and a_tag.get("href") and not a_tag.get("href").startswith(("/search", "https://search.yahoo.com")):
                        elements.append(h3.parent.parent or h3.parent)
            
            for elem in elements[:5]:
                title_elem = elem.find("h3")
                desc_elem = elem.find("div", class_="compText") or elem.find("span", class_="fc-tombstone") or elem.find("p") or elem.find(class_=lambda x: x and 'compText' in x)
                
                if title_elem:
                    title = title_elem.get_text().strip()
                    desc = desc_elem.get_text().strip() if desc_elem else "No description available."
                    # De-duplicate
                    if (title, desc) not in fallback_results:
                        fallback_results.append((title, desc))
    except Exception as e:
        print(f"Fallback Yahoo search failed: {e}")
    return fallback_results

def fallback_wiki_search(query):
    import urllib.parse
    from bs4 import BeautifulSoup
    
    fallback_results = []
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&origin=*"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            search_results = data.get("query", {}).get("search", [])
            for res in search_results[:5]:
                title = res.get("title")
                snippet = BeautifulSoup(res.get("snippet", ""), "html.parser").get_text().strip()
                fallback_results.append((title, snippet))
    except Exception as e:
        print(f"Fallback Wikipedia search failed: {e}")
    return fallback_results

def GoogleSearch(query):
    results = []
    try:
        results_obj = list(search(query, advanced=True, num_results=5))
        for r in results_obj:
            results.append((r.title, r.description))
    except Exception as e:
        print(f"Google search package failed: {e}")
        
    if not results:
        print("Attempting fallback Yahoo search scraper...")
        results = fallback_yahoo_search(query)
        
    if not results:
        print("Attempting fallback Google search scraper...")
        results = fallback_google_search(query)
        
    if not results:
        print("Attempting fallback DuckDuckGo search scraper...")
        results = fallback_ddg_search(query)

    if not results:
        print("Attempting fallback Wikipedia search API...")
        results = fallback_wiki_search(query)

    Answer = f"The search results for '{query}' are:\n[start]\n"

    for title, desc in results:
        Answer += f"Title: {title}\nDescription: {desc}\n\n"

    Answer += "[end]"
    return Answer


SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can i help you?"}
]


def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data += f"Use This Real-Time Information if needed,\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
    return data


def RecentMessages(chat_messages):
    return chat_messages[-ChatHistoryLimit:] if ChatHistoryLimit > 0 else []


def _gemini_contents(chat_messages):
    contents = []
    for message in chat_messages:
        role = "model" if message.get("role") == "assistant" else "user"
        content = str(message.get("content", "")).strip()
        if content:
            contents.append({"role": role, "parts": [{"text": content}]})
    return contents


def _gemini_chat(chat_messages, search_context):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GeminiModel}:generateContent"
    response = requests.post(
        url,
        params={"key": GeminiAPIKey},
        json={
            "systemInstruction": {"parts": [{"text": f"{System}\n{search_context}\n{Information()}"}]},
            "contents": _gemini_contents(chat_messages),
            "generationConfig": {
                "temperature": 0.7,
                "topP": 1,
                "maxOutputTokens": RealtimeMaxResponseTokens,
            },
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates") or []
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    return "".join(part.get("text", "") for part in parts).strip()


def _groq_chat(chat_messages, search_context):
    if client is None:
        return "No chat API key is configured. Add GeminiAPIKey or GroqAPIKey to .env."

    combined_system = f"{System}\n\n{search_context}\n\n{Information()}"
    messages_payload = [{"role": "system", "content": combined_system}] + chat_messages

    completion = client.chat.completions.create(
        model=GroqModel,
        messages=messages_payload,
        temperature=0.7,
        max_tokens=RealtimeMaxResponseTokens,
        top_p=1,
        stream=True,
        stop=None
    )

    answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            answer += chunk.choices[0].delta.content
    return answer.strip().replace("</s>", "")


def RealtimeSearchEngine(prompt):
    global messages
    if not GeminiAPIKey and client is None:
        return "No chat API key is configured. Add GeminiAPIKey or GroqAPIKey to the .env file."

    try:
        with open(r"Data\ChatLog.json", "r", encoding="utf-8") as f:
            messages = load(f)
            if not isinstance(messages, list):
                messages = []
    except Exception:
        messages = []

    messages.append({"role": "user", "content": f"{prompt}"})
    request_messages = RecentMessages(messages)
    search_context = GoogleSearch(prompt)

    try:
        try:
            if GeminiAPIKey:
                Answer = _gemini_chat(request_messages, search_context)
            else:
                Answer = _groq_chat(request_messages, search_context)
        except requests.HTTPError as e:
            if client is not None:
                print(f"Gemini realtime failed, falling back to Groq: {e}")
                try:
                    Answer = _groq_chat(request_messages, search_context)
                except Exception as fallback_error:
                    print(f"Groq realtime fallback failed: {fallback_error}")
                    return "I am having trouble connecting right now. Please try again in a few minutes."
            else:
                print(f"Gemini realtime failed and no Groq fallback is configured: {e}")
                return "I am having trouble connecting right now. Please try again in a few minutes."
        except Exception as e:
            if client is not None:
                print(f"Primary realtime provider failed, falling back to Groq: {e}")
                try:
                    Answer = _groq_chat(request_messages, search_context)
                except Exception as fallback_error:
                    print(f"Groq realtime fallback failed: {fallback_error}")
                    return "I am having trouble connecting right now. Please try again in a few minutes."
            else:
                print(f"Realtime provider failed and no fallback is configured: {e}")
                return "I am having trouble connecting right now. Please try again in a few minutes."

        messages.append({"role": "assistant", "content": Answer})

        with open(r"Data\ChatLog.json", "w", encoding="utf-8") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer=Answer)
    except Exception as e:
        print(f"Realtime answer failed: {e}")
        return "I could not complete the realtime search response. Please try again."
                          

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))

