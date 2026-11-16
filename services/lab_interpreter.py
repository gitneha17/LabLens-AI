import math
from datetime import date, datetime


def calculate_age(dob):
    """Calculate age from a date or ISO-format date string."""

    if isinstance(dob, datetime):
        dob = dob.date()

    if isinstance(dob, str):
        try:
            dob = date.fromisoformat(dob)
        except ValueError:
            return None

    if not isinstance(dob, date):
        return None

    today = date.today()
    age = today.year - dob.year

    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1

    return age


def get_unit(patient, field):
    """Get the selected unit or its custom value."""

    unit = str(patient.get(f"{field}_unit") or "Unknown").strip()

    if unit == "Other":
        custom_unit = str(
            patient.get(f"{field}_custom_unit") or ""
        ).strip()

        return custom_unit if custom_unit else "Unknown"

    return unit


def to_number(value):
    """Convert a value to a finite float, or return None."""

    try:
        number = float(value)

        if not math.isfinite(number):
            return None

        return number

    except (ValueError, TypeError):
        return None


def classify_against_range(value, low, high):
    """Compare a result with a valid supplied laboratory range."""

    if value < low:
        return "Below supplied laboratory reference range"

    if value > high:
        return "Above supplied laboratory reference range"

    return "Within supplied laboratory reference range"


