# Smart Tamper Detection System

A Flask-based academic prototype for registering files and checking whether a later copy has changed. The application uses SHA-256 hashing with a per-file random salt, stores fingerprints and verification history in SQLite, and displays an experimental machine-learning risk label.

## Features

- File registration using SHA-256.
- Random salt generation for each registered file.
- File integrity verification.
- Detection of modified files.
- SQLite-based verification history.
- Dashboard with file and verification statistics.
- Experimental AI-based risk prediction using a Decision Tree.

## Technologies Used

- Python
- Flask
- SHA-256 Hashing
- SQLite
- HTML and CSS
- Pandas
- Scikit-learn
- Joblib

## Project Structure

```text
smart-tamper-project/
├── app.py
├── db_init.py
├── train_ai.py
├── training_data.csv
├── requirements.txt
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── verify.html
│   └── result.html
├── model/
├── uploads/
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Ha-rshu/smart-tamper-project.git
cd smart-tamper-project
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Train the AI model

```bash
mkdir model
python train_ai.py
```

The training script requires `training_data.csv` with the expected feature and risk columns.

### 5. Run the application

```bash
python app.py
```

Open your browser at:

http://127.0.0.1:5000/

## How It Works

1. A user logs into the application.
2. A file is uploaded and registered.
3. The application calculates its SHA-256 hash.
4. A random salt is generated and combined with the hash to create a fingerprint.
5. The fingerprint is stored in the SQLite database.
6. During verification, the submitted file is hashed again.
7. The new fingerprint is compared with the stored fingerprint.
8. The system reports whether the file is verified or tampered.
9. An experimental AI model predicts a risk category.

## Security Notes

This is an educational prototype, not a production-ready security system.

- Replace hardcoded login credentials with secure authentication.
- Store Flask secret keys in environment variables.
- Disable debug mode outside local development.
- Do not publish private databases, uploaded files, or secrets.
- Treat AI risk predictions as experimental, not as definitive security assessments.

## Future Enhancements

- Secure user authentication.
- Improved AI risk prediction.
- Email or dashboard alerts.
- Detailed audit logs.
- Cloud-based file integrity monitoring.
- Automated testing and deployment.


