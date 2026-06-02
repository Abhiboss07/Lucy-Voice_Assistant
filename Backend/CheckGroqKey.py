from dotenv import dotenv_values
from groq import Groq


env_vars = dotenv_values(".env")
api_key = env_vars.get("GroqAPIKey")
model = env_vars.get("GroqModel") or "llama-3.3-70b-versatile"

if not api_key:
    print("GroqAPIKey is missing from .env")
    raise SystemExit(1)

print(f"Loaded GroqAPIKey: {api_key[:7]}...{api_key[-4:]}")
print(f"Loaded GroqModel: {model}")

try:
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with only: OK"}],
        max_tokens=8,
    )
    print("Groq auth: OK")
    print(completion.choices[0].message.content)
except Exception as e:
    print("Groq auth/test failed:")
    print(e)
    raise SystemExit(1)
