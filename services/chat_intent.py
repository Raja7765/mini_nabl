# ==========================================
# GREETING / SMALL CHAT DETECTOR
# ==========================================

GREETINGS = {
    "hi",
    "hello",
    "hey",
    "hai",
    "hlo",
    "good morning",
    "good afternoon",
    "good evening",
    "good night",
}

SMALL_TALK = {
    "how are you",
    "how are you doing",
    "what's up",
    "whats up",
}

THANKS = {
    "thanks",
    "thank you",
    "thankyou",
    "thx",
}

GOODBYES = {
    "bye",
    "goodbye",
    "see you",
}
ABOUT = {
    "who is your creater",
}


def detect_chat_intent(message: str):
    """
    Detect simple greetings and small-talk messages.

    Returns:
        greeting
        small_talk
        thanks
        goodbye
        None
    """

    text = message.strip().lower()

    # Exact matching only for now.
    # This prevents normal NABL questions
    # from being incorrectly classified.

    if text in GREETINGS:
        return "greeting"

    if text in SMALL_TALK:
        return "small_talk"

    if text in THANKS:
        return "thanks"

    if text in GOODBYES:
        return "goodbye"
    if text in ABOUT:
        return "about"

    return None


def get_chat_response(intent: str):
    """
    Return a predefined response without using LLM.
    """

    responses = {
        "greeting":
            "Hello! How can I help you with NABL documents?",

        "small_talk":
            "I'm doing well! How can I help you with NABL documents?",

        "thanks":
            "You're welcome! Feel free to ask me anything about NABL documents.",

        "goodbye":
            "Goodbye! Have a great day.",
        "about":
            "I'm a NABL AI Assistant created by Rajalingam he is a backend developer he is working in Corover."
    }

    return responses.get(intent)