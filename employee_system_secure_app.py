#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import getpass
import hashlib
import os
import re
import secrets
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence, Tuple

from colorama import Fore, Style, init
from tabulate import tabulate

# Initialize colorama
init(autoreset=True)

# ---------------------------
# Configuration / defaults
# ---------------------------
DB_FILE = "Employees.db"
"""
Employee HR Management System (with CSV export)
- Uses PBKDF2 for admin passwords
- switch DB file with set_db_file(path) or CLI --db argument
- robust input validation using strip() and isdigit()
- CSV export added

import sqlite3
import re
import sys
import os
import getpass
import hashlib
import secrets
from tabulate import tabulate
from colorama import Fore, Style, init
import argparse
import csv
from datetime import datetime
from pathlib import Path

init(autoreset=True)

# Default DB file (can be changed via set_db_file or CLI)
DB_FILE = "Employees.db"
"""
# PBKDF2 settings
HASH_NAME = "sha256"
ITERATIONS = 150_000
SALT_BYTES = 16
KEY_LEN = 32

NAME_RE = re.compile(r"^[A-Za-z .'\-]{2,70}$")
DEPT_RE = re.compile(r"^[A-Za-z0-9 &\-\_]{1,40}$")
POSITION_RE = re.compile(r"^[A-Za-z0-9 .,&'\-\/]{1,60}$")


# ---------------------------
# Database helpers
# ---------------------------
def set_db_file(path: str) -> None:
    """Set the global DB file path for the running process."""

# ---------------------------
# DB connection helpers
# ---------------------------
def set_db_file(path: str):
    """Set the global DB file path at runtime (for demos, tests, per-customer files)."""
    global DB_FILE
    DB_FILE = path


def get_connection(db_file: Optional[str] = None) -> sqlite3.Connection:
    """Return a sqlite3 connection for the configured DB file."""
    path = db_file or DB_FILE
    if path != ":memory:":
        # ensure directory exists
        dirpath = os.path.dirname(os.path.abspath(path))
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
def get_connection(db_file: str = None):
    Return a sqlite3.Connection to DB_FILE or to db_file if provided.
    Use this everywhere to allow easy switching.
    path = db_file or DB_FILE
    # ensure directory exists for file-based DB
    if path != ":memory:":
        dirpath = os.path.dirname(os.path.abspath(path))
        if dirpath and not os.path.exists(dirpath):
            try:
                os.makedirs(dirpath, exist_ok=True)
            except Exception:
                pass
    conn = sqlite3.connect(path, timeout=10)
    return conn


def execute_query(query: str, params: Sequence = (), fetch: bool = False, fetchone: bool = False, commit: bool = False):
   """ Execute a SQL statement with safe parameterization.
    Returns:
      - None on error
      - list of rows if fetch=True
      - single row if fetchone=True
      - [] if no rows
   """
