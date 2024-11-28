import cv2
import sqlite3
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import os
import time
import pyttsx3  # Optional for audio feedback

# Global Variables
DATABASE_FILE = "password_manager.db"
FACE_FILE = "user_face.jpg"
ENCRYPTION_KEY_FILE = "encryption_key.key"
MASTER_KEY_FILE = "master_key.key"
USER_FOLDER = "users"

# Database Setup
def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Drop the existing table if it exists and recreate it with the username column
    cursor.execute("DROP TABLE IF EXISTS passwords")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            service TEXT NOT NULL,
            encrypted_password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Encryption Key Management
def generate_encryption_key():
    if not os.path.exists(ENCRYPTION_KEY_FILE):
        key = get_random_bytes(16)  # AES key size: 16 bytes
        with open(ENCRYPTION_KEY_FILE, 'wb') as file:
            file.write(key)

def load_encryption_key():
    with open(ENCRYPTION_KEY_FILE, 'rb') as file:
        return file.read()

# AES Encryption Functions
def aes_encrypt(data, key):
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    return base64.b64encode(nonce + ciphertext).decode()

def aes_decrypt(encrypted_data, key):
    encrypted_data = base64.b64decode(encrypted_data.encode())
    nonce = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt(ciphertext).decode()

# Voice Feedback
def speak(message):
    engine = pyttsx3.init()
    engine.say(message)
    engine.runAndWait()

# Master Key Management
def set_master_key(key, username):
    print(f"Setting master key for user {username}...")
    master_key = input("Set a master key for quick login: ")

    if master_key == "":
        # If Enter is pressed without typing anything, we'll set a default key
        master_key = "defaultMasterKey123"  # You can choose to set this as an empty or default value.

    encrypted_master_key = aes_encrypt(master_key, key)

    user_folder = os.path.join(USER_FOLDER, username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    with open(os.path.join(user_folder, MASTER_KEY_FILE), 'w') as file:
        file.write(encrypted_master_key)
    
    speak(f"Master key for {username} has been set.")  # Optional feedback
    print(f"Master key for {username} has been set.")

def verify_master_key(key, username):
    user_folder = os.path.join(USER_FOLDER, username)
    if not os.path.exists(user_folder):
        print(f"No data found for user {username}. Please register.")
        return False
    if not os.path.exists(os.path.join(user_folder, MASTER_KEY_FILE)):
        print("No master key found for the user.")
        return False
    master_key_input = input("Enter master key: ")
    with open(os.path.join(user_folder, MASTER_KEY_FILE), 'r') as file:
        encrypted_master_key = file.read()
    stored_master_key = aes_decrypt(encrypted_master_key, key)
    return master_key_input == stored_master_key

# Facial Recognition with Timeout
def register_or_authenticate_face(mode="register", username=None, timeout=10):
    camera = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    stored_face = cv2.imread(os.path.join(USER_FOLDER, username, FACE_FILE), 0) if mode == "authenticate" and os.path.exists(os.path.join(USER_FOLDER, username, FACE_FILE)) else None

    message = "Registering face..." if mode == "register" else "Authenticating face..."
    speak(message)
    print(message)

    start_time = time.time()

    while time.time() - start_time < timeout:
        ret, frame = camera.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]

            if mode == "register":
                cv2.imwrite(os.path.join(USER_FOLDER, username, FACE_FILE), face)
                speak("Face registered successfully!")
                print("Face registered successfully!")
                camera.release()
                cv2.destroyAllWindows()
                return True
            elif mode == "authenticate":
                if stored_face is not None:
                    face = cv2.resize(face, stored_face.shape[::-1])
                    if cv2.norm(face, stored_face, cv2.NORM_L2) < 5000:
                        speak("Authentication successful!")
                        print("Authentication successful!")
                        camera.release()
                        cv2.destroyAllWindows()
                        return True

        cv2.imshow(message, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()
    speak("Face authentication failed." if mode == "authenticate" else "Face registration failed.")
    print("Face authentication failed." if mode == "authenticate" else "Face registration failed.")
    return False

# Password Manager Functions
def add_password(username, service, password, key):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    encrypted_password = aes_encrypt(password, key)
    cursor.execute("INSERT INTO passwords (username, service, encrypted_password) VALUES (?, ?, ?)", (username, service, encrypted_password))
    conn.commit()
    conn.close()
    speak(f"Password for {service} added successfully.")
    print(f"Password for {service} added successfully.")

def retrieve_passwords(username, key):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT service, encrypted_password FROM passwords WHERE username = ?", (username,))
    rows = cursor.fetchall()
    conn.close()

    for service, encrypted_password in rows:
        decrypted_password = aes_decrypt(encrypted_password, key)
        print(f"Service: {service}, Password: {decrypted_password}")

# Main Program
def main():
    initialize_database()
    generate_encryption_key()
    key = load_encryption_key()

    print("Enter your username:")
    username = input()

    print("1. Register Face\n2. Authenticate and Manage Passwords\n3. Quick Login with Master Key")
    choice = input("Enter your choice: ")

    if choice == "1":
        if register_or_authenticate_face(mode="register", username=username):
            set_master_key(key, username)
            print("\nYou can now set up your password or manage other functions.")
            while True:
                print("\n1. Add Password\n2. View Passwords\n3. Exit")
                action = input("Choose an option: ")

                if action == "1":
                    service = input("Enter service name: ")
                    password = input("Enter password: ")
                    add_password(username, service, password, key)
                    input("Press Enter to continue...")  # Wait for Enter to move to next option
                elif action == "2":
                    retrieve_passwords(username, key)
                    input("Press Enter to continue...")  # Wait for Enter to move to next option
                elif action == "3":
                    break
                else:
                    print("Invalid option. Try again.")
    elif choice == "2":
        if register_or_authenticate_face(mode="authenticate", username=username):
            while True:
                print("\n1. Add Password\n2. View Passwords\n3. Exit")
                action = input("Choose an option: ")

                if action == "1":
                    service = input("Enter service name: ")
                    password = input("Enter password: ")
                    add_password(username, service, password, key)
                    input("Press Enter to continue...")  # Wait for Enter to move to next option
                elif action == "2":
                    retrieve_passwords(username, key)
                    input("Press Enter to continue...")  # Wait for Enter to move to next option
                elif action == "3":
                    break
                else:
                    print("Invalid option. Try again.")
        else:
            print("Authentication failed.")
    elif choice == "3":
        if verify_master_key(key, username):
            while True:
                print("\n1. Add Password\n2. View Passwords\n3. Exit")
                action = input("Choose an option: ")

                if action == "1":
                    service = input("Enter service name: ")
                    password = input("Enter password: ")
                    add_password(username, service, password, key)
                    input("Press Enter to continue...")  # Wait for Enter to move to next option
                elif action == "2":
                    retrieve_passwords(username, key)
                    input("Press Enter to continue...")  # Wait for Enter to move to next option
                elif action == "3":
                    break
                else:
                    print("Invalid option. Try again.")
        else:
            print("Master key verification failed.")
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
