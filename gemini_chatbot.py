    """
    chatbot.py — Hybrid rule-based + Gemini chatbot with enforced brief replies.

    Setup:
        pip install google-genai python-dotenv
        Create .env with: GEMINI_API_KEY=your_key_here

    Run:
        python chatbot.py
    """

    import os
    import time
    from datetime import datetime
    from dotenv import load_dotenv
    from google import genai
    from google.genai import types

    load_dotenv()

    # ── Config ──────────────────────────────────────────────────────────────────
    MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    BOT_NAME   = "Bot"
    LOG_FILE   = "chat_log.txt"
    EXIT_WORDS = {"exit", "quit", "bye", "q"}

    SYSTEM_PROMPT = (
        "You are a concise terminal chatbot. STRICT RULES:\n"
        "- Answer in 1-3 plain sentences. Absolute maximum. No exceptions.\n"
        "- Zero markdown: no **, no #, no bullet points, no numbered lists.\n"
        "- One sentence of context after the direct answer, then stop.\n"
        "- Only elaborate if the user explicitly asks for more detail.\n"
    )

    RULES = {
        "hi":           "Hey! What do you want to know?",
        "hello":        "Hello! Ask me anything.",
        "help":         "Just type any question. Say 'bye' to exit.",
        "who are you":  f"I'm {BOT_NAME}, a simple chatbot backed by Gemini.",
        "thanks":       "No problem.",
        "thank you":    "You're welcome.",
    }

    # ── Colors ───────────────────────────────────────────────────────────────────
    R = "\033[0m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"

    # ── Helpers ───────────────────────────────────────────────────────────────────
    def sanitize(text: str) -> str:
        return text.lower().strip()

    def log(role: str, text: str) -> None:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {role}: {text}\n")

    def bot_print(msg: str, tag: str = "") -> None:
        suffix = f" {YELLOW}[{tag}]{R}" if tag else ""
        print(f"{GREEN}{BOT_NAME}: {msg}{R}{suffix}")

    # ── Gemini setup ──────────────────────────────────────────────────────────────
    def init_gemini():
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            print(f"{YELLOW}No GEMINI_API_KEY — running rule-only mode.{R}\n")
            return None, None
        try:
            client = genai.Client(api_key=key)
            chat = client.chats.create(
                model=MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=512,
                ),
            )
            return client, chat
        except Exception as e:
            print(f"{RED}Gemini init failed: {e}{R}\n")
            return None, None

    def ask_gemini(chat, user_input: str) -> tuple[str, str]:
        """Returns (reply_text, tag_string)."""
        # Prepend a brevity reminder — last thing the model sees before generating
        prompt = f"[Reply in max 2 plain sentences, no markdown] {user_input}"
        t0 = time.perf_counter()
        try:
            resp = chat.send_message(
                prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=512,
                ),
            )
            elapsed = time.perf_counter() - t0
            usage = getattr(resp, "usage_metadata", None)
            tok = getattr(usage, "total_token_count", "?") if usage else "?"
            return resp.text.strip(), f"{elapsed:.1f}s · {tok} tok"
        except Exception as e:
            return f"Gemini error: {e}", "error"

    # ── Main loop ─────────────────────────────────────────────────────────────────
    def main():
        print(f"{YELLOW}=== {BOT_NAME} | type 'bye' to exit ==={R}\n")
        _, chat = init_gemini()

        while True:
            try:
                raw = input(f"{CYAN}You: {R}").strip()
            except (EOFError, KeyboardInterrupt):
                bot_print("Bye!")
                break

            if not raw:
                continue

            clean = sanitize(raw)
            log("You", raw)

            if clean in EXIT_WORDS:
                bot_print("Bye!")
                log(BOT_NAME, "Bye!")
                break

            # Rule layer first
            if clean in RULES:
                reply, tag = RULES[clean], "rule"
            elif chat is None:
                reply = "I don't have an answer for that. Add a GEMINI_API_KEY to unlock full responses."
                tag = "fallback"
            else:
                reply, tag = ask_gemini(chat, raw)

            bot_print(reply, tag)
            log(BOT_NAME, reply)

    if __name__ == "__main__":
        main()