def interpret_patient(patient):
    """
    Interpret laboratory results using deterministic Python rules.

    Supplied laboratory ranges take priority when complete and valid.
    Default thresholds are general adult demonstration thresholds,
    not universal laboratory reference intervals or diagnostic criteria.
    """

    age = calculate_age(patient.get("dob"))

    gender = str(
        patient.get("gender") or "Not specified"
    ).strip().lower()

    findings = []

    def add_finding(
        field,
        label,
        status,
        severity="unknown",
        reference="Not available",
        source="Not classified"
    ):
        value = to_number(patient.get(field))

        findings.append({
            "test": label,
            "value": value,
            "unit": get_unit(patient, field),
            "status": status,
            "severity": severity,
            "reference": reference,
            "interpretation_source": source,
        })

    # ---------------------------------------------------------
    # 1. GLUCOSE
    # ---------------------------------------------------------

    value = to_number(patient.get("glucose"))
    unit = get_unit(patient, "glucose")

    test_type = str(
        patient.get("glucose_test_type") or "Not specified"
    ).strip().lower()

    low = patient.get("glucose_ref_low")
    high = patient.get("glucose_ref_high")

    low_supplied = low not in (None, "")
    high_supplied = high not in (None, "")

    if value is None:
        add_finding(
            "glucose",
            "Glucose",
            "Invalid or unavailable value"
        )

    elif unit == "mg/dL" and value < 54:
        add_finding(
            "glucose",
            "Glucose",
            "Critical low",
            "critical",
            "Below 54 mg/dL",
            "Demonstration critical flag"
        )

    elif unit == "mg/dL" and value > 300:
        add_finding(
            "glucose",
            "Glucose",
            "Critical high",
            "critical",
            "Above 300 mg/dL",
            "Demonstration critical flag"
        )

    elif low_supplied or high_supplied:
        low_value = to_number(low)
        high_value = to_number(high)

        if (
            unit == "Unknown"
            or low_value is None
            or high_value is None
            or low_value > high_value
        ):
            add_finding(
                "glucose",
                "Glucose",
                "Unable to classify: invalid or incomplete supplied reference range"
            )

        else:
            status = classify_against_range(
                value, low_value, high_value
            )

            severity = (
                "normal"
                if status == "Within supplied laboratory reference range"
                else "moderate"
            )

            add_finding(
                "glucose",
                "Glucose",
                status,
                severity,
                f"{low_value} to {high_value} {unit}",
                "User-supplied laboratory range"
            )

    elif unit != "mg/dL":
        add_finding(
            "glucose",
            "Glucose",
            "Unable to classify: default thresholds require mg/dL"
        )

    elif test_type != "fasting":
        add_finding(
            "glucose",
            "Glucose",
            "Unable to classify using fasting thresholds: test type is not fasting"
        )

    elif value < 70:
        add_finding(
            "glucose",
            "Glucose",
            "Low",
            "moderate",
            "70 to 99 mg/dL",
            "General adult fasting demonstration thresholds"
        )

    elif value <= 99:
        add_finding(
            "glucose",
            "Glucose",
            "Within general adult fasting range",
            "normal",
            "70 to 99 mg/dL",
            "General adult fasting demonstration thresholds"
        )

    elif value <= 125:
        add_finding(
            "glucose",
            "Glucose",
            "Prediabetes range",
            "moderate",
            "100 to 125 mg/dL",
            "General adult fasting screening thresholds"
        )

    else:
        add_finding(
            "glucose",
            "Glucose",
            "Diabetes range",
            "high",
            "126 mg/dL or above",
            "General adult fasting screening thresholds"
        )

    # ---------------------------------------------------------
    # 2. HAEMOGLOBIN
    # ---------------------------------------------------------

    value = to_number(patient.get("haemoglobin"))
    unit = get_unit(patient, "haemoglobin")

    low = patient.get("haemoglobin_ref_low")
    high = patient.get("haemoglobin_ref_high")

    low_supplied = low not in (None, "")
    high_supplied = high not in (None, "")

    if value is None:
        add_finding(
            "haemoglobin",
            "Haemoglobin",
            "Invalid or unavailable value"
        )

    elif age is not None and age >= 18 and unit == "g/dL" and value < 8:
        add_finding(
            "haemoglobin",
            "Haemoglobin",
            "Critical low",
            "critical",
            "Below 8 g/dL",
            "Demonstration critical flag"
        )

    elif age is not None and age >= 18 and unit == "g/dL" and value > 20:
        add_finding(
            "haemoglobin",
            "Haemoglobin",
            "Critical high",
            "critical",
            "Above 20 g/dL",
            "Demonstration critical flag"
        )

    elif low_supplied or high_supplied:
        low_value = to_number(low)
        high_value = to_number(high)

        if (
            unit == "Unknown"
            or low_value is None
            or high_value is None
            or low_value > high_value
        ):
            add_finding(
                "haemoglobin",
                "Haemoglobin",
                "Unable to classify: invalid or incomplete supplied reference range"
            )

        else:
            status = classify_against_range(
                value, low_value, high_value
            )

            severity = (
                "normal"
                if status == "Within supplied laboratory reference range"
                else "moderate"
            )

            add_finding(
                "haemoglobin",
                "Haemoglobin",
                status,
                severity,
                f"{low_value} to {high_value} {unit}",
                "User-supplied laboratory range"
            )

    elif unit != "g/dL":
        add_finding(
            "haemoglobin",
            "Haemoglobin",
            "Unable to classify: default thresholds require g/dL"
        )

    elif age is None or age < 18:
        add_finding(
            "haemoglobin",
            "Haemoglobin",
            "Unable to classify: adult demonstration thresholds are not applicable"
        )

    elif gender == "male":

        if value < 13.5:
            status = "Below general adult male range"
            severity = "moderate"

        elif value <= 17.5:
            status = "Within general adult male range"
            severity = "normal"

        else:
            status = "Above general adult male range"
            severity = "moderate"

        add_finding(
            "haemoglobin",
            "Haemoglobin",
            status,
            severity,
            "13.5 to 17.5 g/dL",
            "General adult male demonstration thresholds"
        )

    elif gender == "female":

        if value < 12.0:
            status = "Below general adult female range"
            severity = "moderate"

        elif value <= 15.5:
            status = "Within general adult female range"
            severity = "normal"

        else:
            status = "Above general adult female range"
            severity = "moderate"

        add_finding(
            "haemoglobin",
            "Haemoglobin",
            status,
            severity,
            "12.0 to 15.5 g/dL",
            "General adult female demonstration thresholds"
        )

    else:
        add_finding(
            "haemoglobin",
            "Haemoglobin",
            "Unable to classify: sex-specific adult range is unavailable"
        )

    # ---------------------------------------------------------
    # 3. TOTAL CHOLESTEROL
    # ---------------------------------------------------------

    value = to_number(patient.get("cholesterol"))
    unit = get_unit(patient, "cholesterol")

    low = patient.get("cholesterol_ref_low")
    high = patient.get("cholesterol_ref_high")

    low_supplied = low not in (None, "")
    high_supplied = high not in (None, "")

    if value is None:
        add_finding(
            "cholesterol",
            "Total cholesterol",
            "Invalid or unavailable value"
        )

    elif low_supplied or high_supplied:
        low_value = to_number(low)
        high_value = to_number(high)

        if (
            unit == "Unknown"
            or low_value is None
            or high_value is None
            or low_value > high_value
        ):
            add_finding(
                "cholesterol",
                "Total cholesterol",
                "Unable to classify: invalid or incomplete supplied reference range"
            )

        else:
            status = classify_against_range(
                value, low_value, high_value
            )

            severity = (
                "normal"
                if status == "Within supplied laboratory reference range"
                else "moderate"
            )

            add_finding(
                "cholesterol",
                "Total cholesterol",
                status,
                severity,
                f"{low_value} to {high_value} {unit}",
                "User-supplied laboratory range"
            )

    elif unit != "mg/dL":
        add_finding(
            "cholesterol",
            "Total cholesterol",
            "Unable to classify: default thresholds require mg/dL"
        )

    elif value < 200:
        add_finding(
            "cholesterol",
            "Total cholesterol",
            "Desirable",
            "normal",
            "Below 200 mg/dL",
            "General adult demonstration thresholds"
        )

    elif value <= 239:
        add_finding(
            "cholesterol",
            "Total cholesterol",
            "Borderline high",
            "moderate",
            "200 to 239 mg/dL",
            "General adult demonstration thresholds"
        )

    else:
        add_finding(
            "cholesterol",
            "Total cholesterol",
            "High",
            "high",
            "240 mg/dL or above",
            "General adult demonstration thresholds"
        )

    # ---------------------------------------------------------
    # 4. OVERALL REPORT CATEGORY
    # ---------------------------------------------------------

    severities = [item["severity"] for item in findings]

    if "critical" in severities:
        risk_level = "High"

    elif "high" in severities:
        risk_level = "High"

    elif "moderate" in severities:
        risk_level = "Moderate"

    elif all(level == "normal" for level in severities):
        risk_level = "Low"

    else:
        risk_level = "Unable to assess"

    return {
        "age": age,
        "findings": findings,
        "risk_level": risk_level,
    }