def execute_query(query, params=(), fetch=False, fetchone=False, commit=False):
   """" Helper to run queries safely. Returns:
      - None on error,
      - list of tuples if fetch=True,
      - single tuple if fetchone=True,
      - [] for no rows.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            result = None
            if fetchone:
                result = cur.fetchone()
            elif fetch:
                result = cur.fetchall()
            if commit:
                conn.commit()
            cur.close()
            return result
    except Exception as exc:  # pragma: no cover - runtime error reporting
        print (Fore.RED + f"[DB ERROR] {exc}")
    except Exception as e:
        print (Fore.RED + f"[DB ERROR] {e}")
        return None


# ---------------------------
# Password hashing helpers
# ---------------------------
def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """Return tuple (salt_hex, key_hex)."""
def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = secrets.token_bytes(SALT_BYTES)
    key = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, ITERATIONS, dklen=KEY_LEN)
    return salt.hex(), key.hex()


def verify_password(password: str, salt_hex: str, key_hex: str) -> bool:
def verify_password(password: str, salt_hex: str, key_hex: str):
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(key_hex)
    key = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, ITERATIONS, dklen=len(expected))
    return secrets.compare_digest(key, expected)


# ---------------------------
# Validation helpers
# ---------------------------
# Input validation helpers
# ---------------------------
NAME_RE = re.compile(r"^[A-Za-z .'\-]{2,70}$")
DEPT_RE = re.compile(r"^[A-Za-z0-9 &\-\_]{1,40}$")
POSITION_RE = re.compile(r"^[A-Za-z0-9 .,&'\-\/]{1,60}$")


def validate_name(name: str) -> bool:
    return bool(NAME_RE.match(name.strip()))


def validate_department(dept: str) -> bool:
    return bool(DEPT_RE.match(dept.strip()))


def validate_position(pos: str) -> bool:
    return bool(POSITION_RE.match(pos.strip()))

def parse_int(s: Optional[str]) -> Tuple[bool, Optional[int]]:
    """Parse integer with optional comma separators. Reject negatives."""
def parse_int(s: str):
    """
    Strip and parse an integer. Accepts comma separators (e.g. "50,000").
    Uses isdigit() after sanitizing. Rejects negative numbers.
    Returns (ok: bool, value: int | None)
    """
    if s is None:
        return False, None
    s2 = s.strip().replace(",", "")
    if s2.isdigit():
        val = int(s2)
        if val < 0:
            return False, None
        return True, val
    return False, None


# ---------------------------
# Initialization and seed
# ---------------------------
def init_db() -> None:
    """Create required tables if they do not exist."""
# Database initialization
# ---------------------------
def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS Employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            salary INTEGER NOT NULL,
            UNIQUE(name, department)
        );
        """
        )
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS Admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            passhash TEXT NOT NULL
        );
        """
        )
        conn.commit()
        cur.close()


def seed_default_data() -> None:
    """Seed sample data if Employees is empty (safe for demos)."""
def seed_default_data():
    # only seed if table empty
    res = execute_query("SELECT COUNT(*) FROM Employees;", fetchone=True)
    if res is None:
        return
    count = res[0]
    if count == 0:
        employees = [
            ("Albert Einstein", "IT", "Manager", 55000)
            ("Segio Abar", "Finance", "Manager", 50000)
            ("Paul Skywalker", "IT", "Developer", 35000)
            ("John Smith", "IT", "Director", 80000)
            ("Michael Sheen", "Health", "Administrator", 20000)
            ("Muhammed Ashar", "IT", "Data Analyst", 40000)
            ("Malcom Mayer", "Health", "Data Analyst", 40000)
            ("Bumpy Jay", "Finance", "Accountant", 80000)
            ("Ryan Booth", "Finance", "Director", 50000)
            ("James Reece", "IT", "PS", 90000)
        ]
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.executemany(
                    "INSERT OR IGNORE INTO Employees (name, department, position, salary) VALUES (?, ?, ?, ?);",
                    employees,
                )
                conn.commit()
                cur.close()
                print (Fore.GREEN + "Default Employee Data Added Successfully!")
        except Exception as exc:  # pragma: no cover
            print (Fore.RED + f"[Seed Error] {exc}")
    else:
        print (Fore.BLUE + "Employee Data Already Exists, skipping insert...")


def remove_duplicates() -> None:
    """Remove duplicate employee rows (keep lowest id)."""
                print (Fore.GREEN + "Default Employee Data Added Successfully!")
        except Exception as e:
            print (Fore.RED + f"[Seed Error] {e}")
    else:
        print (Fore.BLUE + "Employee Data Already Exists, skipping insert...")


def remove_duplicates():
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
            DELETE FROM Employees
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM Employees
                GROUP BY name, department
            );
            """
            )
            conn.commit()
            cur.close()
        print (Fore.GREEN + "✅ Duplicate records removed.")
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Cleanup Error] {exc}")


# ---------------------------
# Admin helpers
# ---------------------------
def admin_exists() -> bool:
        print (Fore.GREEN + "✅ Duplicate records removed.")
    except Exception as e:
        print (Fore.RED + f"[Cleanup Error] {e}")


# ---------------------------
# Admin functions
# ---------------------------
def admin_exists():
    r = execute_query("SELECT COUNT(*) FROM Admins;", fetchone=True)
    return bool(r and r[0] > 0)


def set_admin_password_interactive() -> None:
    """Interactive admin password creation/upsert."""
    print (Fore.CYAN + "=== Set Admin Password ===")
