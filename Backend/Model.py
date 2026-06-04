from rich import print
import os
import json


# funcs = [
#     "exit", "general", "realtime", "open", "close", "play",
#     "generate image", "system", "content", "google search",
#     "youtube search", "reminder"
# ]

COMMAND_PREFIXES = [
    ("youtube search", ["youtube search", "search youtube for", "search on youtube", "youtube"]),
    ("google search", ["google search", "search google for", "search on google", "search ", "google"]),
    ("generate image", [
        "generate image", "generator image", "generate picture", "create image",
        "create picture", "make image", "make picture", "draw", "generate a image",
        "generate an image", "edit image", "edit this image", "change this image",
        "transform this image", "stylize this image", "turn this image", "make this image",
        "animate me", "anime me"
    ]),
    ("open", ["open", "launch", "start", "visit", "go to", "browse to", "open website", "open site"]),
    ("close", ["close", "quit", "exit app", "stop app"]),
    ("play", ["play"]),
    ("content", [
        "write", "draft", "compose", "create content", "make a document",
        "write code", "generate code", "create code", "make code", "give me code",
        "give code", "code for", "program", "make a program", "create a program",
        "write a program", "write python", "generate python", "make python"
    ]),
    ("system", ["mute", "unmute", "volume up", "volume down", "increase volume", "decrease volume"]),
    ("reminder", ["remind me to", "remind me", "set reminder to", "set a reminder for", "set reminder", "set a reminder", "clear all reminders", "clear reminders", "clear reminder", "delete all reminders", "delete reminders", "delete reminder", "remove all reminders", "remove reminders", "remove reminder", "remind"]),
    ("email", ["send email to", "send an email to", "send email", "send an email", "email to", "email"]),
    ("weather", ["weather in", "weather of", "current weather in", "current weather", "temperature in", "how is the weather in", "how is the weather", "weather today in", "weather today", "what is the weather in", "what is the weather", "what's the weather in", "what's the weather", "show me the weather in", "show me the weather", "tell me about the weather", "tell me the weather", "tell me weather", "how's the weather", "weather info", "weather"]),
    ("smarthome", [
        "turn on", "turn off", "switch on", "switch off", 
        "turn it on", "turn it off", "switch it on", "switch it off",
        "set temperature of", "set ac to", "set air conditioner to", "toggle", "toggle it"
    ]),
]

REALTIME_HINTS = [
    "latest", "recent", "news", "headline", "headlines", "current", "today's",
    "today news", "weather", "stock", "price", "score", "election", "update",
    "updates", "prime minister", "president", "net worth", "networth"
]

GENERAL_CREATOR_HINTS = [
    "who are you", "what are you", "who created you", "who made you",
    "who built you", "your creator", "who is your creator"
]

PRONOUN_REFERENCES = ["he", "she", "him", "her", "they", "them", "it", "this", "that"]
CODE_HINTS = [
    " code", " coding", " program", " script", " python", " javascript", " html",
    " css", " java ", " c++", " calculator", " app in", " website code"
]
QUESTION_STARTS = [
    "what is", "what are", "who is", "who are", "why", "how", "when", "where",
    "explain", "tell me about"
]


def _normalize(text):
    normalized = str(text or "").lower().strip()
    for char in ".,?!;:-":
        normalized = normalized.replace(char, " ")
    return " ".join(normalized.split())


def _strip_prefix(text, prefixes):
    lowered = _normalize(text)
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix):].strip(" ,.")
    return text.strip()


def _split_tasks(prompt):
    parts = [prompt]
    for separator in [" and ", ","]:
        split_parts = []
        for part in parts:
            split_parts.extend(piece.strip() for piece in part.split(separator) if piece.strip())
        parts = split_parts
    return parts


def _is_last_message_weather():
    try:
        chat_file = os.path.join("Data", "ChatLog.json")
        if os.path.exists(chat_file):
            with open(chat_file, "r", encoding="utf-8") as f:
                chat_log = json.load(f)
            if chat_log:
                for entry in reversed(chat_log):
                    if isinstance(entry, dict) and entry.get("role") == "assistant":
                        content = entry.get("content", "").lower()
                        if "weather in" in content or "temperature of" in content or "forecast is" in content:
                            return True
                        break
    except Exception:
        pass
    return False


