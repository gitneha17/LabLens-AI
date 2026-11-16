
import re
from datetime import date, datetime


ALLOWED_GENDERS = {
    "Male",
    "Female",
    "Other",
    "Prefer not to say",
    "Not specified",
}

ALLOWED_GLUCOSE_TYPES = {
    "Fasting",
    "Random",
    "Not specified",
}

ALLOWED_UNITS = {
    "glucose_unit": {
        "mg/dL",
        "mmol/L",
        "Other",
        "Unknown",
    },
    "haemoglobin_unit": {
        "g/dL",
        "g/L",
        "mmol/L",
        "Other",
        "Unknown",
    },
    "cholesterol_unit": {
        "mg/dL",
        "mmol/L",
        "Other",
        "Unknown",
    },
}


def validate_reference_range(data, field, label, normalized, errors):
    """
    Validate optional laboratory reference ranges.

    Both lower and upper values must be provided together.
    """

    low_raw = data.get(f"{field}_ref_low", "").strip()
    high_raw = data.get(f"{field}_ref_high", "").strip()

    low = None
    high = None

    if not low_raw and not high_raw:
        normalized[f"{field}_ref_low"] = None
        normalized[f"{field}_ref_high"] = None
        return

    if not low_raw or not high_raw:
        errors.append(
            f"{label}: provide both lower and upper "
            "reference range values, or leave both blank."
        )

        normalized[f"{field}_ref_low"] = None
        normalized[f"{field}_ref_high"] = None
        return

    try:
        low = float(low_raw)
        high = float(high_raw)

        if not (0 <= low <= 100000):
            raise ValueError

        if not (0 <= high <= 100000):
            raise ValueError

        if low > high:
            errors.append(
                f"{label}: lower reference value cannot "
                "exceed the upper reference value."
            )

    except (ValueError, TypeError):
        errors.append(
            f"{label}: reference range values must be "
            "valid non-negative numbers."
        )

        low = None
        high = None

    normalized[f"{field}_ref_low"] = low
    normalized[f"{field}_ref_high"] = high


def validate_patient(data):
    errors = []
    normalized = {}

    # Full name
    name = data.get("full_name", "").strip()

    if not name:
        errors.append("Full name is required.")
    elif len(name) > 100:
        errors.append(
            "Full name must be 100 characters or fewer."
        )

    normalized["full_name"] = name

    # Date of birth
    raw_dob = data.get("dob", "").strip()
    parsed_dob = None

    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            parsed_dob = datetime.strptime(
                raw_dob,
                fmt
            ).date()
            break
        except ValueError:
            continue

    if not raw_dob:
        errors.append("Date of birth is required.")

    elif parsed_dob is None:
        errors.append(
            "Date of birth must be a valid date "
            "in dd/mm/yyyy format."
        )

    elif parsed_dob > date.today():
        errors.append(
            "Date of birth cannot be in the future."
        )

    normalized["dob"] = parsed_dob

    # Email
    email = data.get("email", "").strip()

    email_pattern = (
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)
    
    
    if not email:
        errors.append("Email address is required.")

    elif len(email) > 254 or not re.match(
        email_pattern,
        email
    ):
        errors.append(
            "Enter a valid email address, "
            "such as name@example.com."
        )

    normalized["email"] = email

    # Gender
    gender = data.get(
        "gender",
        "Not specified"
    ).strip()

    if not gender:
        gender = "Not specified"

    if gender not in ALLOWED_GENDERS:
        errors.append(
            "Please select a valid gender option."
        )
        gender = "Not specified"

    normalized["gender"] = gender

    # Glucose test type
    glucose_test_type = data.get(
        "glucose_test_type",
        "Not specified"
    ).strip()

    if not glucose_test_type:
        glucose_test_type = "Not specified"

    if glucose_test_type not in ALLOWED_GLUCOSE_TYPES:
        errors.append(
            "Please select a valid glucose test type."
        )
        glucose_test_type = "Not specified"

    normalized["glucose_test_type"] = glucose_test_type

    # Blood test values
    numeric_fields = [
        ("glucose", "Glucose"),
        ("haemoglobin", "Haemoglobin"),
        ("cholesterol", "Cholesterol"),
    ]

    for field, label in numeric_fields:
        raw_value = str(
            data.get(field, "")
        ).strip()

        try:
            value = float(raw_value)

            if not (0 <= value <= 100000):
                raise ValueError

            normalized[field] = value

        except (ValueError, TypeError):
            errors.append(
                f"{label} must be a valid "
                "non-negative numeric value."
            )
            normalized[field] = None

    # Measurement units
    for field, allowed_values in ALLOWED_UNITS.items():

        unit = data.get(
            field,
            "Unknown"
        ).strip()

        if not unit:
            unit = "Unknown"

        if unit not in allowed_values:
            errors.append(
                f"Please select a valid option for "
                f"{field.replace('_', ' ')}."
            )
            unit = "Unknown"

        if unit == "Other":
            custom_unit_field = field.replace("_unit", "_custom_unit")

            custom_unit = data.get(
                custom_unit_field,
                ""
            ).strip()

            if not custom_unit:
                errors.append(
                    f"Please enter the custom unit for "
                    f"{field.replace('_', ' ')}."
                )
            elif len(custom_unit) > 30:
                errors.append(
                    "Custom measurement units must be "
                    "30 characters or fewer."
                )

            normalized[custom_unit_field] = custom_unit

        normalized[field] = unit

    # Optional laboratory reference ranges
    reference_fields = [
        ("glucose", "Glucose"),
        ("haemoglobin", "Haemoglobin"),
        ("cholesterol", "Cholesterol"),
    ]

    for field, label in reference_fields:
        validate_reference_range(
            data,
            field,
            label,
            normalized,
            errors
        )

    return errors, normalized