def set_admin_password_interactive():
    print (Fore.CYAN + "=== Set Admin Password ===")
    username = input("Admin username (default 'admin'): ").strip() or "admin"
    while True:
        pw = getpass.getpass("Enter new password: ")
        pw2 = getpass.getpass("Confirm password: ")
        if pw != pw2:
            print (Fore.RED + "Passwords do not match — try again.")
            continue
        if len(pw) < 6:
            print (Fore.RED + "Password too short — minimum 6 characters.")
            continue
        salt_hex, key_hex = hash_password(pw)
        try:
            execute_query(
                """
            INSERT INTO Admins (username, salt, passhash)
            VALUES (?, ?, ?)
            ON CONFLICT(username)
            DO UPDATE SET salt=excluded.salt, passhash=excluded.passhash;
            """,
                (username, salt_hex, key_hex),
                commit=True,
            )
            print (Fore.GREEN + "Admin password set.")
            break
        except Exception as exc:  # pragma: no cover
            print (Fore.RED + f"[Admin Save Error] {exc}")
            break


def login() -> bool:
    """Prompt for login and verify credentials."""
    print (Fore.CYAN + Style.BRIGHT + "\n=== Admin Login ===")
    username = input("Admin username: ").strip()
    pw = getpass.getpass("Password: ")
    try:
        row = execute_query("SELECT salt, passhash FROM Admins WHERE username=?;", (username,), fetchone=True)
        if not row:
            print (Fore.RED + "Unknown admin username.")
            return False
        salt_hex, key_hex = row
        if verify_password(pw, salt_hex, key_hex):
            print (Fore.GREEN + "\n--- Welcome back Admin! ---")
            return True
        print (Fore.RED + "\n⚠️ Wrong Credentials!")
        return False
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Login Error] {exc}")
            print (Fore.RED + "Passwords do not match — try again.")
            continue
        if len(pw) < 6:
            print (Fore.RED + "Password too short — minimum 6 characters.")
            continue
        salt_hex, key_hex = hash_password(pw)
        try:
            # upsert using ON CONFLICT
            execute_query(
                          """
                          INSERT INTO Admins (username, salt, passhash)
                          VALUES (?, ?, ?)
                          ON CONFLICT(username)
                          DO UPDATE SET salt=excluded.salt, passhash=excluded.passhash;
                          """,
                          (username, salt_hex, key_hex), commit=True)

            print (Fore.GREEN + "Admin password set.")
            break
        except Exception as e:
            print (Fore.RED + f"[Admin Save Error] {e}")
            break


def login():
    print (Fore.CYAN + Style.BRIGHT + "\n=== Admin Login ===")
    username = input("Admin username: ").strip()
    pw = getpass.getpass("Password: ")

    try:
        row = execute_query("SELECT salt, passhash FROM Admins WHERE username=?;", (username,), fetchone=True)
        if not row:
            print (Fore.RED + "Unknown admin username.")
            return False
        salt_hex, key_hex = row
        if verify_password(pw, salt_hex, key_hex):
            print (Fore.GREEN + "\n--- Welcome back Admin! ---")
            return True
        else:
            print (Fore.RED + "\n⚠️ Wrong Credentials!")
            return False
    except Exception as e:
        print (Fore.RED + f"[Login Error] {e}")
        return False


# ---------------------------
# CRUD / Reports
# ---------------------------
def add_employee() -> None:
    print (Fore.CYAN + Style.BRIGHT + "\n=== Add Employee ===")
    name = input("Enter Name: ").strip()
    if not validate_name(name):
        print (Fore.RED + "Invalid name. Use letters and common punctuation (2-70 chars).")
        return
    department = input("Enter Department: ").strip()
    if not validate_department(department):
        print (Fore.RED + "Invalid department name.")
        return
    position = input("Enter Position: ").strip()
    if not validate_position(position):
        print (Fore.RED + "Invalid position.")
