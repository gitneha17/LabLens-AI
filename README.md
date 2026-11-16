# LabLens AI — Smart Patient Records & AI Health Insights

LabLens AI is a Flask-based patient record management application that uses SQLite for persistent storage and the Groq API for AI-assisted explanations of laboratory findings.

The application combines Python-based laboratory interpretation with AI-generated, patient-friendly explanations to produce informational laboratory reports.

## Features

- Create, view, update and delete patient records.
- Validate required fields, email addresses, dates, future dates and non-negative numeric values.
- Accept DOB input in `dd/mm/yyyy`, `dd.mm.yyyy` or ISO `yyyy-mm-dd` format.
- Store patient records persistently using SQLite.
- Generate laboratory reports using Python-based interpretation.
- Generate patient-friendly explanations using the Groq API.
- Display glucose, haemoglobin and total cholesterol findings.
- Consider measurement units and supplied laboratory reference ranges.
- Support fasting glucose interpretation where applicable.
- Generate an overall application-based informational assessment.
- Provide a Python-generated fallback report when the Groq API is unavailable.
- Search patients by name or email.
- Regenerate AI explanations for existing patient records.
- Responsive Bootstrap interface.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend logic and laboratory interpretation |
| Flask | Web application framework |
| SQLite | Patient record storage |
| Groq API | AI-generated explanations |
| Llama 3.3 70B Versatile | AI language model |
| HTML, CSS, JavaScript | Frontend |
| Bootstrap | Responsive interface |

## Requirements

- Python 3.10 or later
- pip
- Internet connection for Groq API requests and CDN-based frontend resources

## Installation and Setup

### 1. Clone or download the project

Open the project folder in Visual Studio Code or a terminal.

### 2. Create a virtual environment

Windows PowerShell:

powershell
python -m venv venv

### 3. Activate the virtual environment

powershell
.\venv\Scripts\Activate.ps1


### 4. Install dependencies

powershell
pip install -r requirements.txt

### 5. Configure environment variables

Copy the example environment file:

powershell
Copy-Item .env.example .env

Open `.env` and configure the following values:

env
GROQ_API_KEY=your_real_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
FLASK_SECRET_KEY=replace-with-a-random-secret

Keep your actual API key private. Never upload `.env` to a public repository.

### 6. Run the application
powershell
python app.py

Open the application in your browser:

http://127.0.0.1:5000

## Groq API Integration

LabLens AI uses the Groq API through the following endpoint:

`https://api.groq.com/openai/v1/chat/completions`

The application reads the API key and model configuration from environment variables.

The Groq API receives prepared laboratory findings containing:

- Laboratory test name
- Result and measurement unit
- Python-generated status
- Reference range

The AI generates short, understandable explanations for these findings.

The application validates the AI response before using it in the report.

Get an API key from:

https://console.groq.com/

## Laboratory Interpretation

The `services/lab_interpreter.py` module performs deterministic Python-based interpretation of:

1. Glucose
2. Haemoglobin
3. Total cholesterol

The interpretation considers relevant patient and test information, including age, gender, measurement units, glucose test type and supplied laboratory reference ranges.

Supplied reference ranges take priority when complete and valid.

When suitable supplied ranges are unavailable, the application may use predefined general adult demonstration or screening thresholds where applicable.

These thresholds are not universal laboratory reference intervals or diagnostic criteria.

## AI Report Generation

The `services/groq_service.py` module manages AI integration and report generation.

The workflow is:

1. Python interprets the laboratory results.
2. Python determines the status of each finding.
3. Python calculates the overall informational assessment.
4. Groq generates short patient-friendly explanations.
5. Python validates the AI response.
6. Python assembles the final laboratory report.

The AI cannot change Python-generated statuses or the overall assessment.

### Fallback Mechanism

If the Groq API key is missing, the API request fails, a timeout occurs or the AI returns an invalid response, the application can generate a fallback report using Python-based explanations.

This allows report generation to continue without depending entirely on the AI service.

## Assignment Test Cases

Use the ten patient entries supplied in the employer's Task 2 PDF.

The application permits duplicate patient details because the assignment includes the same Robyn Pears record twice. Each patient submission receives its own database ID.

Validation test cases include:

- John Hunter: invalid email `hunter@gmail`.
- Peter Larry: invalid calendar date `31.11.2001`.
- Kris Wu: future DOB `19.10.2030` and malformed email `Kris.wu.gmail.com`.

The other seven submissions should pass the basic field validation, subject to the current date and the supplied test data.

The application accepts the employer's dotted DOB format as well as the requested slash format and displays stored dates as `dd/mm/yyyy`.

## Medical Safety and Limitations

LabLens AI is an educational assignment demonstration, not a medical device.

- Laboratory classifications are generated using application-defined Python rules.
- Default thresholds are demonstration or screening thresholds, not diagnostic criteria.
- Supplied laboratory reference ranges are not independently verified.
- Glucose interpretation depends on the recorded test type and measurement unit.
- Haemoglobin interpretation uses age and gender where appropriate.
- Total cholesterol alone cannot determine complete cardiovascular risk.
- Critical flags are application-generated priority indicators, not universal emergency thresholds.
- AI explanations do not constitute medical diagnoses or treatment recommendations.

Patients should consult a qualified healthcare professional for interpretation of their original laboratory reports.

**Report disclaimer:**

"Informational only — not a medical diagnosis."

## Project Structure

text
LabLens-AI/
│
├── app.py
├── database.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── models/
├── routes/
├── services/
│   ├── groq_service.py
│   └── lab_interpreter.py
│
├── utils/
├── templates/
├── static/
│   ├── css/
│   └── js/
│
├── instance/
│   └── lablens.db
│
└── Documentation/
    └── LabLens_AI_Prompt_Documentation.docx

