"""
DecodeBot - Hybrid Rule-Based + Gemini AI Chatbot
===================================================
Decode Labs Internship - Project 1 (extended)

Satisfies the original Project 1 spec:
  - Continuous input loop
  - Input sanitization (case/whitespace)
  - Dictionary-based knowledge base with 5+ intents
  - Fallback for unrecognized input
  - Clean exit command

...then goes further with the "hybrid architecture" pattern shown in the
training deck: if no rule matches, the message is passed to the Gemini API
for a real generative response, with conversation memory, logging, and
graceful error handling.

Setup:
    pip install google-genai python-dotenv
    Copy .env.example to .env and add your Gemini API key
    (free key: https://aistudio.google.com/app/apikey)

Run:
    python gemini_chatbot.py
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LOG_FILE = "chat_log.txt"
BOT_NAME = "DecodeBot"

SYSTEM_INSTRUCTION = (
    f"You are {BOT_NAME}, a friendly and concise AI assistant built for a "
    "Decode Labs internship demo. Keep answers short (2-4 sentences) unless "
    "the user explicitly asks for more detail."
)

EXIT_COMMANDS = {"exit", "quit", "bye", "goodbye"}

# ---------------------------------------------------------------------------
# RULE-BASED KNOWLEDGE BASE  (Project 1 requirement: dict, not if-elif, 5+ intents)
# ---------------------------------------------------------------------------
RULES = {
    "hello": f"Hi there! I'm {BOT_NAME}. Ask me anything.",
    "hi": "Hey! How can I help you today?",
    "help": "Just chat normally - I'll answer using Gemini for anything I don't "
            "already have a canned reply for. Type 'bye' to exit.",
    "who are you": f"I'm {BOT_NAME}: a hybrid chatbot. Simple stuff gets an instant "
                    "rule-based reply, everything else goes to Gemini.",
    "what can you do": "I can handle quick commands instantly, and answer open-ended "
                        "questions using Google's Gemini model.",
    "thanks": "You're welcome!",
    "thank you": "Anytime!",
}


# ---------------------------------------------------------------------------
# TERMINAL COLORS (small UX touch, purely cosmetic)
# ---------------------------------------------------------------------------
class Color:
    USER = "\033[96m"
    BOT = "\033[92m"
    SYS = "\033[93m"
    ERR = "\033[91m"
    RESET = "\033[0m"


# ---------------------------------------------------------------------------
# CORE HELPERS
# ---------------------------------------------------------------------------
def sanitize(text: str) -> str:
    """Normalize input the way Phase 1 of the spec requires."""
    return text.lower().strip()


def log_line(role: str, text: str) -> None:
    """Append every turn to a log file with a timestamp."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {role}: {text}\n")


def rule_based_reply(clean_input: str):
    """Exact-match dictionary lookup. Returns None if nothing matches."""
    return RULES.get(clean_input)


def build_client():
    """Create a Gemini client if an API key is available; otherwise degrade gracefully."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(
            f"{Color.SYS}No GEMINI_API_KEY found. Add one to a .env file to enable "
            f"Gemini responses. Running in rule-based-only mode for now.{Color.RESET}\n"
        )
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"{Color.ERR}Could not initialize Gemini client: {e}{Color.RESET}")
        return None


def build_chat(client):
    """Start a chat session so Gemini has conversation memory across turns."""
    if client is None:
        return None
    try:
        return client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
        )
    except TypeError:
        # Fallback in case the installed SDK version doesn't accept `config` here
        return client.chats.create(model=MODEL_NAME)


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------
def main():
    print(f"{Color.SYS}=== {BOT_NAME}: Hybrid Rule-Based + Gemini Chatbot ==={Color.RESET}")
    print(f"{Color.SYS}Type 'bye', 'exit', or 'quit' to leave.{Color.RESET}\n")

    client = build_client()
    chat = build_chat(client)

    while True:
        try:
            raw = input(f"{Color.USER}You: {Color.RESET}")
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Color.BOT}{BOT_NAME}: Goodbye!{Color.RESET}")
            break

        clean = sanitize(raw)
        if not clean:
            continue

        log_line("You", raw)

        if clean in EXIT_COMMANDS:
            print(f"{Color.BOT}{BOT_NAME}: Goodbye! \U0001F44B{Color.RESET}")
            log_line(BOT_NAME, "Goodbye!")
            break

        # 1. Rule-based layer first: instant, free, zero hallucination risk
        reply = rule_based_reply(clean)
        tag = "rule"

        # 2. No rule matched -> pass to Gemini for a real generative answer
        if reply is None:
            if chat is None:
                reply = "I do not understand. (Add a GEMINI_API_KEY to unlock full answers.)"
                tag = "fallback"
            else:
                try:
                    response = chat.send_message(raw)
                    reply = response.text
                    tag = "gemini"
                except Exception as e:
                    reply = f"Gemini request failed: {e}"
                    tag = "error"

        label = f" {Color.SYS}[{tag}]{Color.RESET}" if tag != "gemini" else ""
        print(f"{Color.BOT}{BOT_NAME}: {reply}{Color.RESET}{label}")
        log_line(BOT_NAME, reply)


if __name__ == "__main__":
    main()