#---------------------------
# CRUD and reports
# ---------------------------
def add_employee():
    print (Fore.CYAN + Style.BRIGHT + "\n=== Add Employee ===")
    name = input("Enter Name: ").strip()
    if not validate_name(name):
        print (Fore.RED + "Invalid name. Use letters and common punctuation (2-70 chars).")
        return
    department = input("Enter Department: ").strip()
    if not validate_department(department):
        print (Fore.RED + "Invalid department name.")
        return
    position = input("Enter Position: ").strip()
    if not validate_position(position):
        print (Fore.RED + "Invalid position.")
        return
    salary_raw = input("Enter Salary (integer): ").strip()
    ok, salary = parse_int(salary_raw)
    if not ok:
        print (Fore.RED + "Salary must be a non-negative integer (commas allowed).")
        print (Fore.RED + "Salary must be a non-negative integer (commas allowed).")
        return
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM Employees WHERE name=? AND department=?;", (name, department))
            if cur.fetchone():
                print (Fore.RED + Style.BRIGHT + f"\n⚠️ Employee '{name}' already exists in '{department}'.")
            else:
                cur.execute(
                    "INSERT INTO Employees (name, department, position, salary) VALUES (?, ?, ?, ?);",
                    (name, department, position, salary),
                )
                conn.commit()
                print (Fore.GREEN + f"\n✅ Employee '{name}' added successfully!")
            cur.close()
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Add Error] {exc}")


def view_all() -> None:
    print (Fore.CYAN + Style.BRIGHT + "\n=== View All Employees ===")
    try:
        results = execute_query(
            "SELECT id, name, department, position, salary FROM Employees;", fetch=True
        )
        if results:
            headers = ["ID", "Name", "Department", "Position", "Salary"]
            print (tabulate(results, headers=headers, tablefmt="grid"))
            return
        print (Fore.RED + "No records found.")
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[View Error] {exc}")


def filter_department() -> None:
    print (Fore.CYAN + Style.BRIGHT + "\n=== Search Employees By Department ===")
    dept = input("Enter Department, e.g. 'HR': ").strip()
    if not validate_department(dept):
        print (Fore.RED + "Invalid department input.")
                print (Fore.RED + Style.BRIGHT + f"\n⚠️ Employee '{name}' already exists in '{department}'.")
            else:
                cur.execute("INSERT INTO Employees (name, department, position, salary) VALUES (?, ?, ?, ?);", (name, department, position, salary))
                print (Fore.GREEN + f"\n✅ Employee '{name}' added successfully!")
                cur.close()
    except Exception as e:
        print (Fore.RED + f"[Add Error] {e}")


def view_all():
    print (Fore.CYAN + Style.BRIGHT + "\n=== View All Employees ===")
    try:
        results = execute_query("SELECT id, name, department, position, salary FROM Employees;", fetch=True)
        if results:
            headers = ["ID", "Name", "Department", "Position", "Salary"]
            print (tabulate(results, headers=headers, tablefmt="grid"))
        else:
            print (Fore.RED + "No records found.")
    except Exception as e:
        print (Fore.RED + f"[View Error] {e}")


def filter_department():
    print (Fore.CYAN + Style.BRIGHT + "\n=== Search Employees By Department ===")
    dept = input("Enter Department, e.g. 'HR': ").strip()
    if not validate_department(dept):
        print (Fore.RED + "Invalid department input.")
        return
    try:
        results = execute_query(
            "SELECT id, name, department, position, salary FROM Employees WHERE department=?;",
            (dept,),
            fetch=True,
        )
        if results:
            headers = ["ID", "Name", "Department", "Position", "Salary"]
            print (tabulate(results, headers=headers, tablefmt="grid"))
            return
        print (Fore.RED + "No Employees found in that department!")
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Filter Error] {exc}")


def count_by_department() -> None:
    print (Fore.CYAN + Style.BRIGHT + "\n=== Count Employees Per Department ===")
            print (tabulate(results, headers=headers, tablefmt="grid"))
        else:
            print (Fore.RED + "No Employees found in that department!")
    except Exception as e:
        print (Fore.RED + f"[Filter Error] {e}")


def count_by_department():
    print (Fore.CYAN + Style.BRIGHT + "\n=== Count Employees Per Department ===")
    try:
        results = execute_query("SELECT department, COUNT(*) FROM Employees GROUP BY department;", fetch=True)
        if results:
            headers = ["Department", "Employee Count"]
            print (tabulate(results, headers=headers, tablefmt="grid"))
            return
        print (Fore.RED + "No Employees found!")
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Count Error] {exc}")


