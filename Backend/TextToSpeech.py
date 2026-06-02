import pygame
import asyncio
import edge_tts
import os
import threading
import uuid
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice") #or "en-US-AriaNeural"
_stop_event = threading.Event()


def StopTextToSpeech():
    _stop_event.set()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass


def ResetTextToSpeechStop():
    _stop_event.clear()


def IsTextToSpeechStopped():
    return _stop_event.is_set()


async def TextToAudioFile(text) -> str:
    os.makedirs("Data", exist_ok=True)
    file_path = os.path.join("Data", f"speech-{uuid.uuid4().hex}.mp3")

    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(file_path)
    return file_path

def TTS(Text, func=lambda r=None: True):
    ResetTextToSpeechStop()
    
    # Split text into sentences using regex (split on terminal punctuation followed by space)
    import re
    sentences = re.split(r'(?<=[.!?])\s+', Text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return True

    next_download_thread = None
    
    def download_sentence_sync(sentence):
        try:
            return asyncio.run(TextToAudioFile(sentence))
        except Exception as e:
            print(f"Error downloading TTS sentence: {e}")
            return None

    # Start by downloading the first sentence immediately (very fast because it's short)
    current_file_path = download_sentence_sync(sentences[0])
    if not current_file_path:
        return False

    for idx, current_sentence in enumerate(sentences):
        if IsTextToSpeechStopped() or func() == False:
            break

        # Start pre-downloading the NEXT sentence asynchronously in the background
        class DownloadResult:
            path = None
        res = DownloadResult()
        
        if idx + 1 < len(sentences):
            next_sentence = sentences[idx + 1]
            def pre_fetch_target():
                res.path = download_sentence_sync(next_sentence)
            next_download_thread = threading.Thread(target=pre_fetch_target, daemon=True)
            next_download_thread.start()
        else:
            next_download_thread = None

        # Play the CURRENT sentence
        mixer_started = False
        try:
            pygame.mixer.init()
            mixer_started = True

            try:
                pygame.mixer.music.load(current_file_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    if IsTextToSpeechStopped() or func() == False:
                        break
                    pygame.time.Clock().tick(10)
            except Exception as music_err:
                print(f"Pygame music load failed, trying Sound fallback: {music_err}")
                sound = pygame.mixer.Sound(current_file_path)
                channel = sound.play()
                while channel.get_busy():
                    if IsTextToSpeechStopped() or func() == False:
                        sound.stop()
                        break
                    pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Error playing TTS sentence: {e}")
        finally:
            if mixer_started:
                try:
                    pygame.mixer.music.stop()
                    try:
                        pygame.mixer.music.unload()
                    except Exception:
                        pass
                    pygame.mixer.quit()
                except Exception as e:
                    print(f"Error releasing TTS mixer: {e}")
            
            # Clean up the played sentence file
            if current_file_path:
                try:
                    os.remove(current_file_path)
                except OSError:
                    pass

        # Wait for the next sentence download to finish, then set it as current
        if next_download_thread:
            next_download_thread.join()
            current_file_path = res.path
            if not current_file_path:
                break

    try:
        func(False)
    except Exception:
        pass

    return True


def TextToSpeech(Text, func=lambda r=None: True):
    TTS(Text, func)

if __name__ == "__main__":
    while True:
        
        TextToSpeech(input("Enter the text: "))
