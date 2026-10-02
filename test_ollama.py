import json
import sys

import requests


def main():
    prompt = "Create a simple family tree in JSON for Raj, Neha, and their children Abhay and Kavya."
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "tinyllama", "prompt": prompt},
            stream=True,
            timeout=(3, 60),
        )
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                print(chunk.get("response", ""), end="", flush=True)
        print()
        return 0
    except (requests.RequestException, ValueError) as error:
        print(f"Ollama check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
