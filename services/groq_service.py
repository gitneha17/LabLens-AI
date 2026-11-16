import json
import os
import requests

from services.lab_interpreter import interpret_patient


GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

DISCLAIMER = "Informational only — not a medical diagnosis."


def format_value(item):
    """Format a test result with its unit."""

    value = item.get("value")
    unit = item.get("unit") or ""

    if value is None:
        return "Not available"

    return f"{value} {unit}".strip()


def explain_finding(item):
    """Generate a safe fallback explanation using Python."""

    status = item.get("status", "")
    reference = item.get("reference", "Not available")
    source = item.get("interpretation_source", "")

    status_lower = status.lower()

    if status.startswith(
        "Unable to classify using fasting thresholds"
    ):
        return (
            "The test was not fasting, so fasting glucose "
            "thresholds cannot be applied."
        )

    if status == "Within general adult male range":
        return (
            "Your result is within the typical adult male "
            f"range of {reference}."
        )

    if status == "Within general adult female range":
        return (
            "Your result is within the typical adult female "
            f"range of {reference}."
        )

    if status == "Above general adult male range":
        return (
            "Your result is above the typical adult male "
            f"range ({reference})."
        )

    if status == "Below general adult male range":
        return (
            "Your result is below the typical adult male "
            f"range ({reference})."
        )

    if status == "Above general adult female range":
        return (
            "Your result is above the typical adult female "
            f"range ({reference})."
        )

    if status == "Below general adult female range":
        return (
            "Your result is below the typical adult female "
            f"range ({reference})."
        )

    if status == "Desirable":
        return (
            "Your result falls within the application's "
            "desirable total cholesterol category."
        )

    if status == "Borderline high":
        return (
            "Your result falls within the application's "
            "borderline high total cholesterol category."
        )

    if status == "High":
        return (
            "Your result falls within the application's "
            "high total cholesterol category."
        )

    if status == "Prediabetes range":
        return (
            "Your result falls within the application's "
            "prediabetes screening category. This is not a diagnosis."
        )

    if status == "Diabetes range":
        return (
            "Your result falls within the application's "
            "diabetes screening category. This is not a diagnosis."
        )

    if status == "Low":
        return (
            "Your result falls below the application's "
            "general demonstration threshold."
        )

    if status == "Within general adult fasting range":
        return (
            f"Your result falls within the general adult "
            f"fasting range ({reference})."
        )

    if status == "Within supplied laboratory reference range":
        return (
            f"Your result is within the supplied laboratory "
            f"reference range ({reference})."
        )

    if status == "Above supplied laboratory reference range":
        return (
            f"Your result is above the supplied laboratory "
            f"reference range ({reference})."
        )

    if status == "Below supplied laboratory reference range":
        return (
            f"Your result is below the supplied laboratory "
            f"reference range ({reference})."
        )

    if "critical" in status_lower:
        return (
            "This result has triggered an application-generated "
            "priority flag. Please seek prompt review from a "
            "qualified healthcare professional."
        )

    if "invalid or incomplete supplied reference range" in status_lower:
        return (
            "The supplied reference range is incomplete or invalid, "
            "so this result cannot be compared reliably."
        )

    if "adult demonstration thresholds are not applicable" in status_lower:
        return (
            "Adult demonstration thresholds cannot be applied "
            "to this patient's age."
        )

    if "sex-specific adult range is unavailable" in status_lower:
        return (
            "A suitable adult reference range is unavailable "
            "for the recorded gender."
        )

    if "default thresholds require" in status_lower:
        return (
            "The selected unit does not match the application's "
            "default thresholds."
        )

    if "invalid or unavailable" in status_lower:
        return "A valid test result was not available."

    if source == "User-supplied laboratory range":
        return (
            f"Your result was compared with the supplied "
            f"laboratory range ({reference})."
        )

    return (
        "There is not enough information to interpret this "
        "result reliably."
    )


def create_fallback_remarks(risk_level, findings):
    """Create a complete report without depending on Groq."""

    lines = [
        "YOUR LAB TEST SUMMARY",
        "",
        f"Overall assessment: {risk_level}",
        "",
    ]

    for index, item in enumerate(findings, start=1):
        lines.extend([
            f"{index}. {item.get('test', 'Laboratory test')}",
            f"Result: {format_value(item)}",
            f"Status: {item.get('status', 'Unable to assess')}",
            explain_finding(item),
            "",
        ])

    lines.extend([
        "Recommended next step:",
        "Check your original laboratory report and discuss "
        "the findings with a qualified healthcare professional.",
        "",
        "Note: This overall assessment is an application-generated "
        "informational category, not a clinical diagnosis. "
        "Supplied reference ranges have not been independently verified.",
        "",
        "Total cholesterol alone cannot determine complete "
        "cardiovascular risk.",
        "",
        DISCLAIMER,
    ])

    return "\n".join(lines)


