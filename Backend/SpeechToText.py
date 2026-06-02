from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidSessionIdException, NoSuchWindowException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt
from time import sleep, time
import atexit
import shutil
import tempfile


env_vars = dotenv_values(".env")

Inputlanguage = env_vars.get("Inputlanguage") or "en"
SpeechTimeout = float(env_vars.get("SpeechTimeout") or 10)

HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <p id="final"></p>
    <p id="error"></p>
    <script>
        const output = document.getElementById('output');
        const finalOutput = document.getElementById('final');
        const error = document.getElementById('error');
        let recognition;
        let shouldListen = false;
        let finalTranscript = "";
        let interimTranscript = "";

        function startRecognition() {
            output.textContent = "";
            finalOutput.textContent = "";
            error.textContent = "";
            finalTranscript = "";
            interimTranscript = "";
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                error.textContent = "Speech recognition is not supported in this browser.";
                return;
            }

            shouldListen = true;
            recognition = new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;
            recognition.interimResults = true;

            recognition.onresult = function(event) {
                interimTranscript = "";
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + " ";
                    } else {
                        interimTranscript += transcript;
                    }
                }
                output.textContent = (finalTranscript + interimTranscript).trim();
                finalOutput.textContent = finalTranscript.trim();
            };

            recognition.onerror = function(event) {
                error.textContent = event.error || "unknown speech recognition error";
                shouldListen = false;
            };

            recognition.onend = function() {
                if (shouldListen) {
                    try {
                        recognition.start();
                    } catch (event) {
                        error.textContent = event.message || "speech recognition restart failed";
                        shouldListen = false;
                    }
                }
            };
            try {
                recognition.start();
            } catch (event) {
                error.textContent = event.message || "speech recognition start failed";
                shouldListen = false;
            }
        }

        function stopRecognition() {
            shouldListen = false;
            if (recognition) {
                recognition.stop();
            }
            output.innerHTML = "";
            finalOutput.innerHTML = "";
        }
    </script>
</body>
</html>'''

HtmlCode = str(HtmlCode).replace("recognition.lang = '';", f"recognition.lang = '{Inputlanguage}';")

os.makedirs("Data", exist_ok=True)
with open(r"Data\SpeechToText.html", "w", encoding="utf-8") as f:
    f.write(HtmlCode)


current_dir = os.getcwd()

Link = f"{current_dir}/Data/SpeechToText.html"
ChromeProfilePath = None


def _cleanup_chrome_profile():
    global ChromeProfilePath
    if ChromeProfilePath is not None:
        try:
            shutil.rmtree(ChromeProfilePath, ignore_errors=True)
        except Exception:
            pass


atexit.register(_cleanup_chrome_profile)


def _build_chrome_options():
    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument(f"--user-data-dir={ChromeProfilePath}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument("--remote-debugging-port=0")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--window-size=360,220")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_settings.popups": 0,
        },
    )
    return chrome_options

driver = None

TempDirPath = rf"{current_dir}/Frontend/Files"

def _close_driver():
    global driver
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass
    driver = None


def _get_driver():
    global driver, ChromeProfilePath
    if driver is not None:
        try:
            _ = driver.current_window_handle
            return driver
        except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
            _close_driver()

    if driver is None:
        if ChromeProfilePath is None:
            ChromeProfilePath = tempfile.mkdtemp(prefix="flock-chrome-profile-")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=_build_chrome_options())
    return driver


def _start_browser_recognition():
    driver = _get_driver()
    driver.get("file:///" + Link)
    driver.find_element(by=By.ID, value="start").click()
    return driver


def SetAssistantStatus(Status):
    with open(rf'{TempDirPath}/Status.data', 'w', encoding='utf-8') as file:
        file.write(Status)


def QueryModifier(Query):
    new_query = Query.lower().strip()
    if not new_query:
        return ""

    query_words = new_query.split()
    question_words = ["what", "who", "where", "when", "why", "how", "is", "are", "do", "does", "did", "can", "could", "should", "would", "which", "whose", "has", "have", "had", "whom", "can", "may", "might", "must", "shall", "will"]


    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in [".", "?", "!"]:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in [".", "?", "!"]:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    return new_query.capitalize()

# def UniversalTranslate(Text):
#     english_translation = mt.translate(Text, "en", "auto")
#     return english_translation.capitalize()

def SpeechRecognition(should_stop=None, timeout=None):
    driver = _start_browser_recognition()
    started_at = time()
    timeout = SpeechTimeout if timeout is None else float(timeout)

    while True:
        try:
            if should_stop and should_stop():
                try:
                    driver.find_element(by=By.ID, value="end").click()
                except Exception:
                    pass
                raise TimeoutError("Speech recognition stopped.")

            Text = driver.find_element(by=By.ID, value="output").text
            FinalText = driver.find_element(by=By.ID, value="final").text
            Error = driver.find_element(by=By.ID, value="error").text

            if FinalText:
                driver.find_element(by=By.ID, value="end").click()

                return QueryModifier(FinalText)

            if Error:
                raise RuntimeError(f"Chrome speech recognition error: {Error}")

            if time() - started_at > timeout:
                raise TimeoutError(f"No speech was detected within {timeout:g} seconds.")
        except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
            _close_driver()
            sleep(0.5)
            driver = _start_browser_recognition()
            started_at = time()
        except TimeoutError:
            raise
        except RuntimeError:
            raise
        except Exception as e:
            print(f"Speech recognition polling error: {e}")
            sleep(0.1)

if __name__ == "__main__":
    while True:
        Text = SpeechRecognition()
        print(Text)