def average_salary_per_department() -> None:
    print (Fore.CYAN + Style.BRIGHT + "\n=== Average Salary Per Department ===")
    try:
        results = execute_query(
            "SELECT department, ROUND(AVG(salary), 2) as avg_salary, COUNT(*) FROM Employees GROUP BY department;",
            fetch=True,
        )
        if results:
            headers = ["Department", "Average Salary", "Employee Count"]
            print (tabulate(results, headers=headers, tablefmt="grid"))
            return
        print (Fore.RED + "No data available.")
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Avg Salary Error] {exc}")


def filter_salary() -> None:
    print (Fore.CYAN + Style.BRIGHT + "\n=== Show Employees With Salary Over X ===")
    MIN_SALARY = input("Enter Salary (integer): ").strip()
    ok, min_salary = parse_int(MIN_SALARY)
    if not ok:
        print (Fore.RED + "Invalid salary input.")
            print (tabulate(results, headers=headers, tablefmt="grid"))
        else:
            print (Fore.RED + "No Employees found!")
    except Exception as e:
        print (Fore.RED + f"[Count Error] {e}")


def average_salary_per_department():
    print (Fore.CYAN + Style.BRIGHT + "\n=== Average Salary Per Department ===")
    try:
        results = execute_query("SELECT department, ROUND(AVG(salary), 2) as avg_salary, COUNT(*) FROM Employees GROUP BY department;", fetch=True,)
        if results:
            headers = ["Department", "Average Salary", "Employee Count"]
            print(tabulate(results, headers=headers, tablefmt="grid"))
        else:
            print (Fore.RED + "No data available.")
    except Exception as e:
        print (Fore.RED + f"[Avg Salary Error] {e}")


def filter_salary():
    print (Fore.CYAN + Style.BRIGHT + "\n=== Show Employees With Salary Over X ===")
    MIN_SALARY = input("Enter Salary (integer): ").strip()
    ok, min_salary = parse_int(MIN_SALARY)
    if not ok:
        print (Fore.RED + "Invalid salary input.")
        return
    try:
        results = execute_query(
            "SELECT id, name, department, position, salary FROM Employees WHERE salary >= ?;",
            (min_salary,),
            fetch=True,
        )
        if results:
            headers = ["ID", "Name", "Department", "Position", "Salary"]
            print (tabulate(results, headers=headers, tablefmt="grid"))
            return
        print (Fore.RED + "No Salary Matches!")
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Filter Salary Error] {exc}")


def sort_by() -> None:
    print(Fore.CYAN + Style.BRIGHT + "\n=== Sort Employees By Name or Salary ===")
    while True:
        print (Fore.YELLOW + "\nSort by: 1. Name  2. Salary  3. Back")
            print (tabulate(results, headers=headers, tablefmt="grid"))
        else:
            print (Fore.RED + "No Salary Matches!")
    except Exception as e:
        print (Fore.RED + f"[Filter Salary Error] {e}")


def sort_by():
    print (Fore.CYAN + Style.BRIGHT + "\n=== Sort Employees By Name or Salary ===")
    while True:
        print (Fore.YELLOW + "\nSort by: 1. Name  2. Salary  3. Back") 
        choice = input("Enter choice: ").strip()
        if choice == "1":
            sql = "SELECT id, name, department, position, salary FROM Employees ORDER BY name ASC;"
        elif choice == "2":
            sql = "SELECT id, name, department, position, salary FROM Employees ORDER BY salary DESC;"
        elif choice == "3":
            return
        else:
            print (Fore.RED + "Invalid choice.")
            continue
            print (Fore.RED + "Invalid choice.")
            continue
        try:
            results = execute_query(sql, fetch=True)
            if results:
                headers = ["ID", "Name", "Department", "Position", "Salary"]
                print (tabulate(results, headers=headers, tablefmt="grid"))
                return
            print (Fore.RED + "No records found.")
        except Exception as exc:  # pragma: no cover
            print (Fore.RED + f"[Sort Error] {exc}")


def update_employee() -> None:
    print (Fore.CYAN + Style.BRIGHT + "\n=== Update Employee ===")
        print (tabulate(results, headers=headers, tablefmt="grid"))
    else:
        print (Fore.RED + "No records found.")
    except Exception as e:
        print (Fore.RED + f"[Sort Error] {e}")


