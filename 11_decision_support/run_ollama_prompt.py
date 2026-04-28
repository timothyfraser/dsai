#!/usr/bin/env python3
from pathlib import Path
import argparse
from datetime import datetime
import requests

DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_PROMPT_FILE = "11_decision_support/venue_prompt.md"
DEFAULT_HOST = "http://localhost:11434"
DEFAULT_TIMEOUT = 180
OLD_PRIORITIES = [
    "Budget: under $8,000 for venue rental",
    "Guest count: ~120 people",
    "Vibe: romantic, not too corporate",
    "Must have outdoor ceremony option",
    "Catering must be in-house or on an approved vendor list",
]
NEW_PRIORITIES = [
    "Budget: flexible, up to $15,000",
    "Guest count: ~200 people",
    "Vibe: elegant, grand",
    "Outdoor is a nice-to-have but not required",
    "No catering constraint",
]
def list_installed_models(host: str, timeout: int) -> list[str]:
    url = f"{host.rstrip('/')}/api/tags"
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]


def choose_model(requested_model: str, installed_models: list[str]) -> tuple[str, str | None]:
    if not installed_models:
        raise RuntimeError("No local Ollama models are installed. Run `ollama pull <model>` once.")

    if requested_model in installed_models:
        return requested_model, None

    # Prefer a llama model if available; otherwise use the first installed model.
    preferred = next((m for m in installed_models if m.startswith("llama")), installed_models[0])
    return preferred, requested_model


def build_prompt_with_priorities(base_prompt: str, priorities: list[str]) -> str:
    start_marker = "Here are the couple's priorities:"
    end_marker = "Here are descriptions of 16 venues. Please analyze and recommend."
    if start_marker not in base_prompt or end_marker not in base_prompt:
        raise ValueError("Prompt template is missing expected priorities markers.")

    before, rest = base_prompt.split(start_marker, 1)
    _, after = rest.split(end_marker, 1)
    priority_lines = "\n".join(f"- {item}" for item in priorities)
    return (
        f"{before}{start_marker}\n"
        f"{priority_lines}\n\n"
        f"{end_marker}{after}"
    )


def create_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(f"11_decision_support/venue_shortlist_{timestamp}.md")


def generate_change_summary(
    host: str,
    model: str,
    old_content: str,
    new_content: str,
    timeout: int,
) -> tuple[str, str]:
    comparison_prompt = (
        "You are comparing two ranked venue shortlists created from the same 16 venues.\n\n"
        "SHORTLIST A (old priorities):\n"
        f"{old_content}\n\n"
        "SHORTLIST B (new priorities):\n"
        f"{new_content}\n\n"
        "Write exactly 5-6 sentences. Compare what changed between the shortlists and explain why.\n"
        "Explicitly mention which venues moved up or down in ranking and tie each shift to priorities "
        "(budget, guest count, vibe, outdoor requirement, and catering constraint)."
    )
    return call_model(host=host, model=model, prompt_text=comparison_prompt, timeout=timeout)


def build_combined_output(
    old_priorities: list[str],
    new_priorities: list[str],
    old_content: str,
    new_content: str,
    change_summary: str,
) -> str:
    old_priority_block = "\n".join(f"- {item}" for item in old_priorities)
    new_priority_block = "\n".join(f"- {item}" for item in new_priorities)
    return (
        "## Shortlist A (Old Priorities)\n"
        f"{old_priority_block}\n\n"
        f"{old_content.strip()}\n\n"
        "## Shortlist B (New Priorities)\n"
        f"{new_priority_block}\n\n"
        f"{new_content.strip()}\n\n"
        "## AI Comparison Summary\n"
        f"{change_summary.strip()}\n"
    )


def extract_content(response_json: dict, endpoint: str) -> str:
    if endpoint == "/api/chat":
        return response_json["message"]["content"].strip()
    if endpoint == "/v1/chat/completions":
        return response_json["choices"][0]["message"]["content"].strip()
    if endpoint == "/api/generate":
        return response_json["response"].strip()
    raise ValueError(f"Unsupported endpoint parser: {endpoint}")


def call_model(host: str, model: str, prompt_text: str, timeout: int) -> tuple[str, str]:
    system_text = (
        "You are a structured data extractor and decision analyst. "
        "Follow the user's output format exactly."
    )

    endpoint_payloads = [
        (
            "/api/chat",
            {
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": prompt_text},
                ],
            },
        ),
        (
            "/v1/chat/completions",
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": prompt_text},
                ],
                "stream": False,
            },
        ),
        (
            "/api/generate",
            {
                "model": model,
                "stream": False,
                "prompt": f"{system_text}\n\n{prompt_text}",
            },
        ),
    ]

    errors = []
    for endpoint, payload in endpoint_payloads:
        url = f"{host.rstrip('/')}{endpoint}"
        try:
            response = requests.post(url, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            errors.append(f"{endpoint}: request failed ({exc})")
            continue

        if response.status_code == 404:
            body_preview = response.text[:200].replace("\n", " ")
            errors.append(f"{endpoint}: 404 not found ({body_preview})")
            continue

        try:
            response.raise_for_status()
            data = response.json()
            return extract_content(data, endpoint), endpoint
        except Exception as exc:
            errors.append(f"{endpoint}: {exc}")

    error_text = "\n".join(errors)
    raise RuntimeError(f"All endpoint attempts failed:\n{error_text}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a prompt against local Ollama and write output to a file."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--prompt-file",
        default=DEFAULT_PROMPT_FILE,
        help="Path to markdown/text file containing your full user prompt",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Ollama host URL (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    args = parser.parse_args()

    prompt_path = Path(args.prompt_file)
    output_path = create_output_path()

    prompt_template = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt_template:
        raise ValueError(f"Prompt file is empty: {prompt_path}")

    old_prompt_text = build_prompt_with_priorities(prompt_template, OLD_PRIORITIES)
    new_prompt_text = build_prompt_with_priorities(prompt_template, NEW_PRIORITIES)

    installed_models = list_installed_models(args.host, args.timeout)
    model_to_use, requested_but_missing = choose_model(args.model, installed_models)

    if requested_but_missing:
        print(
            f"Requested model '{requested_but_missing}' not installed. "
            f"Using '{model_to_use}' instead."
        )

    print(f"Model: {model_to_use}")
    print(f"Prompt file: {prompt_path}")
    print(f"Output file: {output_path}")

    old_content, old_endpoint = call_model(
        host=args.host,
        model=model_to_use,
        prompt_text=old_prompt_text,
        timeout=args.timeout,
    )
    print(f"Old-priority endpoint used: {old_endpoint}")

    new_content, new_endpoint = call_model(
        host=args.host,
        model=model_to_use,
        prompt_text=new_prompt_text,
        timeout=args.timeout,
    )
    print(f"New-priority endpoint used: {new_endpoint}")

    change_summary, summary_endpoint = generate_change_summary(
        host=args.host,
        model=model_to_use,
        old_content=old_content,
        new_content=new_content,
        timeout=args.timeout,
    )
    print(f"Summary endpoint used: {summary_endpoint}")

    combined_text = build_combined_output(
        old_priorities=OLD_PRIORITIES,
        new_priorities=NEW_PRIORITIES,
        old_content=old_content,
        new_content=new_content,
        change_summary=change_summary,
    )
    output_path.write_text(combined_text, encoding="utf-8")
    print(f"Wrote combined output to: {output_path}")


if __name__ == "__main__":
    main()