def generate_ai_explanations(findings, api_key, model):
    """
    Ask Groq for short explanations only.

    Python-generated statuses and classifications are not changed.
    """

    findings_data = []

    for item in findings:
        findings_data.append({
            "test": item.get("test"),
            "value": format_value(item),
            "status": item.get("status"),
            "reference": item.get("reference"),
        })

    prompt = f"""
You are assisting with a laboratory report.

Generate one short, simple, patient-friendly explanation
for each finding below.

FINDINGS:
{json.dumps(findings_data, ensure_ascii=False)}

STRICT RULES:
1. Return only a valid JSON object.
2. Use this exact structure:
   {{
       "explanations": [
           "Explanation for finding 1",
           "Explanation for finding 2"
       ]
   }}
3. Return exactly one explanation per finding, in the same order.
4. Do not change, repeat, or reinterpret the supplied statuses.
5. Do not invent reference ranges or medical information.
6. Do not provide a diagnosis or treatment advice.
7. Keep each explanation to one short sentence.
8. For glucose, mention fasting limitations when applicable.
9. For total cholesterol, do not claim that it determines
   complete cardiovascular risk.
"""

    response = requests.post(
        GROQ_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate concise explanations for "
                        "laboratory findings. Return valid JSON only. "
                        "Never diagnose or change supplied statuses."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": 700,
            "response_format": {
                "type": "json_object"
            },
        },
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    content = (
        payload["choices"][0]["message"]["content"].strip()
    )

    if not content:
        raise ValueError("The AI returned an empty response.")

    result = json.loads(content)

    explanations = result.get("explanations")

    if not isinstance(explanations, list):
        raise ValueError("Invalid AI explanation format.")

    if len(explanations) != len(findings):
        raise ValueError("AI explanation count does not match findings.")

    cleaned_explanations = []

    for explanation in explanations:
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("An AI explanation is empty or invalid.")

        cleaned_explanations.append(explanation.strip())

    return cleaned_explanations


def assemble_report(risk_level, findings, explanations):
    """Build the final report using Python-controlled statuses."""

    lines = [
        "YOUR LAB TEST SUMMARY",
        "",
        f"Overall assessment: {risk_level}",
        "",
    ]

    for index, item in enumerate(findings):
        explanation = explanations[index]

        lines.extend([
            f"{index + 1}. {item.get('test', 'Laboratory test')}",
            f"Result: {format_value(item)}",
            f"Status: {item.get('status', 'Unable to assess')}",
            explanation,
            "",
        ])

    lines.extend([
        "Recommended next step:",
        "Check your original laboratory report and discuss "
        "the findings with a qualified healthcare professional.",
        "",
        "Note: This overall assessment is an application-generated "
        "informational category, not a clinical diagnosis. "
        "Supplied reference ranges have not been independently verified.",
        "",
        "Total cholesterol alone cannot determine complete "
        "cardiovascular risk.",
        "",
        DISCLAIMER,
    ])

    return "\n".join(lines)


def generate_health_remarks(patient):
    """
    Generate a laboratory report.

    Python determines classifications and risk level.
    Groq generates explanations only.

    Returns:
        (report_dictionary, error_message)
    """

    # STEP 1: Python interpretation

    try:
        interpretation = interpret_patient(patient)

        risk_level = interpretation["risk_level"]
        findings = interpretation["findings"]

    except (KeyError, TypeError, ValueError) as exc:
        return None, f"Python interpretation failed: {exc}"

    # STEP 2: Create a fallback report

    report = {
        "risk_level": risk_level,
        "remarks": create_fallback_remarks(
            risk_level,
            findings
        ),
        "findings": findings,
    }

    # STEP 3: Get Groq configuration

    api_key = os.getenv("GROQ_API_KEY", "").strip()

    model = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    ).strip()

    if not api_key or api_key == "your_groq_api_key_here":
        return report, "GROQ_API_KEY is missing."

    # STEP 4: Generate explanations

    try:
        explanations = generate_ai_explanations(
            findings,
            api_key,
            model
        )

        # Python assembles the final report.
        # Groq cannot modify the classifications.

        report["remarks"] = assemble_report(
            risk_level,
            findings,
            explanations
        )

        return report, None

    except requests.Timeout:
        return report, "Groq API request timed out."

    except requests.RequestException as exc:
        detail = "The Groq API request failed."

        try:
            detail = (
                exc.response.json()
                .get("error", {})
                .get("message", detail)
            )
        except (AttributeError, ValueError, TypeError):
            pass

        return report, detail

    except (KeyError, ValueError, TypeError, AttributeError):
        return report, (
            "Groq returned an unexpected response. "
            "The Python-generated fallback report is being used."
        )