def update_employee():
    print (Fore.CYAN + Style.BRIGHT + "\n=== Update Employee ===")
    emp_id_raw = input("Enter Employee ID to update: ").strip()
    if not emp_id_raw.isdigit():
        print(Fore.RED + "Invalid ID.")
        return
    try:
        emp_id = int(emp_id_raw)
        results = execute_query(
            "SELECT id, name, department, position, salary FROM Employees WHERE id=?;",
            (emp_id,),
            fetch=True,
        )
        if not results:
            print (Fore.RED + "Employee not found.")
            return
        row = results[0]
        print (tabulate([row], headers=["ID", "Name", "Department", "Position", "Salary"], tablefmt="grid"))
        print ("Leave field empty to keep current value.")
            print (Fore.RED + "Employee not found.")
            return
        row = results[0]
        print (tabulate([row], headers=["ID", "Name", "Department", "Position", "Salary"], tablefmt="grid"))
        print ("Leave field empty to keep current value.")
        new_name = input("New name: ").strip()
        new_department = input("New department: ").strip()
        new_position = input("New position: ").strip()
        new_salary_raw = input("New salary: ").strip()

        # defaults to old values if empty
        name = new_name if new_name else row[1]
        department = new_department if new_department else row[2]
        position = new_position if new_position else row[3]
        if new_salary_raw:
            ok, salary = parse_int(new_salary_raw)
            if not ok:
                print (Fore.RED + "Invalid salary.")
                print (Fore.RED + "Invalid salary.")
                return
        else:
            salary = row[4]

        if not validate_name(name):
            print (Fore.RED + "Invalid name format.")
            return
        if not validate_department(department):
            print(Fore.RED + "Invalid department.")
            return
        if not validate_position(position):
            print (Fore.RED + "Invalid position.")
        # validate final values
        if not validate_name(name):
            print (Fore.RED + "Invalid name format.")
            return
        if not validate_department(department):
            print (Fore.RED + "Invalid department.")
            return
        if not validate_position(position):
            print (Fore.RED + "Invalid position.")
            return

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE Employees SET name=?, department=?, position=?, salary=? WHERE id=?;",
                (name, department, position, salary, emp_id),
            )
            conn.commit()
            cur.close()
        print (Fore.GREEN + "✅ Employee updated successfully.")
    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Update Error] {exc}")


def delete_employee() -> None:
    print (Fore.RED + "\n=== Delete An Employee From The Database ===")
    empt_id_raw = input("Enter Employee ID To Delete: ").strip()
    if not empt_id_raw.isdigit():
        print (Fore.RED + "Invalid ID.")
            cur.execute("UPDATE Employees SET name=?, department=?, position=?, salary=? WHERE id=?;",(name, department, position, salary, (..., emp_id)))
            conn.commit()
            cur.close()
        print (Fore.GREEN + "✅ Employee updated successfully.")
    except Exception as e:
        print (Fore.RED + f"[Update Error] {e}")


def delete_employee():
    print (Fore.RED + "\n=== Delete An Employee From The Database ===")
    empt_id_raw = input("Enter Employee ID To Delete: ").strip()
    if not empt_id_raw.isdigit():
        print (Fore.RED + "Invalid ID.")
        return
    empt_id = int(empt_id_raw)
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM Employees WHERE id=?;", (empt_id,))
            conn.commit()
            cur.close()
        print (Fore.GREEN + "✅ Employee deleted (if existed)!")
    except Exception as exc:  # pragma: no cover
        print(Fore.RED + f"[Delete Error] {exc}")


def export_employees() -> None:
    """
    Export employees to CSV. Options:
      1) All
    """
        print (Fore.GREEN + "✅ Employee deleted (if existed)!")
    except Exception as e:
        print (Fore.RED + f"[Delete Error] {e}")


