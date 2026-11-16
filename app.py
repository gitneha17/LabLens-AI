
import os
from datetime import date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)
from dotenv import load_dotenv

from database import init_db, get_db
from utils.validators import validate_patient
from services.groq_service import generate_health_remarks


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY",
    "change-this-development-secret",
)

app.config["DATABASE"] = os.getenv(
    "DATABASE_PATH",
    "instance/lablens.db",
)

os.makedirs("instance", exist_ok=True)

init_db(app.config["DATABASE"])


# --------------------------------------------------
# PATIENT FORM DATA
# --------------------------------------------------

def patient_payload(form):
    """Collect patient information from the form."""

    return {
        "full_name": form.get("full_name", "").strip(),
        "dob": form.get("dob", "").strip(),
        "email": form.get("email", "").strip(),

        "gender": form.get(
            "gender",
            "Not specified",
        ).strip(),

        "glucose": form.get("glucose", "").strip(),

        "glucose_test_type": form.get(
            "glucose_test_type",
            "Not specified",
        ).strip(),

        "glucose_unit": form.get(
            "glucose_unit",
            "Unknown",
        ).strip() or "Unknown",

        "haemoglobin": form.get(
            "haemoglobin",
            "",
        ).strip(),

        "haemoglobin_unit": form.get(
            "haemoglobin_unit",
            "Unknown",
        ).strip() or "Unknown",

        "cholesterol": form.get(
            "cholesterol",
            "",
        ).strip(),

        "cholesterol_unit": form.get(
            "cholesterol_unit",
            "Unknown",
        ).strip() or "Unknown",

        "glucose_ref_low": form.get(
            "glucose_ref_low",
            "",
        ).strip(),

        "glucose_ref_high": form.get(
            "glucose_ref_high",
            "",
        ).strip(),

        "haemoglobin_ref_low": form.get(
            "haemoglobin_ref_low",
            "",
        ).strip(),

        "haemoglobin_ref_high": form.get(
            "haemoglobin_ref_high",
            "",
        ).strip(),

        "cholesterol_ref_low": form.get(
            "cholesterol_ref_low",
            "",
        ).strip(),

        "cholesterol_ref_high": form.get(
            "cholesterol_ref_high",
            "",
        ).strip(),

        "glucose_custom_unit": form.get(
            "glucose_custom_unit",
            "",
        ).strip(),

        "haemoglobin_custom_unit": form.get(
            "haemoglobin_custom_unit",
            "",
        ).strip(),

        "cholesterol_custom_unit": form.get(
            "cholesterol_custom_unit",
            "",
        ).strip(),
    }


# --------------------------------------------------
# HELPER: GENERATE REPORT
# --------------------------------------------------

def generate_patient_report(patient_data):
    """
    Generate Python findings and an optional Groq explanation.

    Returns:
        report: dictionary containing risk_level and remarks
        error: error message if AI explanation is unavailable
    """

    report, error = generate_health_remarks(patient_data)

    if report is None:
        return None, error or "Unable to generate the report."

    return report, error


# --------------------------------------------------
# GLOBAL TEMPLATE VARIABLES
# --------------------------------------------------

@app.context_processor
def inject_globals():
    return {
        "current_year": date.today().year,
    }


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def dashboard():

    db = get_db(app.config["DATABASE"])

    total = db.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    ai_count = db.execute(
        """
        SELECT COUNT(*)
        FROM patients
        WHERE remarks IS NOT NULL
        AND remarks != ''
        """
    ).fetchone()[0]

    recent = db.execute(
        """
        SELECT *
        FROM patients
        ORDER BY created_at DESC, id DESC
        LIMIT 5
        """
    ).fetchall()

    db.close()

    return render_template(
        "dashboard.html",
        total=total,
        ai_count=ai_count,
        recent=recent,
    )


# --------------------------------------------------
# VIEW ALL PATIENTS
# --------------------------------------------------

