import argparse
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

def main(argv=None):
    parser = argparse.ArgumentParser(description="Randomly split a metadata CSV.")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    ratios = (args.train_ratio, args.val_ratio, args.test_ratio)
    if any(not 0 < ratio < 1 for ratio in ratios):
        parser.error("each split ratio must be between 0 and 1")
    if abs(sum(ratios) - 1.0) > 1e-6:
        parser.error("split ratios must sum to 1")
    if not args.metadata.is_file():
        parser.error(f"metadata file does not exist: {args.metadata}")

    df = pd.read_csv(args.metadata)
    print(f"📄 Total samples: {len(df)}")

    # --- 第一次划分：train vs (val+test) ---
    train_df, temp_df = train_test_split(
        df,
        test_size=(1 - args.train_ratio),
        random_state=args.seed,
        shuffle=True,
    )

    # --- 第二次划分：val vs test ---
    val_size = args.val_ratio / (args.val_ratio + args.test_ratio)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1 - val_size),
        random_state=args.seed,
        shuffle=True,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    train_df.to_csv(args.output_dir / "metadata_train.csv", index=False)
    val_df.to_csv(args.output_dir / "metadata_val.csv", index=False)
    test_df.to_csv(args.output_dir / "metadata_test.csv", index=False)

    print("✅ Split finished:")
    print(f"   Train: {len(train_df)}")
    print(f"   Val:   {len(val_df)}")
    print(f"   Test:  {len(test_df)}")

if __name__ == "__main__":
    main()
