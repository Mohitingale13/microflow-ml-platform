import os
from sqlalchemy import create_engine, text

def fix_db():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("No DATABASE_URL found, skipping fixes.")
        return
        
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    print(f"Connecting to database to apply schema fixes...")
    engine = create_engine(db_url)
    
    with engine.begin() as conn:
        # 1. RAGAS columns
        try:
            conn.execute(text("ALTER TABLE ai_query_caches ADD COLUMN IF NOT EXISTS context_relevance_score FLOAT;"))
            conn.execute(text("ALTER TABLE ai_query_caches ADD COLUMN IF NOT EXISTS faithfulness_score FLOAT;"))
            conn.execute(text("ALTER TABLE ai_query_caches ADD COLUMN IF NOT EXISTS answer_relevance_score FLOAT;"))
            conn.execute(text("ALTER TABLE ai_query_caches ADD COLUMN IF NOT EXISTS evaluation_reasoning TEXT;"))
            print("RAGAS columns verified.")
        except Exception as e:
            print(f"Error adding RAGAS columns: {e}")
            
        # 2. SHAP columns
        try:
            conn.execute(text("ALTER TABLE run_results ADD COLUMN IF NOT EXISTS explainability_status VARCHAR(50);"))
            conn.execute(text("ALTER TABLE run_results ADD COLUMN IF NOT EXISTS explainability_error TEXT;"))
            conn.execute(text("ALTER TABLE run_results ADD COLUMN IF NOT EXISTS explainability_summary JSON;"))
            print("SHAP columns verified.")
        except Exception as e:
            print(f"Error adding SHAP columns: {e}")

        # 3. Stamp Alembic so it doesn't crash on previously created tables
        try:
            conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY);"))
            result = conn.execute(text("SELECT version_num FROM alembic_version;"))
            versions = [row[0] for row in result]
            buggy_versions = ["c3d4e5f6a7b8", "d4e5f6a7b8c9", "e5f6a7b8c9d0", "f6a7b8c9d0e1", "96c25a0c4cd8", "a299078d4c6a", "b0107acce356", "g7h8i9j0k1l2"]
            
            if len(versions) == 0 or any(v in versions for v in buggy_versions):
                conn.execute(text("DELETE FROM alembic_version;"))
                conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0bc48e7b232a');"))
                print(f"Alembic history upgraded from {versions} to latest (0bc48e7b232a).")
            else:
                print(f"Alembic history is {versions}. Skipping stamp.")
        except Exception as e:
            print(f"Error stamping Alembic: {e}")

    print("Database fixes complete!")

if __name__ == "__main__":
    fix_db()
