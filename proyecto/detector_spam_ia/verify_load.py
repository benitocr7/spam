
import pandas as pd
try:
    df = pd.read_csv(
        "spam.csv",
        sep=";",
        header=None,
        names=["label", "mensaje"],
        engine="python",
        on_bad_lines="skip"
    )
    print("--- Loaded Data Head ---")
    print(df.head())
    print("--- Loaded Data Shape ---")
    print(df.shape)
    print("--- Unique Labels ---")
    print(df["label"].unique())
except Exception as e:
    print(f"Error: {e}")
