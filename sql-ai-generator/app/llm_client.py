import json
import urllib.request
import urllib.error

from app.config import LLM_PROVIDER, ANTHROPIC_API_KEY, CLAUDE_MODEL, OLLAMA_MODEL, OLLAMA_HOST
from app.prompt_builder import build_system_prompt, build_nosql_prompt


def generate_sql(question: str) -> str:
    """Generates the real, executable SQLite SQL for this question."""
    return _clean_sql(_generate(question, build_system_prompt()))


def generate_nosql_reference(question: str, target: str) -> str:
    """Generates a non-executable reference query/explanation for a
    non-relational target (mongodb, redis), for display purposes only."""
    return _clean_sql(_generate(question, build_nosql_prompt(target)))


def _generate(question: str, system_prompt: str) -> str:
    if LLM_PROVIDER == "ollama":
        return _generate_with_ollama(question, system_prompt)
    elif LLM_PROVIDER == "anthropic":
        return _generate_with_anthropic(question, system_prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER!r} (use 'ollama' or 'anthropic')")


def _generate_with_anthropic(question: str, system_prompt: str) -> str:
    from anthropic import Anthropic  # imported lazily so Ollama-only setups don't need this configured

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _generate_with_ollama(question: str, system_prompt: str) -> str:
    """Calls a local Ollama server -- free, runs entirely on your machine.
    Requires Ollama installed and running (https://ollama.com) with a model
    pulled, e.g.: `ollama pull qwen2.5-coder`."""
    payload = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": question,
        "stream": False,
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_HOST}. Is it running? "
            f"Install from https://ollama.com, then run `ollama pull {OLLAMA_MODEL}` "
            f"and `ollama serve`. Original error: {e}"
        )
    return data.get("response", "")


def _clean_sql(text: str) -> str:
    """Strips markdown fences in case the model adds them despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text