def _classify_single(part, full_prompt):
    lowered = _normalize(part)
    full_lowered = _normalize(full_prompt)

    if lowered in ["bye", "goodbye", "exit", "quit", "stop listening"]:
        return "exit"

    if _is_last_message_weather():
        cleaned_query = lowered.strip()
        words = cleaned_query.split()
        if len(words) <= 4:
            is_other_command = False
            for label, prefixes in COMMAND_PREFIXES:
                if label != "weather":
                    for prefix in prefixes:
                        if cleaned_query.startswith(prefix):
                            is_other_command = True
                            break
            if not is_other_command:
                location = cleaned_query
                for prep in ["what about in", "how about in", "what about", "how about", "and in", "in", "at", "for", "and"]:
                    if location.startswith(prep + " "):
                        location = location[len(prep):].strip()
                        break
                if location and location not in ["me", "my location", "here", "current location", "yes", "no", "ok", "sure", "yep", "nope"]:
                    return f"weather weather in {location}"

    for hint in GENERAL_CREATOR_HINTS:
        if hint in full_lowered:
            return f"general {full_prompt.strip()}"

    # Check for generic image requests or follow-ups (e.g. "show me", "in image pls", "try again")
    generic_image_commands = [
        "in image pls", "in image please", "in image", "in picture pls", "in picture please",
        "in picture", "draw it", "show me", "as an image", "create an image of this",
        "generate an image of this", "draw this", "make an image", "make it an image",
        "image pls", "image please", "picture pls", "picture please", "in image form",
        "generate an image of it", "generate it", "show me in image", "show me in picture",
        "show it", "show this", "try again", "regenerate", "redo", "make another", 
        "generate another", "not me try again", "its not me try again", "another one", 
        "try one more time", "one more time", "redo it", "its not me", "not me"
    ]
    if lowered in generic_image_commands or any(phrase in lowered for phrase in ["in image pls", "in picture pls", "show me in image", "show me in picture", "try again", "not me"]):
        clean_part = part.split("\n\n")[0].strip()
        return f"generate image {clean_part}"
    # Dynamic classification for general 'generate/create/make... image/photo' queries
    if (lowered.startswith("generate") or lowered.startswith("create") or lowered.startswith("make")) and any(word in lowered for word in ["image", "picture", "photo", "portrait", "illustration", "sketch", "drawing", "painting"]):
        clean_part = part.split("\n\n")[0].strip()
        return f"generate image {clean_part}"
    # Check if there is an attached image file in the full prompt context
    has_attached_image = "attached file" in full_prompt.lower() and any(ext in full_prompt.lower() for ext in [".png", ".jpg", ".jpeg", ".webp"])
    if has_attached_image:
        image_keywords = [
            "anime", "cartoon", "sketch", "drawing", "paint", "convert", "stylize", 
            "transform", "edit", "change", "animate", "avatar", "portrait", "illustration",
            "caricature", "pixel", "filter", "look like", "enhance", "enchance", "4k", 
            "hd", "resolution", "upscale", "background", "bg", "remove", "cutout", "transparent",
            "clear", "brighten", "fix"
        ]
        if any(keyword in lowered for keyword in image_keywords):
            clean_part = part.split("\n\n")[0].strip()
            return f"generate image {clean_part}"

    for label, prefixes in COMMAND_PREFIXES:
        for prefix in prefixes:
            if lowered.startswith(prefix):
                subject = _strip_prefix(part, [prefix])
                if label == "generate image" and subject.lower().startswith("of "):
                    subject = subject[3:].strip()
                if prefix in ["visit", "go to", "browse to", "open website", "open site"]:
                    return f"open website {subject}".strip()
                if label in ["smarthome", "reminder", "email", "weather"]:
                    return f"{label} {part.strip()}"
                return f"{label} {subject}".strip()

    weather_keywords = ["weather", "temperature", "forecast", "rain", "rainy", "snow", "cloudy", "sunny", "umbrella", "hot outside", "cold outside", "degree outside"]
    if any(kw in lowered for kw in weather_keywords):
        return f"weather {part.strip()}"

    if any(hint in lowered for hint in REALTIME_HINTS):
        return f"realtime {part.strip()}"

    image_edit_hints = ["anime style", "cartoon style", "stylize", "edit this", "transform this", "animate me"]
    if any(hint in lowered for hint in image_edit_hints):
        return f"generate image {part.strip()}"

    words = lowered.split()
    explicit_code_request = any(word in words for word in ["code", "program", "script", "make", "create", "generate", "write", "build"])
    informational_question = any(lowered.startswith(start) for start in QUESTION_STARTS)

    if any(hint in f" {lowered} " for hint in CODE_HINTS) and (explicit_code_request or not informational_question):
        return f"content {part.strip()}"

    words = lowered.split()
    if len(words) >= 3 and lowered.startswith("who is "):
        subject = lowered.removeprefix("who is ").strip()
        if subject and subject not in PRONOUN_REFERENCES:
            return f"realtime {part.strip()}"

    return f"general {part.strip()}"


def FirstLayerDMM(prompt: str = "test"):
    if not isinstance(prompt, str) or not prompt.strip():
        return ["general"]

    # Clean correction prefixes
    cleaned_prompt = prompt.lower().strip()
    correction_prefixes = ["i meant ", "no i meant ", "no actually ", "actually ", "no no ", "no "]
    for pref in correction_prefixes:
        if cleaned_prompt.startswith(pref):
            # Strip the prefix from the actual prompt to classify the core command
            prompt = prompt[len(pref):].strip(" ,.!?")
            break

    lowered = _normalize(prompt)
    is_email = any(lowered.startswith(prefix) for prefix in ["send email", "send an email", "email to", "email"])
    if is_email:
        decision = _classify_single(prompt, prompt)
        return [decision] if decision else [f"general {prompt}"]

    decisions = []
    for part in _split_tasks(prompt):
        decision = _classify_single(part, prompt)
        if decision and decision not in decisions:
            decisions.append(decision)

    return decisions or [f"general {prompt}"]


if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>> ")))
