import base64
import json
import mimetypes
import os
import shutil
import time
from dotenv import dotenv_values


UPLOAD_DIR = os.path.join("Data", "Uploads")
MANIFEST_PATH = os.path.join("Data", "UploadedFiles.json")
TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".csv", ".tsv",
    ".log", ".xml", ".yaml", ".yml", ".ini", ".env"
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_CONTEXT_FILES = 6
MAX_IMAGE_FILES = 3

env_vars = dotenv_values(".env")
MAX_TEXT_CHARS_PER_FILE = int(env_vars.get("FileContextMaxChars") or 6000)


def _safe_filename(path):
    name = os.path.basename(path)
    keep = []
    for char in name:
        keep.append(char if char.isalnum() or char in " ._-" else "_")
    cleaned = "".join(keep).strip(" .")
    return cleaned or f"upload_{int(time.time())}"


def _load_manifest():
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _save_manifest(items):
    os.makedirs("Data", exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as file:
        json.dump(items[-40:], file, indent=2)


def register_uploads(paths):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    manifest = _load_manifest()
    added = []

    for source in paths:
        if not source or not os.path.isfile(source):
            continue

        filename = _safe_filename(source)
        stem, ext = os.path.splitext(filename)
        destination = os.path.join(UPLOAD_DIR, filename)
        counter = 1

        while os.path.exists(destination):
            filename = f"{stem}_{counter}{ext}"
            destination = os.path.join(UPLOAD_DIR, filename)
            counter += 1

        shutil.copy2(source, destination)
        item = {
            "name": filename,
            "path": os.path.abspath(destination),
            "ext": ext.lower(),
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        manifest.append(item)
        added.append(item)

    _save_manifest(manifest)
    return added


def remove_upload(path):
    target = os.path.abspath(path)
    manifest = _load_manifest()
    kept = []
    removed = False

    for item in manifest:
        item_path = os.path.abspath(item.get("path", ""))
        if item_path == target:
            removed = True
            continue
        kept.append(item)

    if removed:
        _save_manifest(kept)
        try:
            uploads_root = os.path.abspath(UPLOAD_DIR)
            if os.path.isfile(target) and target.startswith(uploads_root):
                os.remove(target)
        except OSError:
            pass

    return removed


def _read_text(path):
    for encoding in ["utf-8", "utf-8-sig", "cp1252"]:
        try:
            with open(path, "r", encoding=encoding) as file:
                return file.read(MAX_TEXT_CHARS_PER_FILE)
        except UnicodeDecodeError:
            continue
        except OSError:
            return ""
    return ""


def get_file_context():
    manifest = [item for item in _load_manifest() if os.path.isfile(item.get("path", ""))]
    recent = manifest[-MAX_CONTEXT_FILES:]
    text_sections = []
    image_parts = []
    file_names = []

    for item in recent:
        path = item.get("path", "")
        name = item.get("name") or os.path.basename(path)
        ext = (item.get("ext") or os.path.splitext(path)[1]).lower()
        file_names.append(name)

        if ext in TEXT_EXTENSIONS:
            content = _read_text(path).strip()
            if content:
                text_sections.append(f"File: {name}\n{content}")

        elif ext in IMAGE_EXTENSIONS and len(image_parts) < MAX_IMAGE_FILES:
            mime_type = mimetypes.guess_type(path)[0] or "image/jpeg"
            try:
                with open(path, "rb") as image_file:
                    image_parts.append({
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64.b64encode(image_file.read()).decode("ascii"),
                        }
                    })
            except OSError:
                continue

    summary = ""
    if file_names:
        summary = "Uploaded files available for context: " + ", ".join(file_names) + "."
    if text_sections:
        summary += "\n\nUse this uploaded file context when relevant:\n\n" + "\n\n---\n\n".join(text_sections)

    return {
        "summary": summary.strip(),
        "image_parts": image_parts,
        "file_names": file_names,
    }


def get_latest_uploaded_image():
    manifest = [item for item in _load_manifest() if os.path.isfile(item.get("path", ""))]
    for item in reversed(manifest):
        ext = (item.get("ext") or os.path.splitext(item.get("path", ""))[1]).lower()
        if ext in IMAGE_EXTENSIONS:
            return item
    return None

def clear_all_uploads():
    try:
        manifest_path = MANIFEST_PATH
        if os.path.exists(manifest_path):
            with open(manifest_path, "w", encoding="utf-8") as file:
                json.dump([], file)
                
        upload_dir = UPLOAD_DIR
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                filepath = os.path.join(upload_dir, filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except OSError:
                    pass
    except Exception as e:
        print(f"Error clearing uploads: {e}")
