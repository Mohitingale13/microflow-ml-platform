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
            result = conn.execute(text("SELECT COUNT(*) FROM alembic_version;"))
            count = result.scalar()
            if count == 0:
                conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0bc48e7b232a');"))
                print("Alembic history stamped to latest (0bc48e7b232a).")
            else:
                print("Alembic history already stamped. Skipping.")
        except Exception as e:
            print(f"Error stamping Alembic: {e}")

    print("Database fixes complete!")

if __name__ == "__main__":
    fix_db()
