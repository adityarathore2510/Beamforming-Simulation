"""
Claude API Quickstart
---------------------
A minimal example to verify your Anthropic SDK setup is working.
Run: python claude_quickstart.py
"""

import os
from pathlib import Path
from anthropic import Anthropic

# Load API key from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"📂 Loading .env from: {env_path}")
except ImportError:
    print("⚠️  python-dotenv not found, reading env vars directly")

api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

# Debug: show what was loaded (masked)
if api_key:
    masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"🔑 Key loaded: {masked} (length: {len(api_key)})")
else:
    print("❌ ANTHROPIC_API_KEY is empty or not set!")
    print()
    print("   Fix: Open .env and make sure it looks EXACTLY like this:")
    print("   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx")
    print()
    print("   (No spaces, no quotes, key immediately after the = sign)")
    exit(1)

if api_key in ("your_api_key_here", ""):
    print("❌ Placeholder key detected — paste your real key in .env")
    exit(1)

client = Anthropic(api_key=api_key)

print("🚀 Sending test message to Claude...")

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hello Claude! I just set up the Anthropic SDK. Reply with a short greeting."
        }
    ]
)

print("\n✅ Claude responded:")
print("-" * 40)
print(message.content[0].text)
print("-" * 40)
print(f"\n📊 Usage: {message.usage.input_tokens} input tokens | {message.usage.output_tokens} output tokens")