@app.route("/patients")
def patients():

    search = request.args.get("q", "").strip()

    db = get_db(app.config["DATABASE"])

    if search:

        rows = db.execute(
            """
            SELECT *
            FROM patients
            WHERE full_name LIKE ?
            OR email LIKE ?
            ORDER BY created_at DESC, id DESC
            """,
            (
                f"%{search}%",
                f"%{search}%",
            ),
        ).fetchall()

    else:

        rows = db.execute(
            """
            SELECT *
            FROM patients
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    db.close()

    return render_template(
        "patients.html",
        patients=rows,
        search=search,
    )


# --------------------------------------------------
# ADD PATIENT
# --------------------------------------------------

@app.route("/patients/new", methods=["GET", "POST"])
def add_patient():

    if request.method == "POST":

        data = patient_payload(request.form)

        errors, normalized = validate_patient(data)

        if errors:

            for error in errors:
                flash(error, "error")

            return render_template(
                "add_patient.html",
                data=data,
            )

        # Generate Python findings and AI explanation.
        report, ai_error = generate_patient_report(normalized)

        # Preserve the patient record even if report generation fails.
        if report is None:

            risk_level = "Not assessed"

            remarks = (
                "The report could not be generated. "
                "Please retry from the patient record."
            )

        else:

            risk_level = report["risk_level"]
            remarks = report["remarks"]

        db = get_db(app.config["DATABASE"])

        cursor = db.execute(
            """
            INSERT INTO patients (
                full_name,
                dob,
                email,
                gender,

                glucose,
                glucose_test_type,
                haemoglobin,
                cholesterol,

                glucose_unit,
                haemoglobin_unit,
                cholesterol_unit,

                glucose_custom_unit,
                haemoglobin_custom_unit,
                cholesterol_custom_unit,

                glucose_ref_low,
                glucose_ref_high,
                haemoglobin_ref_low,
                haemoglobin_ref_high,
                cholesterol_ref_low,
                cholesterol_ref_high,

                risk_level,
                remarks
            )
            VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?
            )
            """,
            (
                normalized["full_name"],
                normalized["dob"].isoformat(),
                normalized["email"],
                normalized["gender"],

                normalized["glucose"],
                normalized["glucose_test_type"],
                normalized["haemoglobin"],
                normalized["cholesterol"],

                normalized["glucose_unit"],
                normalized["haemoglobin_unit"],
                normalized["cholesterol_unit"],

                normalized.get("glucose_custom_unit") or None,
                normalized.get("haemoglobin_custom_unit") or None,
                normalized.get("cholesterol_custom_unit") or None,

                normalized.get("glucose_ref_low") or None,
                normalized.get("glucose_ref_high") or None,
                normalized.get("haemoglobin_ref_low") or None,
                normalized.get("haemoglobin_ref_high") or None,
                normalized.get("cholesterol_ref_low") or None,
                normalized.get("cholesterol_ref_high") or None,

                risk_level,
                remarks,
            ),
        )

        db.commit()

        patient_id = cursor.lastrowid

        db.close()

        flash(
            "Patient record created successfully.",
            "success",
        )

        if ai_error:
            flash(
                "Patient saved, but the AI explanation could not "
                "be completed. The available Python findings were "
                "saved. You can retry the report.",
                "warning",
            )

        return redirect(
            url_for(
                "patient_detail",
                patient_id=patient_id,
            )
        )

    return render_template(
        "add_patient.html",
        data={},
    )


# --------------------------------------------------
# PATIENT DETAILS
# --------------------------------------------------

@app.route("/patients/<int:patient_id>")
def patient_detail(patient_id):

    db = get_db(app.config["DATABASE"])

    patient = db.execute(
        "SELECT * FROM patients WHERE id = ?",
        (patient_id,),
    ).fetchone()

    db.close()

    if not patient:
        abort(404)

    return render_template(
        "patient_details.html",
        patient=patient,
    )


# --------------------------------------------------
# EDIT PATIENT
# --------------------------------------------------

@app.route(
    "/patients/<int:patient_id>/edit",
    methods=["GET", "POST"],
)
def edit_patient(patient_id):

    db = get_db(app.config["DATABASE"])

    patient = db.execute(
        "SELECT * FROM patients WHERE id = ?",
        (patient_id,),
    ).fetchone()

    if not patient:
        db.close()
        abort(404)

    if request.method == "POST":

        data = patient_payload(request.form)

        errors, normalized = validate_patient(data)

        if errors:

            db.close()

            for error in errors:
                flash(error, "error")

            return render_template(
                "edit_patient.html",
                patient=patient,
                data=data,
            )

        db.execute(
            """
            UPDATE patients
            SET
                full_name = ?,
                dob = ?,
                email = ?,
                gender = ?,

                glucose = ?,
                glucose_test_type = ?,
                haemoglobin = ?,
                cholesterol = ?,

                glucose_unit = ?,
                haemoglobin_unit = ?,
                cholesterol_unit = ?,

                glucose_custom_unit = ?,
                haemoglobin_custom_unit = ?,
                cholesterol_custom_unit = ?,

                glucose_ref_low = ?,
                glucose_ref_high = ?,
                haemoglobin_ref_low = ?,
                haemoglobin_ref_high = ?,
                
                                cholesterol_ref_low = ?,
                cholesterol_ref_high = ?,

                updated_at = CURRENT_TIMESTAMP
                
            WHERE id = ?
            """,
            (
                normalized["full_name"],
                normalized["dob"].isoformat(),
                normalized["email"],
                normalized["gender"],

                normalized["glucose"],
                normalized["glucose_test_type"],
                normalized["haemoglobin"],
                normalized["cholesterol"],

                normalized["glucose_unit"],
                normalized["haemoglobin_unit"],
                normalized["cholesterol_unit"],

                normalized.get("glucose_custom_unit") or None,
                normalized.get("haemoglobin_custom_unit") or None,
                normalized.get("cholesterol_custom_unit") or None,

                normalized.get("glucose_ref_low") or None,
                normalized.get("glucose_ref_high") or None,
                normalized.get("haemoglobin_ref_low") or None,
                normalized.get("haemoglobin_ref_high") or None,
                normalized.get("cholesterol_ref_low") or None,
                normalized.get("cholesterol_ref_high") or None,

                patient_id,
            ),
        )

        db.commit()
        db.close()

        flash(
            "Patient record updated successfully. "
            "Generate a new report to reflect the updated information.",
            "success",
        )

        return redirect(
            url_for(
                "patient_detail",
                patient_id=patient_id,
            )
        )

    db.close()

    return render_template(
        "edit_patient.html",
        patient=patient,
        data=dict(patient),
    )


# --------------------------------------------------
# DELETE PATIENT
# --------------------------------------------------

@app.route(
    "/patients/<int:patient_id>/delete",
    methods=["POST"],
)
def delete_patient(patient_id):

    db = get_db(app.config["DATABASE"])

    patient = db.execute(
        "SELECT id FROM patients WHERE id = ?",
        (patient_id,),
    ).fetchone()

    if not patient:
        db.close()
        abort(404)

    db.execute(
        "DELETE FROM patients WHERE id = ?",
        (patient_id,),
    )

    db.commit()
    db.close()

    flash(
        "Patient record deleted.",
        "success",
    )

    return redirect(url_for("patients"))


# --------------------------------------------------
# GENERATE / REGENERATE PATIENT REPORT
# --------------------------------------------------

@app.route(
    "/patients/<int:patient_id>/analyze",
    methods=["POST"],
)
def analyze_patient(patient_id):

    db = get_db(app.config["DATABASE"])

    patient = db.execute(
        "SELECT * FROM patients WHERE id = ?",
        (patient_id,),
    ).fetchone()

    if not patient:
        db.close()
        abort(404)

    # Prepare patient information for the interpreter and Groq.
    data = {
        "full_name": patient["full_name"],
        "dob": patient["dob"],
        "gender": patient["gender"],

        "glucose": patient["glucose"],
        "glucose_test_type": patient["glucose_test_type"],
        "glucose_unit": patient["glucose_unit"],
        "glucose_custom_unit": patient["glucose_custom_unit"],
        "glucose_ref_low": patient["glucose_ref_low"],
        "glucose_ref_high": patient["glucose_ref_high"],

        "haemoglobin": patient["haemoglobin"],
        "haemoglobin_unit": patient["haemoglobin_unit"],
        "haemoglobin_custom_unit": patient["haemoglobin_custom_unit"],
        "haemoglobin_ref_low": patient["haemoglobin_ref_low"],
        "haemoglobin_ref_high": patient["haemoglobin_ref_high"],

        "cholesterol": patient["cholesterol"],
        "cholesterol_unit": patient["cholesterol_unit"],
        "cholesterol_custom_unit": patient["cholesterol_custom_unit"],
        "cholesterol_ref_low": patient["cholesterol_ref_low"],
        "cholesterol_ref_high": patient["cholesterol_ref_high"],
    }

    report, error = generate_patient_report(data)

    # If Python interpretation itself fails, do not save an invalid report.
    if report is None:

        db.close()

        flash(
            "Report generation failed: " + str(error),
            "error",
        )

        return redirect(
            url_for(
                "patient_detail",
                patient_id=patient_id,
            )
        )

    # Save the Python-generated risk category and report remarks.
    # This is done even if the Groq explanation is unavailable.
    db.execute(
        """
        UPDATE patients
        SET
            risk_level = ?,
            remarks = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            report["risk_level"],
            report["remarks"],
            patient_id,
        ),
    )

    db.commit()
    db.close()

    if error:

        flash(
            "Python report generated and saved. "
            "AI explanation unavailable: " + str(error),
            "warning",
        )

    else:

        flash(
            "Patient health report generated successfully.",
            "success",
        )

    return redirect(
        url_for(
            "patient_detail",
            patient_id=patient_id,
        )
    )


# --------------------------------------------------
# 404 ERROR HANDLER
# --------------------------------------------------

@app.errorhandler(404)
def not_found(_error):

    return render_template("404.html"), 404


# --------------------------------------------------
# DATE TEMPLATE FILTER
# --------------------------------------------------

@app.template_filter("format_date")
def format_date(value):

    try:
        return date.fromisoformat(
            str(value)
        ).strftime("%d/%m/%Y")

    except (ValueError, TypeError):
        return value


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)
