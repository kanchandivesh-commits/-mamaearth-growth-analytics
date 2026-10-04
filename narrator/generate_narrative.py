import json
import os

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


FINDINGS_PATH = "narrator/findings.json"
OUTPUT_PATH = "narrator/sample_output.txt"


SYSTEM_INSTRUCTION = """
You are a senior growth and operations analyst preparing a concise executive
narrative for Mamaearth operations and finance heads.

Write exactly three labeled sections:
SITUATION
COMPLICATION
RESOLUTION

Use only numbers provided in the findings.
Do not invent statistics.
Keep the tone concise, analytical, and decision-oriented.
"""


def load_findings():
    with open(FINDINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def offline_narrative(findings):
    return f"""SITUATION
Cleaned revenue is ₹{findings["cleaned_total_revenue_inr"]:,.2f}, compared with raw revenue of ₹{findings["raw_total_revenue_inr"]:,.2f}.

COMPLICATION
COD has the highest return rate at {findings["return_rate_by_payment"]["COD"]:.1f}%, while the highest-risk segment is Tier {findings["highest_risk_segment"]["city_tier"]} COD at {findings["highest_risk_segment"]["return_rate_pct"]:.1f}%. Duplicate reconciliation accounts for ₹{findings["duplicate_reconciliation_delta_inr"]:,.2f}.

RESOLUTION
The true revenue peak is {findings["true_peak_month"]["month"]} at ₹{findings["true_peak_month"]["revenue_inr"]:,.2f}. January's apparent ₹{findings["outlier_inflated_month"]["apparent_revenue_inr"]:,.2f} falls to ₹{findings["outlier_inflated_month"]["corrected_revenue_inr"]:,.2f} after correcting for outliers."""


def generate_narrative(findings):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key or genai is None:
        return offline_narrative(findings), "offline"

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30000)
        )

        prompt = (
            "Create the executive narrative using ONLY this findings JSON:\n\n"
            + json.dumps(findings, indent=2)
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.0,
                max_output_tokens=500
            )
        )

        return response.text.strip(), "online"

    except Exception as exc:
        print(f"Gemini generation failed: {exc}")
        print("Using deterministic offline fallback.")
        return offline_narrative(findings), "offline"


def check_narrative(narrative, findings):
    checks = [
        f'{findings["cleaned_total_revenue_inr"]:,.2f}',
        f'{findings["return_rate_by_payment"]["COD"]:.1f}',
        f'{findings["highest_risk_segment"]["return_rate_pct"]:.1f}',
        f'{findings["duplicate_reconciliation_delta_inr"]:,.2f}',
        f'{findings["true_peak_month"]["revenue_inr"]:,.2f}',
    ]

    required_sections = [
        "SITUATION",
        "COMPLICATION",
        "RESOLUTION"
    ]

    for section in required_sections:
        assert section in narrative, f"Missing section: {section}"

    for value in checks:
        assert value in narrative, f"Missing required value: {value}"

    return True


def main():
    findings = load_findings()

    narrative, mode = generate_narrative(findings)

    check_narrative(narrative, findings)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(narrative + "\n")

    print(f"Narrative generated successfully using {mode} mode.")
    print(f"Saved to {OUTPUT_PATH}")
    print("Checker: PASS")


if __name__ == "__main__":
    main()
