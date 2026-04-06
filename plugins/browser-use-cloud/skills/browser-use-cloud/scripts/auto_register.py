#!/usr/bin/env python3
"""
Auto-register for a free Browser Use Cloud API key.

Usage:
    python3 auto_register.py

The script requests a math challenge, prints it for LLM solving,
then submits the answer to get a fresh API key.

Each free key provides ~$0.10 in credits (~100 Browser-mode sessions).
"""

import json
import sys
from urllib.request import Request, urlopen

API_BASE = "https://api.browser-use.com"

# CJK numeral mapping for challenge solving
CJK_NUMERALS = {
    # Korean
    "일": 1, "이": 2, "삼": 3, "사": 4, "오": 5,
    "육": 6, "칠": 7, "팔": 8, "구": 9, "십": 10,
    "백": 100, "천": 1000,
    # Chinese
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    "百": 100, "千": 1000,
    # Japanese
    "零": 0, "壱": 1, "弐": 2, "参": 3,
}


def request_challenge(name="auto-agent"):
    """Step 1: Request a signup challenge."""
    req = Request(
        f"{API_BASE}/cloud/signup",
        data=json.dumps({"name": name}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urlopen(req).read())


def verify_answer(challenge_id, answer):
    """Step 3: Submit answer and receive API key."""
    req = Request(
        f"{API_BASE}/cloud/signup/verify",
        data=json.dumps({
            "challenge_id": challenge_id,
            "answer": answer,
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urlopen(req).read())


def claim_account(api_key):
    """Optional: Generate a claim URL to bind to a human account."""
    req = Request(
        f"{API_BASE}/cloud/signup/claim",
        headers={
            "Content-Type": "application/json",
            "X-Browser-Use-API-Key": api_key,
        },
        method="POST",
    )
    return json.loads(urlopen(req).read())


def clean_challenge(text):
    """Remove noise characters from challenge text."""
    noise = set("~!@#$%^&*(){}[]|\\/<>?;:`.,-_")
    cleaned = []
    for ch in text:
        if ch in noise:
            cleaned.append(" ")
        else:
            cleaned.append(ch)
    result = " ".join("".join(cleaned).split())
    # Replace CJK numerals
    for cjk, num in CJK_NUMERALS.items():
        result = result.replace(cjk, str(num))
    return result


def main():
    print("=" * 50)
    print("Browser Use Cloud — Auto Registration")
    print("=" * 50)

    # Step 1
    print("\n[1/3] Requesting challenge...")
    resp = request_challenge()
    challenge_id = resp["challenge_id"]
    raw_text = resp["challenge_text"]

    print(f"\nRaw challenge:\n  {raw_text}")
    print(f"\nCleaned:\n  {clean_challenge(raw_text)}")

    # Step 2
    print("\n[2/3] Solve the math problem above.")
    print("Answer format: string with 2 decimal places, e.g. '144.00'")
    answer = input("\nYour answer: ").strip()

    # Step 3
    print("\n[3/3] Verifying...")
    try:
        result = verify_answer(challenge_id, answer)
        api_key = result["api_key"]
        print(f"\n{'=' * 50}")
        print(f"API Key: {api_key}")
        print(f"{'=' * 50}")
        print(f"\nExport it:")
        print(f"  export BROWSER_USE_API_KEY='{api_key}'")
        print(f"\nAdd to Claude Code MCP:")
        print(f'  claude mcp add -t http -s user \\')
        print(f'    -H "x-browser-use-api-key: {api_key}" \\')
        print(f'    -- browser-use https://api.browser-use.com/v3/mcp')
    except Exception as e:
        print(f"\nVerification failed: {e}")
        print("Check your answer and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
