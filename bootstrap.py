"""
One-shot setup script: generates data, cleans it, runs EDA, trains the ML models,
and seeds the database. Run this once before starting the API server.

    python bootstrap.py
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable


def run_step(description, module):
    print(f"\n{'=' * 70}\n{description}\n{'=' * 70}")
    result = subprocess.run([PYTHON, "-m", module], cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"\nStep failed: {module}")
        sys.exit(result.returncode)


def main():
    run_step("Step 1/6: Generating synthetic datasets", "data.generate_data")
    run_step("Step 2/6: Cleaning datasets", "ml.data_cleaning")
    run_step("Step 3/6: Running exploratory data analysis", "ml.eda")
    run_step("Step 4/6: Training purchase prediction models (LR / DT / RF)", "ml.train_purchase_model")
    run_step("Step 5/6: Training customer segmentation model (K-Means)", "ml.train_segmentation")
    run_step("Step 6/6: Seeding the database", "db.seed_db")

    print("\n" + "=" * 70)
    print("Setup complete! Start the API with:")
    print("  uvicorn app.main:app --reload")
    print("Then open http://127.0.0.1:8000 in your browser.")
    print("=" * 70)


if __name__ == "__main__":
    main()
