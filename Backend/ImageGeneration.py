import asyncio
from random import randint
from PIL import Image
from dotenv import dotenv_values
from huggingface_hub import InferenceClient
import os
import requests
# from time import sleep
from urllib.parse import quote
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Backend.FileContext import get_latest_uploaded_image


# def open_image(prompt):
#     folder_path = r"Data"
#     prompt = safe_image_name(prompt)
# 
#     Files = [f"{prompt}{i}.jpg" for i in range(1, IMAGE_COUNT + 1)]
# 
#     for jpg_file in Files:
#         image_path = os.path.join(folder_path, jpg_file)
# 
#         try:
# 
#             img = Image.open(image_path)
#             print(f"Opening image: {image_path}")
#             img.show()
#             sleep(1)
# 
#         except IOError:
#             print(f"Unable to open image: {image_path}")


env_vars = dotenv_values(".env")
HUGGINGFACE_API_KEY = env_vars.get("HuggingFaceAPIKey")
IMAGE_MODEL = env_vars.get("HuggingFaceImageModel") or "black-forest-labs/FLUX.1-schnell"
IMAGE_PROVIDER = (env_vars.get("ImageProvider") or "auto").lower()
IMAGE_COUNT = max(1, min(int(env_vars.get("ImageCount") or 1), 4))
IMAGE_WIDTH = max(256, min(int(env_vars.get("ImageWidth") or 512), 1024))
IMAGE_HEIGHT = max(256, min(int(env_vars.get("ImageHeight") or 512), 1024))
IMAGE_TIMEOUT = max(10, int(env_vars.get("ImageTimeout") or 35))
IMAGE_FAST_MODE = (env_vars.get("ImageFastMode") or "True").lower() == "true"
client = InferenceClient(provider="hf-inference", api_key=HUGGINGFACE_API_KEY) if HUGGINGFACE_API_KEY else None


async def query_huggingface(payload):
    if client is None:
        raise RuntimeError("HuggingFaceAPIKey is missing from .env")

    prompt = payload["inputs"]
    image = await asyncio.to_thread(
        client.text_to_image,
        prompt,
        model=IMAGE_MODEL,
    )
    return image


async def query_pollinations(prompt, seed):
    url = (
        "https://image.pollinations.ai/prompt/"
        f"{quote(prompt)}?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}&seed={seed}&nologo=true&model=flux"
    )
    response = await asyncio.to_thread(requests.get, url, timeout=IMAGE_TIMEOUT)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "image" not in content_type:
        raise RuntimeError(f"Pollinations returned {content_type or 'non-image response'}")

    from io import BytesIO
    return Image.open(BytesIO(response.content)).convert("RGB")





STYLE_KEYWORDS = [
    "anime", "cartoon", "illustration", "painting", "sketch", "drawing",
    "watercolor", "oil painting", "digital art", "3d", "render", "cinematic",
    "cyberpunk", "fantasy", "pixel art", "logo", "icon", "poster", "style"
]


def safe_image_name(prompt):
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in prompt.lower())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return (cleaned[:80] or "generated_image")


def build_image_prompt(prompt: str, seed: int) -> str:
    base_prompt = prompt.strip()
    lower_prompt = base_prompt.lower()

    if any(keyword in lower_prompt for keyword in STYLE_KEYWORDS):
        return f"{base_prompt}, seed {seed}"

    if IMAGE_FAST_MODE:
        return f"{base_prompt}, realistic, clear subject, seed {seed}"

    return (
        f"{base_prompt}, natural realistic photo, true-to-life colors, realistic lighting, "
        f"normal camera perspective, subtle details, not overprocessed, no heavy filters, seed {seed}"
    )


def analyze_image_with_gemini(image_path: str) -> str:
    gemini_key = env_vars.get("GeminiAPIKey")
    if not gemini_key:
        print("GeminiAPIKey not found in .env, skipping image analysis.")
        return ""
        
    try:
        import base64
        import requests
        import mimetypes
        
        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        with open(image_path, "rb") as image_file:
            img_data = base64.b64encode(image_file.read()).decode("ascii")
            
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        
        prompt = (
            "You are a master portrait artist. Analyze the person in this photo in extreme detail. "
            "Write a highly specific visual description of their unique facial contours and proportions, "
            "including their exact face shape, jawline structure, eyebrow thickness and shape, eye shape (e.g. almond, deep-set) and color, "
            "nose shape, lip fullness, exact hair texture/cut/style/color, unique facial markings, beard/mustache specifics, "
            "skin tone, and distinguishing accessories (like the exact frames of their glasses). "
            "Focus heavily on the details that make their face unique and recognizable, so a text-to-image generator "
            "can recreate an identical recognizable version. Do not use generic terms. Keep it under 65 words."
        )
        
        response = requests.post(
            url,
            params={"key": gemini_key},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": img_data
                                }
                            }
                        ]
                    }
                ]
            },
            timeout=25
        )
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates") or []
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        desc = "".join(part.get("text", "") for part in parts).strip()
        print(f"Gemini Image Analysis: {desc}")
        return desc
    except Exception as e:
        print(f"Failed to analyze image with Gemini: {e}")
        return ""


