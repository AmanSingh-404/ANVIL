from registry.db import get_connection

def migrate():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE tools ADD COLUMN approval_count INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("Added approval_count column.")
    except Exception as e:
        print(f"approval_count migration skipped/failed: {e}")

    try:
        cursor.execute("ALTER TABLE tools ADD COLUMN auto_approved INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("Added auto_approved column.")
    except Exception as e:
        print(f"auto_approved migration skipped/failed: {e}")

    conn.close()

if __name__ == "__main__":
    migrate()