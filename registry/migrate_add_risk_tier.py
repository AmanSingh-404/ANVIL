from registry.db import get_connection

def migrate():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE tools ADD COLUMN risk_tier TEXT NOT NULL DEFAULT 'side_effecting'")
        conn.commit()
        print("Migration applied: added risk_tier column (default 'side_effecting' — safe default).")
    except Exception as e:
        print(f"Migration skipped or failed (may already be applied): {e}")
    conn.close()

if __name__ == "__main__":
    migrate()