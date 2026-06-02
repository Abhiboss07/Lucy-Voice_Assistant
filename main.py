from Frontend.GUI import (
Assistantname,
GraphicalUserInterface,
SetAssistantStatus,
ShowTextToScreen,
TempDirectoryPath,
SetMicrophoneStatus,
AnswerModifier,
QueryModifier,
GetMicrophoneStatus,
GetAssistantStatus )
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.TextToSpeech import TextToSpeech, StopTextToSpeech
from Backend.Chatbot import ChatBot
from dotenv import dotenv_values
from asyncio import run
from time import sleep, time
import subprocess
import threading
import json
import os
import sys

env_vars = dotenv_values(".env")
Username = env_vars.get("Username") or "User"
Assistantname = env_vars.get("Assistantname") or Assistantname or "Lucy"
WAKE_WORDS = [
    word.strip().lower()
    for word in (env_vars.get("WakeWords") or f"hey {Assistantname}, {Assistantname}").split(",")
    if word.strip()
]
INTERRUPT_WORDS = [
    word.strip().lower()
    for word in (env_vars.get("InterruptWords") or f"stop, wait, cancel, nevermind, ruko, ruk jao, बस, hey {Assistantname}, {Assistantname}").split(",")
    if word.strip()
]
DefaultMessage = f'''{Username} : Hello {Assistantname}, how are you?
{Assistantname} : I'm doing well. How can I help?'''

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search", "reminder", "email", "weather", "smarthome"]
CHAT_LOG_PATH = os.path.join("Data", "ChatLog.json")
SESSION_LOG_PATH = os.path.join("Data", "CurrentSession.json")
IMAGE_GENERATION_STATUS_PATH = os.path.join("Frontend", "Files", "ImageGeneration.data")
TYPED_QUERY_PATH = os.path.join("Frontend", "Files", "TypedQuery.data")
CONTROL_PATH = os.path.join("Frontend", "Files", "Control.data")
speech_lock = threading.Lock()
LONG_SPEECH_CHAR_LIMIT = int(env_vars.get("LongSpeechCharLimit") or 420)
LONG_SPEECH_SENTENCE_LIMIT = int(env_vars.get("LongSpeechSentenceLimit") or 3)

def _safe_set_status(status):
    try:
        SetAssistantStatus(status)
    except Exception as e:
        print(f"Error setting assistant status to {status!r}: {e}")

def _safe_text_to_speech(answer):
    try:
        TextToSpeech(answer)
    except Exception as e:
        print(f"Text-to-speech failed: {e}")

def _cleanup_subprocesses():
    subprocesses[:] = [process for process in subprocesses if process.poll() is None]

def ResetCurrentSession():
    os.makedirs("Data", exist_ok=True)
    with open(SESSION_LOG_PATH, "w", encoding="utf-8") as file:
        json.dump([], file)

def SaveSessionMessage(role, content):
    try:
        with open(SESSION_LOG_PATH, "r", encoding="utf-8") as file:
            session_messages = json.load(file)
            if not isinstance(session_messages, list):
                session_messages = []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        session_messages = []

    session_messages.append({"role": role, "content": content})

    with open(SESSION_LOG_PATH, "w", encoding="utf-8") as file:
        json.dump(session_messages, file, indent=4)

