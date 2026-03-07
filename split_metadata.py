import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# ========= 配置 =========
METADATA_PATH = "juliet/metadata.csv"
OUT_DIR = Path("juliet/metadata")

TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1

RANDOM_SEED = 42
# =======================

assert abs(TRAIN_RATIO + VAL_RATIO + TEST_RATIO - 1.0) < 1e-6

def main():
    df = pd.read_csv(METADATA_PATH)
    print(f"📄 Total samples: {len(df)}")

    # --- 第一次划分：train vs (val+test) ---
    train_df, temp_df = train_test_split(
        df,
        test_size=(1 - TRAIN_RATIO),
        random_state=RANDOM_SEED,
        shuffle=True,
    )

    # --- 第二次划分：val vs test ---
    val_size = VAL_RATIO / (VAL_RATIO + TEST_RATIO)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1 - val_size),
        random_state=RANDOM_SEED,
        shuffle=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    train_df.to_csv(OUT_DIR / "metadata_train.csv", index=False)
    val_df.to_csv(OUT_DIR / "metadata_val.csv", index=False)
    test_df.to_csv(OUT_DIR / "metadata_test.csv", index=False)

    print("✅ Split finished:")
    print(f"   Train: {len(train_df)}")
    print(f"   Val:   {len(val_df)}")
    print(f"   Test:  {len(test_df)}")

if __name__ == "__main__":
    main()
