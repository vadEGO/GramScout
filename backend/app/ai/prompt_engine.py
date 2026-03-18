import random
from typing import Optional
from app.ai.llm_client import openrouter


PERSONA_TYPES = {
    "skeptical": {"weight": 0.30, "temp_base": 0.7},
    "enthusiastic": {"weight": 0.25, "temp_base": 0.9},
    "sarcastic": {"weight": 0.15, "temp_base": 0.85},
    "helpful": {"weight": 0.10, "temp_base": 0.6},
    "curious": {"weight": 0.10, "temp_base": 0.75},
    "contrarian": {"weight": 0.10, "temp_base": 0.8},
}

TYPO_MAP = {
    "the": "teh",
    "because": "becuase",
    "something": "somethin",
    "probably": "probly",
    "definitely": "definately",
    "actually": "actualy",
}

ABBR_MAP = {
    "you": "u",
    "are": "r",
    "though": "tho",
    "probably": "prob",
    "literally": "lit",
    "seriously": "srsly",
    "right now": "rn",
    "by the way": "btw",
    "for real": "fr",
    "not gonna lie": "ngl",
    "to be honest": "tbh",
}


def generate_persona() -> dict:
    """Generate a random persona for an account."""
    personality = random.choices(
        list(PERSONA_TYPES.keys()),
        weights=[v["weight"] for v in PERSONA_TYPES.values()],
    )[0]

    age_ranges = ["18-24", "25-34", "35-44", "45+"]
    nationalities = [
        "american",
        "british",
        "canadian",
        "australian",
        "german",
        "french",
    ]
    vocab_levels = ["simple", "moderate", "advanced"]
    emoji_usage = ["never", "rare", "sometimes", "often"]

    return {
        "personality_type": personality,
        "age_range": random.choice(age_ranges),
        "nationality": random.choice(nationalities),
        "education_level": random.choice(["informal", "average", "educated"]),
        "vocabulary_level": random.choice(vocab_levels),
        "emoji_usage": random.choice(emoji_usage),
        "typo_rate": round(random.uniform(0.01, 0.08), 2),
        "abbreviation_tendency": round(random.uniform(0.3, 0.9), 2),
        "sentence_length_preference": random.choice(["short", "medium", "varied"]),
    }


def build_system_prompt(persona: dict) -> str:
    """Build system prompt from persona."""
    return f"""You are a real person commenting on Telegram. Write like you're texting a friend.

Your personality: {persona["personality_type"]}
Your age: {persona["age_range"]}
Your vocabulary: {persona["vocabulary_level"]}

RULES:
1. Write like a real human texting - lowercase, no perfect grammar
2. Embrace imperfection - typos are OK, run-on sentences are natural
3. Match the tone of the post - serious if serious, casual if casual
4. Have a clear opinion - agree or disagree, don't be neutral
5. Keep it short: 1-2 sentences (15-40 words) for most comments
6. Sometimes use: "idk", "tbh", "ngl", "lol", "bro", "bruh", "nah", "fr"
7. NEVER use: "I think that...", "Furthermore", "Additionally", "Great post!", hashtags
8. NEVER list points as "1. 2. 3."
9. React to the POST CONTENT specifically, not just its existence
10. Pick ONE specific point from the post to react to
"""


def apply_post_processing(text: str, persona: dict) -> str:
    """Apply persona-specific post-processing to generated text."""
    if random.random() > persona.get("typo_rate", 0.03):
        return text

    words = text.split()
    result = []
    for word in words:
        lower = word.lower()
        if lower in TYPO_MAP and random.random() < 0.3:
            result.append(TYPO_MAP[lower])
        elif persona.get("abbreviation_tendency", 0.5) > 0.6:
            if lower in ABBR_MAP and random.random() < 0.4:
                result.append(ABBR_MAP[lower])
            else:
                result.append(word)
        else:
            result.append(word)

    text = " ".join(result)

    if random.random() < 0.3 and persona.get("sentence_length_preference") != "short":
        text = text.rstrip(".")
    if random.random() < 0.15:
        text = text.replace("...", "..")
    if random.random() < 0.1:
        text = text.replace("no", random.choice(["noo", "nooo"]))
        text = text.replace("so", random.choice(["soo", "sooo"]))

    return text


async def generate_comment(
    post_text: str, persona: dict, channel_context: str = ""
) -> Optional[str]:
    """Generate a human-like comment for a post."""
    system_prompt = build_system_prompt(persona)
    user_prompt = f"""Post to comment on:
"{post_text}"

Channel: {channel_context}
Your personality: {persona["personality_type"]}
Write ONE comment as a real person would. Output ONLY the comment text."""

    temperature = PERSONA_TYPES.get(persona["personality_type"], {}).get(
        "temp_base", 0.7
    )
    temperature += random.uniform(-0.15, 0.15)
    temperature = max(0.5, min(1.2, temperature))

    max_tokens = random.randint(30, 80)

    result = await openrouter.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model="openai/gpt-4o-mini",
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if result:
        result = apply_post_processing(result.strip(), persona)

    return result
