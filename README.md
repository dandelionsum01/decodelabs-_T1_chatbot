<p align="center">
  <video src="https://github.com/user-attachments/assets/9757e30f-b7bc-4ddd-8243-4cd4a7d647a5" width="100%" autoplay muted loop playsinline></video>
</p>


# DecodeBot — Hybrid Rule-Based + Gemini Chatbot

Extended version of Decode Labs Project 1. Keeps the required rule-based
skeleton (dictionary lookup, sanitization, loop, fallback, exit) and adds a
Gemini API fallback for anything the rules don't cover — the same "rule
match? → instant response : no → pass to LLM" pattern shown in the training
deck's "Hybrid Architecture" slide.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a free Gemini API key: https://aistudio.google.com/app/apikey

3. Copy `.env.example` to `.env` and paste your key in:
   ```
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   GEMINI_API_KEY=your_actual_key
   ```

4. Run it:
   ```
   python gemini_chatbot.py
   ```

If you skip step 2/3, the bot still runs — it just falls back to
"I do not understand" for anything outside the rule dictionary, instead of
calling Gemini. Nothing crashes without a key.

## How it works

1. **Sanitize** — input is lowercased and stripped.
2. **Rule check** — exact match against a dictionary of 5+ intents
   (`hello`, `hi`, `help`, `who are you`, `thanks`, etc.) via `.get()`,
   not an if-elif ladder.
3. **Gemini fallback** — if nothing matches, the raw message is sent to
   Gemini through a persistent chat session, so it remembers earlier turns
   in the conversation.
4. **Logging** — every turn (both sides) is appended to `chat_log.txt` with
   a timestamp.
5. **Exit** — typing `bye`, `exit`, `goodbye`, or `quit` breaks the loop
   cleanly.

## Extend it

- Add more entries to the `RULES` dict.
- Change `GEMINI_MODEL` in `.env` (e.g. to a different Gemini model) if you
  have access to one.
- Swap the `SYSTEM_INSTRUCTION` string to give the bot a different
  personality.