# ---------------------------
# CSV Export
# ---------------------------
def export_employees():
    """
    Export employees to CSV. Supports:
      1) All employees
      2) By department
      3) Salary >= X
      4) Specific IDs (comma-separated)
b   """
    print (Fore.CYAN + Style.BRIGHT + "\n=== Export Employees To CSV ===")
    print (Fore.YELLOW + "Choose export type:\n 1) All\n 2) By department\n 3) Salary >= X\n 4) Specific IDs (comma-separated)\n 5) Back")
    print (Fore.CYAN + Style.BRIGHT + "\n=== Export Employees To CSV ===")
    print (Fore.YELLOW + "Choose export type:\n 1) All\n 2) By department\n 3) Salary >= X\n 4) Specific IDs (comma-separated)\n 5) Back")

    choice = input("Enter choice: ").strip()
    if choice == "5":
        return

    sql = "SELECT id, name, department, position, salary FROM Employees"
    params = ()

    if choice == "1":
        sql_final = sql + ";"
    elif choice == "2":
        dept = input("Enter department: ").strip()
        if not validate_department(dept):
            print(Fore.RED + "Invalid department.")
            print (Fore.RED + "Invalid department.")
            return
        sql_final = sql + " WHERE department=?;"
        params = (dept,)
    elif choice == "3":
        min_salary_raw = input("Enter minimum salary: ").strip()
        ok, min_salary = parse_int(min_salary_raw)
        if not ok:
            print(Fore.RED + "Invalid salary.")
            print (Fore.RED + "Invalid salary.")
            return
        sql_final = sql + " WHERE salary >= ?;"
        params = (min_salary,)
    elif choice == "4":
        ids_raw = input("Enter IDs (e.g. 1,3,5): ").strip()
        if not ids_raw:
            print(Fore.RED + "No IDs provided.")
            return
        ids_clean = [x.strip() for x in ids_raw.split(",") if x.strip().isdigit()]
        if not ids_clean:
            print(Fore.RED + "Invalid IDs.")
            print (Fore.RED + "No IDs provided.")
            return
        ids_clean = [x.strip() for x in ids_raw.split(",") if x.strip().isdigit()]
        if not ids_clean:
            print (Fore.RED + "Invalid IDs.")
            return
        placeholders = ",".join("?" for _ in ids_clean)
        sql_final = f"{sql} WHERE id IN ({placeholders});"
        params = tuple(int(x) for x in ids_clean)
    else:
        print(Fore.RED + "Invalid choice.")
        print (Fore.RED + "Invalid choice.")
        return

    try:
        results = execute_query(sql_final, params, fetch=True)
        if not results:
            print(Fore.RED + "No records found — nothing to export.")
            print (Fore.RED + "No records found — nothing to export.")
            return

        default_name = f"employees_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filename = input(f"Enter filename (default {default_name}): ").strip() or default_name
        path = Path(filename)

        if path.exists():
            overwrite = input("File exists. Overwrite? (y/N): ").strip().lower()
            if overwrite != "y":
                print(Fore.YELLOW + "Export cancelled.")
                return

        headers = ["ID", "Name", "Department", "Position", "Salary"]
                print (Fore.YELLOW + "Export cancelled.")
                return

        # WRITE CSV
        headers = ["ID", "Name", "Department", "Position", "Salary"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in results:
                writer.writerow(row)

        print (Fore.GREEN + f"✅ Exported {len(results)} rows to '{path.resolve()}'.")

    except Exception as exc:  # pragma: no cover
        print (Fore.RED + f"[Export Error] {exc}")
        print (Fore.GREEN + f"✅ Exported {len(results)} rows to '{path.resolve()}'.")

    except Exception as e:
        print (Fore.RED + f"[Export Error] {e}")


# ---------------------------
# CLI menu
# ---------------------------
def menu() -> None:
    while True:
        print (Fore.CYAN + Style.BRIGHT + "\n=== EMPLOYEE MANAGEMENT SYSTEM ===")
        print (Fore.YELLOW + "1. Add New Employee")
        print (Fore.YELLOW + "2. View All Employees")
        print (Fore.YELLOW + "3. Search Employees by Department")
        print (Fore.YELLOW + "4. Count Employees Per Department")
        print (Fore.YELLOW + "5. Show Employees With Salary Above")
        print (Fore.YELLOW + "6. Sort Employees By Name And Salary")
        print (Fore.YELLOW + "7. Update Employee")
        print (Fore.YELLOW + "8. Delete An Employee Record")
        print (Fore.YELLOW + "9. Average Salary Per Department")
        print (Fore.YELLOW + "10. Export Employees to CSV")
        print (Fore.RED + "11. Exit")
def menu():
    while True:
        print (Fore.CYAN + Style.BRIGHT + "\n=== EMPLOYEE MANAGEMENT SYSTEM ===")
        print (Fore.YELLOW + "1. Add New Employee")
        print (Fore.YELLOW + "2. View All Employees")
        print (Fore.YELLOW + "3. Search Employees by Department")
        print (Fore.YELLOW + "4. Count Employees Per Department")
        print (Fore.YELLOW + "5. Show Employees With Salary Above")
        print (Fore.YELLOW + "6. Sort Employees By Name And Salary")
        print (Fore.YELLOW + "7. Update Employee")
        print (Fore.YELLOW + "8. Delete An Employee Record")
        print (Fore.YELLOW + "9. Average Salary Per Department")
        print (Fore.YELLOW + "10. Export Employees to CSV")
        print (Fore.RED + "11. Exit")

        choice = input(Fore.MAGENTA + "Enter Choice: ").strip()

        if choice == "1":
            add_employee()
        elif choice == "2":
            view_all()
        elif choice == "3":
            filter_department()
        elif choice == "4":
            count_by_department()
        elif choice == "5":
            filter_salary()
        elif choice == "6":
            sort_by()
        elif choice == "7":
            update_employee()
        elif choice == "8":
            delete_employee()
        elif choice == "9":
            average_salary_per_department()
        elif choice == "10":
            export_employees()
        elif choice == "11":
            print(Fore.LIGHTBLUE_EX + "Exiting... Goodbye Admin!")
            break
        else:
            print(Fore.RED + "\n⚠️ Invalid Choice!")


# ---------------------------
# Entrypoint
# ---------------------------
def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="EmployeeFlow — Secure Employee Management (CLI)")
    parser.add_argument("--db", help="Path to DB file (overrides default)", default=None)
    parser.add_argument("--no-seed", action="store_true", help="Do not seed example data")
    parser.add_argument("--export", nargs="?", const="auto_export.csv", help="Run export and exit (optional filename)")
    args = parser.parse_args(argv)

    if args.db:
        set_db_file(args.db)

    init_db()
    if not args.no_seed:
        seed_default_data()
    remove_duplicates()

    if args.export:
        # run export non-interactively (exports all rows)
        results = execute_query("SELECT id, name, department, position, salary FROM Employees;", fetch=True)
        if results:
            filename = args.export or f"employees_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with Path(filename).open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Department", "Position", "Salary"])
                for row in results:
                    writer.writerow(row)
            print (Fore.GREEN + f"✅ Exported {len(results)} rows to '{Path(filename).resolve()}'.")
        else:
            print (Fore.RED + "No rows to export.")
        return

    if not admin_exists():
        print (Fore.YELLOW + "No admin account found. Please set one now.")
        set_admin_password_interactive()

    if not login():
        print (Fore.RED + "Exiting due to failed login.")
            print (Fore.LIGHTBLUE_EX + "Exiting... Goodbye Admin!")
            break
        else:
            print (Fore.RED + "\n⚠️ Invalid Choice!")


# ---------------------------
# Main
# ---------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Employee HR Management (CLI)")
    parser.add_argument("--db", help="Path to DB file (overrides default)", default=None)
    args = parser.parse_args(argv)
#always initialize db
    init_db()
    seed_default_data()
    remove_duplicates()
#And then override if --db provided
    if args.db:
        set_db_file(args.db)
        init_db()
        seed_default_data()
        remove_duplicates()

    if not admin_exists():
        print (Fore.YELLOW + "No admin account found. Please set one now.")
        set_admin_password_interactive()
        # try login
    if not login():
        print (Fore.RED + "Exiting due to failed login.")
        sys.exit(1)

    menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print ("\n" + Fore.YELLOW + "Interrupted by user. Exiting.")
        try:
            conn = get_connection()
            conn.close()
        except Exception:
            pass
        print ("\nCreated by Kali Noosi")
        print ("\n" + Fore.YELLOW + "Interrupted by user. Exiting.")
        try:
            get_connection().close()
            print ('\n"Created by Kali Noosi"')
        except Exception:
            pass
        sys.exit(0)
