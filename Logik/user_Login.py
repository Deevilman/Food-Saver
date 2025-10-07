# user_Login.py

import yaml
import os
import hashlib
import msvcrt  # Kun på Windows til stjerner i terminalen

DB_USERS = r"C:\Users\oller\OneDrive\Desktop\KOD - Food saver\DB\Users"

def password_input(prompt="Password: "):
    """Indtast password med * som feedback i terminalen"""
    print(prompt, end="", flush=True)
    pwd = ""
    while True:
        ch = msvcrt.getch()
        if ch in {b'\r', b'\n'}:  # Enter
            print()
            break
        elif ch == b'\x08':  # Backspace
            if len(pwd) > 0:
                pwd = pwd[:-1]
                print("\b \b", end="", flush=True)
        else:
            pwd += ch.decode(errors="ignore")
            print("*", end="", flush=True)
    return pwd

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def gem_bruger(data):
    filsti = os.path.join(DB_USERS, f"{data['brugernavn']}.yml")
    with open(filsti, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)

def load_bruger(brugernavn):
    filsti = os.path.join(DB_USERS, f"{brugernavn}.yml")
    if os.path.exists(filsti):
        with open(filsti, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return None

def opret_bruger():
    print("=== Opret konto ===")
    brugernavn = input("Brugernavn: ").strip()
    if load_bruger(brugernavn):
        print("Brugernavn findes allerede!")
        return None
    password = password_input("Password: ")
    data = {
        "brugernavn": brugernavn,
        "password_hash": hash_password(password),
        "lager": {}
    }
    gem_bruger(data)
    print(f"Konto '{brugernavn}' oprettet!")
    return data

def login():
    print("=== Login ===")
    brugernavn = input("Brugernavn: ").strip()
    bruger_data = load_bruger(brugernavn)
    if not bruger_data:
        print("Brugernavn findes ikke!")
        return None
    password = password_input("Password: ")
    if bruger_data["password_hash"] != hash_password(password):
        print("Forkert password!")
        return None
    print(f"Velkommen tilbage, {brugernavn}!")
    return bruger_data
