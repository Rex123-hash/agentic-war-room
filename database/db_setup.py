import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "warroom.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assignee TEXT,
            status TEXT DEFAULT 'Open',
            priority TEXT DEFAULT 'Medium',
            deadline TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT,
            email TEXT,
            skills TEXT,
            available INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            content TEXT,
            date TEXT
        );

        CREATE TABLE IF NOT EXISTS action_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO tasks (title, assignee, status, priority, deadline, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("Frontend UI Crash", "Alice Smith", "Open", "Critical", "2026-04-04", "App crashes on profile screen"),
                ("API timeout fix", "Bob Johnson", "In Progress", "High", "2026-04-05", "Requests timing out intermittently"),
                ("Write unit tests", "Carol White", "Open", "Medium", "2026-04-07", "Coverage is below target"),
                ("Deploy to staging", "Bob Johnson", "Blocked", "High", "2026-04-04", "Blocked pending bug resolution"),
            ],
        )

        cursor.executemany(
            """
            INSERT INTO team_members (name, role, email, skills, available)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("Alice Smith", "Lead Developer", "alice@company.com", "frontend,react,typescript", 0),
                ("Bob Johnson", "Senior Developer", "bob@company.com", "frontend,python,debugging", 1),
                ("Carol White", "Developer", "carol@company.com", "frontend,css,testing", 1),
                ("David Green", "Junior Developer", "david@company.com", "html,javascript", 1),
            ],
        )

        cursor.executemany(
            """
            INSERT INTO knowledge_base (type, title, content, date)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("sop", "Critical Bug Protocol", "When a critical bug is open and the assignee is unavailable: reassign to an available senior developer, notify the engineering-critical channel, and schedule an emergency huddle.", "2026-01-15"),
                ("sop", "Developer Absence Protocol", "When a lead developer is sick: notify team lead, reassign all critical tasks, and review status in standup.", "2026-02-01"),
                ("meeting_note", "Sprint 23 Planning", "Bug #42 was marked highest priority. Bob Johnson is backup for critical frontend issues.", "2026-03-28"),
                ("decision", "Frontend Architecture Decision", "React 18 with TypeScript. Critical frontend bugs require senior developer review before closure.", "2026-03-20"),
            ],
        )

    conn.commit()
    conn.close()
    print("Database setup complete.")


if __name__ == "__main__":
    setup_database()