def ShowDefaultChatIfNoChats():
    try:
        with open(CHAT_LOG_PATH, "r", encoding='utf-8') as file:
            has_chat_log = len(file.read().strip()) >= 5
    except (FileNotFoundError, OSError):
        has_chat_log = False

    if not has_chat_log:
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    try:
        with open(CHAT_LOG_PATH, 'r', encoding='utf-8') as file:
            chatlog_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    if not isinstance(chatlog_data, list):
        return []

    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    if not json_data:
        return

    formatted_chatlog = ""
    for entry in json_data:
        if not isinstance(entry, dict):
            continue

        role = entry.get("role")
        content = entry.get("content", "")

        if role == "user":
            formatted_chatlog += f"User: {content}\n"
        elif role == "assistant":
            formatted_chatlog += f"Assistant: {content}\n"

    formatted_chatlog = formatted_chatlog.replace("User",Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant",Assistantname + " ")

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatOnGUI():
    with open(TempDirectoryPath('Database.data'),"r", encoding='utf-8') as file:
        Data = file.read()

    if len(str(Data))>0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        with open(TempDirectoryPath('Response.data'),"w", encoding='utf-8') as file:
            file.write(result)

def InitialExecution():
    SetMicrophoneStatus("True")
    ResetCurrentSession()
    try:
        from Backend.FileContext import clear_all_uploads
        clear_all_uploads()
    except Exception as e:
        print(f"Failed to clear uploads on startup: {e}")
    ShowTextToScreen(f"{Assistantname} : Hey there! I'm {Assistantname}. How can I help you today?")

def _contains_phrase(text, phrases):
    normalized = _normalize_for_command(text)
    return any(phrase in normalized for phrase in phrases)

def _normalize_for_command(text):
    normalized = str(text).lower()
    for char in ".,!?;:":
        normalized = normalized.replace(char, " ")
    return " ".join(normalized.split())

def _remove_wake_phrase(text):
    query = str(text).strip()
    lowered = _normalize_for_command(query)

    for wake_word in sorted(WAKE_WORDS, key=len, reverse=True):
        if lowered.startswith(wake_word):
            return query[len(wake_word):].strip(" ,.!?")

    return query

def _read_and_clear(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = file.read().strip()
        if data:
            with open(path, "w", encoding="utf-8") as file:
                file.write("")
        return data
    except OSError:
        return ""

def _peek_control():
    try:
        with open(CONTROL_PATH, "r", encoding="utf-8") as file:
            return file.read().strip().lower()
    except OSError:
        return ""

def _consume_stop_request():
    if _peek_control() == "stop":
        _read_and_clear(CONTROL_PATH)
        StopTextToSpeech()
        return True
    return False

def _consume_listen_request():
    if _peek_control() == "listen":
        _read_and_clear(CONTROL_PATH)
        return True
    return False

def _listen_once(status, show_errors=True, stop_when_muted=True):
    _safe_set_status(status)
    try:
        with speech_lock:
            return SpeechRecognition(
                should_stop=lambda: _peek_control() == "stop" or (stop_when_muted and GetMicrophoneStatus() != "True")
            )
    except TimeoutError:
        return ""
    except Exception as e:
        message = str(e).lower()
        if "aborted" in message:
            _safe_set_status("Mic ready")
            return ""
        if "no-speech" in message:
            _safe_set_status("Mic ready")
            return ""

        print(f"Speech recognition failed: {e}")
        if show_errors:
            ShowTextToScreen(f"{Assistantname} : Speech recognition failed: {e}")
        _safe_set_status("Mic ready")
        return ""

def _start_interruption_listener():
    interrupted = threading.Event()

    def listen_for_interrupt():
        while not interrupted.is_set():
            if _consume_stop_request():
                interrupted.set()
                _safe_set_status("Interrupted...")
                break

            try:
                with speech_lock:
                    heard = SpeechRecognition(
                        should_stop=lambda: interrupted.is_set() or _peek_control() in ["stop", "listen"],
                        timeout=2.5
                    )
            except Exception:
                heard = ""

            if interrupted.is_set():
                break

            if heard and _contains_phrase(heard, INTERRUPT_WORDS):
                StopTextToSpeech()
                interrupted.set()
                _safe_set_status("Interrupted...")
                break

    listener = threading.Thread(target=listen_for_interrupt, daemon=True)
    listener.start()
    return interrupted

def _speak_with_interruption(answer):
    interrupt_event = _start_interruption_listener()

    def should_continue(_playing=True):
        control = _peek_control()
        if control == "listen":
            interrupt_event.set()
            StopTextToSpeech()
            return False

        if control == "stop":
            interrupt_event.set()
            _read_and_clear(CONTROL_PATH)
            StopTextToSpeech()
            SetMicrophoneStatus("False")
            _safe_set_status("Interrupted...")
            return False

        if GetMicrophoneStatus() != "True":
            interrupt_event.set()
            StopTextToSpeech()
            _safe_set_status("Muted")
            return False

        return True

    try:
        TextToSpeech(answer, func=should_continue)
    finally:
        interrupt_event.set()

def _split_for_spoken_followup(answer):
    text = str(answer or "").strip()
    if len(text) <= LONG_SPEECH_CHAR_LIMIT:
        return text, ""

    sentences = []
    current = ""

    for char in text:
        current += char
        if char in ".!?":
            sentence = current.strip()
            if sentence:
                sentences.append(sentence)
            current = ""

    if current.strip():
        sentences.append(current.strip())

    if len(sentences) <= LONG_SPEECH_SENTENCE_LIMIT:
        first_part = text[:LONG_SPEECH_CHAR_LIMIT].rsplit(" ", 1)[0].strip()
        return first_part, text[len(first_part):].strip()

    first_sentences = sentences[:LONG_SPEECH_SENTENCE_LIMIT]
    first_part = " ".join(first_sentences).strip()
    remaining = text[len(first_part):].strip()
    return first_part, remaining

def _wants_spoken_continuation(response):
    normalized = _normalize_for_command(response)
    yes_words = ["yes", "yeah", "yep", "continue", "finish", "go on", "speak", "read it", "read everything", "haan", "ha"]
    no_words = ["no", "nope", "stop", "skip", "chat", "screen", "i will read", "read myself", "bas"]

    if any(word in normalized for word in no_words):
        return False
    if any(word in normalized for word in yes_words):
        return True
    return False

def _speak_answer(answer):
    first_part, remaining = _split_for_spoken_followup(answer)

    if not remaining:
        _speak_with_interruption(first_part)
        return

    prompt = (
        f"{first_part} I have more to say. "
        "Should I finish speaking it, or would you rather read the rest on the screen?"
    )
    _speak_with_interruption(prompt)

    reply = _listen_once("Listening...", show_errors=False, stop_when_muted=True)
    if _wants_spoken_continuation(reply):
        _safe_set_status("Answering...")
        _speak_with_interruption(remaining)
    else:
        _safe_set_status("Available...")

def GetGenericImagePrompt(prompt: str) -> str:
    generic_phrases = [
        "in image pls", "in image please", "in image", "in picture pls", "in picture please",
        "in picture", "draw it", "show me", "as an image", "create an image of this",
        "generate an image of this", "draw this", "make an image", "make it an image",
        "image pls", "image please", "picture pls", "picture please", "in image form",
        "in image pls?", "in image please?", "draw it?", "show me?", "image pls?", "in image pls pls",
        "it", "this", "that", "of it", "of this", "of that", "show it", "show this", "show me",
        "try again", "regenerate", "redo", "make another", "generate another",
        "not me try again", "its not me try again", "another one", "try one more time",
        "one more time", "redo it", "its not me", "not me", "try again?", "regenerate?"
    ]
    cleaned = str(prompt).lower().strip().replace("?", "").replace(".", "").replace("!", "")
    
    if cleaned in generic_phrases:
        chat_log = ReadChatLogJson()
        
        # 1. Search for a previous image generation log to retry/regenerate!
        for entry in reversed(chat_log):
            if isinstance(entry, dict) and entry.get("role") == "assistant":
                content = entry.get("content", "").strip()
                if "Generating an image of" in content:
                    try:
                        subject = content.split("Generating an image of", 1)[1].split("now", 1)[0].strip()
                        if subject:
                            return subject
                    except Exception:
                        pass

        # 2. Fallback: Search for the last rich text description from the chatbot
        for entry in reversed(chat_log):
            if isinstance(entry, dict) and entry.get("role") == "assistant":
                content = entry.get("content", "").strip()
                if content:
                    if " : " in content:
                        content = content.split(" : ", 1)[1].strip()
                    # If the assistant content itself is a generic message or warning, skip it
                    if not any(warning in content.lower() for warning in ["generating an image", "speech recognition failed", "i cannot generate", "i could not generate"]):
                        return content
    return prompt

def HandleQuery(Query):
    _cleanup_subprocesses()
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    if not isinstance(Query, str) or not Query.strip():
        _safe_set_status("Available...")
        return False

    ShowTextToScreen(f"{Username} : {Query}")
    SaveSessionMessage("user", Query)
    _safe_set_status("Thinking...")

    # Check if there is an active email conversation state!
    state_file = os.path.join("Data", "email_state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                email_state = json.load(f)
            
            if email_state:
                # If the state is 'composed', we check if the user is trying to modify it
                if email_state.get("state") == "composed":
                    from Backend.Automation import HandleDraftModification
                    ans, next_state = HandleDraftModification(Query, email_state)
                    if ans is not None:
                        # Save modified state and respond!
                        with open(state_file, "w", encoding="utf-8") as f:
                            json.dump(next_state, f, indent=4)
                        ShowTextToScreen(f"{Assistantname} : {ans}")
                        SaveSessionMessage("assistant", ans)
                        _safe_set_status("Answering...")
                        _speak_answer(ans)
                        return True
                    else:
                        # Check expiry (10 minutes)
                        last_active = email_state.get("last_active", 0)
                        if time() - last_active > 600:
                            try:
                                os.remove(state_file)
                            except Exception:
                                pass
                
                # Normal state machine flow (if still has a state)
                elif email_state.get("state"):
                    from Backend.Automation import HandleEmailState
                    ans, next_state = HandleEmailState(Query, email_state)
                    
                    if next_state.get("state") is None:
                        try:
                            os.remove(state_file)
                        except Exception:
                            pass
                    else:
                        with open(state_file, "w", encoding="utf-8") as f:
                            json.dump(next_state, f, indent=4)
                            
                    ShowTextToScreen(f"{Assistantname} : {ans}")
                    SaveSessionMessage("assistant", ans)
                    _safe_set_status("Answering...")
                    _speak_answer(ans)
                    return True
        except Exception as e:
            print(f"Error in email state handling: {e}")

    try:
        Decision = FirstLayerDMM(Query)
    except Exception as e:
        print(f"Decision model failed: {e}")
        _safe_set_status("Available...")
        return False

    if not isinstance(Decision, (list, tuple)):
        print(f"Invalid decision payload: {Decision!r}")
        _safe_set_status("Available...")
        return False

    print("")
    print(f"Decision : {Decision}")
    print("")

    R = any(i.startswith("realtime") for i in Decision if isinstance(i, str))

    Merged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if isinstance(i, str) and (i.startswith("general") or i.startswith("realtime"))]
    )

    for queries in Decision:
        if isinstance(queries, str) and queries.startswith("generate "):
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    for queries in Decision:
        if not TaskExecution:
            if isinstance(queries, str) and any(queries.startswith(func) for func in Functions):
                try:
                    ans = run(Automation(list(Decision)))
                    TaskExecution = True
                    if isinstance(ans, str) and ans:
                        ShowTextToScreen(f"{Assistantname} : {ans}")
                        SaveSessionMessage("assistant", ans)
                        _safe_set_status("Answering...")
                        _speak_answer(ans)
                except Exception as e:
                    print(f"Automation failed: {e}")

    if ImageExecution == True:
        image_prompt = ImageGenerationQuery.replace("generate image", "", 1).strip()
        if image_prompt.lower().startswith("of "):
            image_prompt = image_prompt[3:].strip()

        # Resolve conversational follow-up requests (e.g. "in image pls" -> last response text)
        resolved = GetGenericImagePrompt(image_prompt)
        if resolved != image_prompt:
            image_prompt = resolved
            ImageGenerationQuery = f"generate image {image_prompt}"

        if not image_prompt:
            Answer = "What should I generate an image of?"
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SaveSessionMessage("assistant", Answer)
            _safe_set_status("Available...")
            _speak_with_interruption(Answer)
            return True

        with open(IMAGE_GENERATION_STATUS_PATH, "w", encoding="utf-8") as file:
            file.write(f"{ImageGenerationQuery},True")

        try:
            with open(TempDirectoryPath("ImageResult.data"), "w", encoding="utf-8") as file:
                file.write(f"loading|{image_prompt}")
        except Exception as e:
            print(f"Error writing loading state to ImageResult.data: {e}")

        
        try:
            os.makedirs("Data", exist_ok=True)
            image_log = open(os.path.join("Data", "ImageGeneration.log"), "a", encoding="utf-8")
            p1 = subprocess.Popen(
                [sys.executable, os.path.join('Backend', 'ImageGeneration.py')],
                stdout=image_log,
                stderr=image_log,
                stdin=subprocess.DEVNULL,
                shell=False
            )
            image_log.close()
            
            subprocesses.append(p1)
            Answer = f"Generating an image of {image_prompt or 'that'} now. I will open it when it is ready."
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SaveSessionMessage("assistant", Answer)
            _safe_set_status("Generating image...")
            _speak_with_interruption(Answer)
            return True

        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")

    if R:

        _safe_set_status("Searching...")
        try:
            Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        except Exception as e:
            print(f"Realtime search failed: {e}")
            _safe_set_status("Available...")
            return False

        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SaveSessionMessage("assistant", Answer)
        _safe_set_status("Answering...")
        _speak_answer(Answer)
        return True
    
    else:
        for Queries in Decision:

            if isinstance(Queries, str) and Queries.startswith("general"):
                _safe_set_status("Thinking...")
                QueryFinal = Queries.replace("general ","", 1)
                try:
                    Answer = ChatBot(QueryModifier(QueryFinal))
                except Exception as e:
                    print(f"Chatbot failed: {e}")
                    _safe_set_status("Available...")
                    return False

                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SaveSessionMessage("assistant", Answer)
                _safe_set_status("Answering...")
                _speak_answer(Answer)
                return True
            
            elif isinstance(Queries, str) and Queries.startswith("realtime"):
                _safe_set_status("Searching...")
                QueryFinal = Queries.replace("realtime ","", 1)
                try:
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                except Exception as e:
                    print(f"Realtime search failed: {e}")
                    _safe_set_status("Available...")
                    return False

                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SaveSessionMessage("assistant", Answer)
                _safe_set_status("Answering...")
                _speak_answer(Answer)
                return True
            
            elif isinstance(Queries, str) and Queries.startswith("exit"):
                QueryFinal = "Okay, Bye!"
                try:
                    Answer = ChatBot(QueryModifier(QueryFinal))
                except Exception as e:
                    print(f"Chatbot failed during exit: {e}")
                    Answer = QueryFinal

                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SaveSessionMessage("assistant", Answer)
                _safe_set_status("Answering...")
                _speak_answer(Answer)
                _safe_set_status("Available...")
                os._exit(0)

    _safe_set_status("Available...")
    return False

def MainExecution():
    Query = _listen_once("Listening...", show_errors=True, stop_when_muted=False)
    return HandleQuery(Query)

def ConversationLoop(first_query=""):
    query = str(first_query or "").strip()

    while GetMicrophoneStatus() == "True":
        control = _peek_control()
        if control == "listen":
            _read_and_clear(CONTROL_PATH)

        if _consume_stop_request():
            SetMicrophoneStatus("False")
            _safe_set_status("Muted")
            break

        typed_query = _read_and_clear(TYPED_QUERY_PATH)
        if typed_query:
            StopTextToSpeech()
            HandleQuery(typed_query)
            continue

        if not query:
            query = _listen_once("Listening...", show_errors=True)

        if query:
            HandleQuery(query)
            query = ""
        else:
            sleep(0.05)

def FirstThread():

    while True:
        if _consume_stop_request():
            SetMicrophoneStatus("False")
            _safe_set_status("Muted")

        typed_query = _read_and_clear(TYPED_QUERY_PATH)
        if typed_query:
            StopTextToSpeech()
            HandleQuery(typed_query)
            continue

        if _consume_listen_request():
            StopTextToSpeech()
            ConversationLoop()
            continue

        CurrentStatus = GetMicrophoneStatus()

        if CurrentStatus == "True":
            try:
                heard = _listen_once(f"Wake mode: say '{WAKE_WORDS[0]}'", show_errors=False)
                if not heard:
                    sleep(0.05)
                    continue

                if not _contains_phrase(heard, WAKE_WORDS):
                    sleep(0.05)
                    continue

                Query = _remove_wake_phrase(heard)
                if not Query:
                    Query = _listen_once("Listening...")

                ConversationLoop(Query)
            except Exception as e:
                print(f"Main execution failed: {e}")
                _safe_set_status("Available...")

        else:
            _safe_set_status("Muted")
            sleep(0.25)

def ReminderEngineThread():
    reminders_file = os.path.join("Data", "reminders.json")
    while True:
        try:
            if os.path.exists(reminders_file):
                with open(reminders_file, "r", encoding="utf-8") as f:
                    reminders = json.load(f)
                    if not isinstance(reminders, list):
                        reminders = []
                
                updated = False
                now = time()
                
                for r in reminders:
                    if not r.get("notified") and r.get("time") <= now:
                        r["notified"] = True
                        updated = True
                        message = r.get("message")
                        is_generic = r.get("is_generic", False)
                        
                        # Friendly, human-like reminder notifications
                        if is_generic or not message or message.lower().strip() in ["reminder", "nothing", "none", "something", "reminder for nothing"]:
                            notification_text = "Just a friendly heads-up: your reminder is due!"
                            spoken_text = "Hey there! Just a friendly heads-up, the reminder you set is due."
                        else:
                            notification_text = f"Friendly Reminder: {message}"
                            spoken_text = f"Hey! Just a quick reminder to: {message}."
                        
                        print(f"\n[REMINDER DUE] {notification_text}\n")
                        
                        ShowTextToScreen(f"{Assistantname} : {notification_text}")
                        SaveSessionMessage("assistant", notification_text)
                        
                        threading.Thread(target=_speak_with_interruption, args=(spoken_text,), daemon=True).start()
                
                if updated:
                    with open(reminders_file, "w", encoding="utf-8") as f:
                        json.dump(reminders, f, indent=4)
        except Exception as e:
            print(f"Error in Reminder Engine: {e}")
        
        sleep(2)

def SecondThread():

    GraphicalUserInterface()

if __name__ == "__main__":
    InitialExecution()
    
    # Start reminder engine thread
    reminder_thread = threading.Thread(target=ReminderEngineThread, daemon=True)
    reminder_thread.start()
    
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
    
