# SecurePassManager-with-AES-Encryption-

# SecurePassManager

A **secure password manager** that combines **facial recognition**, **AES encryption**, and **master key authentication** to ensure robust protection for your passwords. This application supports user-friendly password management with quick login features and optional audio feedback.

---

## Features
- **Facial Recognition**:
  - Register and authenticate using your face.
  - Enhanced security with real-time face matching.

- **AES Encryption**:
  - Passwords are securely encrypted using AES (EAX mode).
  - Encryption key management ensures data security.

- **Master Key Authentication**:
  - Set and verify a master key for quick and secure login.

- **Password Manager**:
  - Add, view, and securely store passwords tied to your account.

- **Audio Feedback (Optional)**:
  - Receive spoken feedback for operations using `pyttsx3`.

---

## Requirements
Ensure you have the following dependencies installed:

- Python 3.7+
- Libraries:
  - `opencv-python`
  - `pyttsx3`
  - `pycryptodome`
- SQLite (built into Python)
- Camera (for facial recognition)

Install required Python packages using:
```bash
pip install opencv-python pyttsx3 pycryptodome