def build_reference_edit_prompt(prompt: str) -> str:
    latest_image = get_latest_uploaded_image()
    if not latest_image:
        return prompt

    image_path = latest_image.get("path")
    if not image_path or not os.path.exists(image_path):
        return prompt

    print(f"Analyzing uploaded image context: {os.path.basename(image_path)}")
    desc = analyze_image_with_gemini(image_path)
    
    if not desc:
        return prompt

    # Clean description and format it nicely for integration
    desc_clean = desc.strip().rstrip(".")
    if desc_clean.lower().startswith("male "):
        desc_clean = "a male " + desc_clean[5:]
    elif desc_clean.lower().startswith("female "):
        desc_clean = "a female " + desc_clean[7:]
    elif desc_clean.lower().startswith("person "):
        desc_clean = "a person " + desc_clean[7:]

    lower_prompt = prompt.lower()
    
    if ("enhance" in lower_prompt or "enchance" in lower_prompt or "4k" in lower_prompt or "upscale" in lower_prompt or "hd" in lower_prompt) and ("remove" in lower_prompt or "background" in lower_prompt or "bg" in lower_prompt):
        final_prompt = (
            f"A gorgeous, extremely high-quality 4K resolution studio portrait of {desc_clean}, "
            "isolated on a clean, solid, pure black background. Superb photorealistic details, professional studio lighting, sharp focus, masterwork photography."
        )
    elif "remove" in lower_prompt or "background" in lower_prompt or "bg" in lower_prompt or "cutout" in lower_prompt:
        final_prompt = (
            f"A professional high-quality studio portrait of {desc_clean}, "
            "isolated on a clean, solid, pure black background. Cinematic studio lighting, sharp focus, masterwork photography."
        )
    elif "enhance" in lower_prompt or "enchance" in lower_prompt or "4k" in lower_prompt or "upscale" in lower_prompt or "hd" in lower_prompt:
        final_prompt = (
            f"A gorgeous, extremely high-quality 4K resolution studio-shot portrait of {desc_clean}. "
            "Superb photorealistic details, professional close-up camera shot, stunning natural lighting, sharp focus, masterwork photography."
        )
    elif "anime" in lower_prompt:
        final_prompt = (
            f"A clean high-quality anime-style portrait of {desc_clean}. "
            "High-quality anime aesthetic, vibrant colors, sharp detailed outlines, Studio Ghibli or Makoto Shinkai style, masterwork illustration."
        )
    elif "cartoon" in lower_prompt:
        final_prompt = (
            f"A beautiful cartoon-style portrait of {desc_clean}. "
            "Polished modern cartoon illustration, expressive eyes, colorful vector-art, clean background."
        )
    elif "sketch" in lower_prompt or "drawing" in lower_prompt:
        final_prompt = (
            f"A detailed pencil sketch drawing of {desc_clean}. "
            "Hand-drawn fine art, clean detailed line-work, realistic shading, solid white background."
        )
    elif "painting" in lower_prompt or "watercolor" in lower_prompt:
        final_prompt = (
            f"A gorgeous watercolor painting of {desc_clean}. "
            "Soft canvas textures, beautiful paint blending, colorful artistic splatters, masterwork painting."
        )
    else:
        final_prompt = (
            f"A high-quality, beautiful stylized digital art portrait of {desc_clean}. "
            f"Artistic representation, vibrant colors, detailed features, gorgeous aesthetic."
        )

    print(f"Constructed optimized style prompt: {final_prompt}")
    return final_prompt


async def generate_image(prompt: str):
    os.makedirs("Data", exist_ok=True)
    saved = 0
    use_huggingface = IMAGE_PROVIDER in ["auto", "huggingface"]

    for i in range(IMAGE_COUNT):
        seed = randint(0, 100000)
        final_prompt = build_image_prompt(prompt, seed)

        try:
            if use_huggingface:
                image = await query_huggingface({"inputs": final_prompt})
            else:
                image = await query_pollinations(final_prompt, seed)
        except Exception as e:
            print(f"Image {i + 1} primary provider failed: {e}")
            if IMAGE_PROVIDER == "huggingface":
                continue

            use_huggingface = False
            try:
                image = await query_pollinations(final_prompt, seed)
            except Exception as fallback_error:
                print(f"Image {i + 1} fallback provider failed: {fallback_error}")
                continue

        image.save(os.path.join("Data", f"{safe_image_name(prompt)}{i + 1}.jpg"))
        saved += 1

    if saved == 0:
        print("No images were generated. Check provider credits or network access.")
        return False

    return True

            

def GenerateImages(prompt: str):
    prompt_clean = prompt.replace("generate image", "", 1).strip() or prompt
    if prompt_clean.lower().startswith("of "):
        prompt_clean = prompt_clean[3:].strip()
    
    prompt_full = build_reference_edit_prompt(prompt_clean)
    
    result_path = os.path.join("Frontend", "Files", "ImageResult.data")
    
    if asyncio.run(generate_image(prompt_full)):
        image_paths = []
        for i in range(IMAGE_COUNT):
            path = os.path.abspath(os.path.join("Data", f"{safe_image_name(prompt_full)}{i + 1}.jpg"))
            if os.path.exists(path):
                image_paths.append(path)
                
        payload = ";".join(image_paths)
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(f"done|{prompt_clean}|{payload}")
    else:
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(f"error|{prompt_clean}|")

def main(wait_for_request=False):
    data_path = os.path.join(os.getcwd(), 'Frontend', 'Files', 'ImageGeneration.data')

    while True:

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                Data: str = f.read()

            parts = Data.rsplit(",", 1)
            Prompt = parts[0].strip()
            Status = parts[1].strip() if len(parts) > 1 else "False"

            if Status == "True" and Prompt:
                print("Generating Image...")
                GenerateImages(prompt=Prompt)

                with open(data_path, "w", encoding="utf-8") as f:
                    f.write("False,False")
                break

            else:
                if not wait_for_request:
                    print("No pending image request. Use the main app or set ImageGeneration.data to '<prompt>,True'.")
                    break
                sleep(1)
        except Exception as e:
            print(f"Image generation loop error: {e}")
            if not wait_for_request:
                break
            sleep(1)

if __name__ == "__main__":
    main()
