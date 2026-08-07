"""
One-off conversion script: WHO raw .xlsx source files -> normalized CSVs.

Run once (or re-run for audit/reproducibility) with:
    source .venv/bin/activate
    python apps/who_standards/data/_convert_raw.py

Reads every raw WHO Child Growth Standards workbook in
apps/who_standards/data/raw/ and writes clean, minimal CSVs into
apps/who_standards/data/ with schema:
    - age-indexed indicators:   edad_meses,L,M,S   (one row per whole month)
    - length/height-indexed:    longitud_talla_cm,L,M,S  (0.5 cm increments)

All values are copied verbatim from the WHO source files (no values are
invented or altered) -- see PROVENANCE.md for the exact source URL of every
raw file consumed here.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).parent / "raw"
OUT_DIR = Path(__file__).parent

# Tolerance for boundary-row L/M/S agreement between the 0-2y and 2-5y source
# files at month 24 (see note below on the recumbent-length vs standing-height
# WHO modeling convention -- a ~0.7cm systematic difference in M is EXPECTED
# and is not a data error).
MAX_L_DIFF = 0.10
MAX_S_DIFF = 0.01


def _read_age_table(path: Path) -> pd.DataFrame:
    """Read an age-indexed (Month, L, M, S, ...) raw WHO xlsx into a
    normalized edad_meses,L,M,S DataFrame. Strips whitespace from column
    names (some WHO files, e.g. lhfa_boys_2-5y, ship a column literally
    named 'M       ' with trailing spaces)."""
    df = pd.read_excel(path, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[["Month", "L", "M", "S"]].rename(columns={"Month": "edad_meses"})
    df["edad_meses"] = df["edad_meses"].astype(int)
    return df.sort_values("edad_meses").reset_index(drop=True)


def _read_length_table(path: Path, col_name: str) -> pd.DataFrame:
    """Read a length/height-indexed raw WHO xlsx into a normalized
    longitud_talla_cm,L,M,S DataFrame."""
    df = pd.read_excel(path, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[[col_name, "L", "M", "S"]].rename(columns={col_name: "longitud_talla_cm"})
    df["longitud_talla_cm"] = df["longitud_talla_cm"].astype(float)
    return df.sort_values("longitud_talla_cm").reset_index(drop=True)


def _merge_age_split(df_low: pd.DataFrame, df_high: pd.DataFrame, label: str) -> pd.DataFrame:
    """Concatenate a 0-2y and a 2-5y age-indexed table into a single 0-60
    month table, resolving the overlapping boundary row (month 24).

    WHO builds the 0-2y tables from recumbent LENGTH and the 2-5y tables
    from standing HEIGHT (standing height runs ~0.7cm shorter than recumbent
    length for the same child -- this is the well documented WHO 0.7cm
    correction, not a data error). At month 24 both source files therefore
    publish a row, and their M values legitimately differ by roughly 0.7cm
    (or, for BMI, by whatever that implies for kg/m^2). Per WHO's own
    measurement convention, children >=24 months are measured standing, so
    we keep the 2-5y (standing-height-based) row at the exact boundary
    month and drop the 0-2y file's duplicate month-24 row.

    We still assert the two rows are in the same ballpark (loose tolerance)
    as a sanity check that we spliced the right files together -- a large
    discrepancy would indicate a wrong/corrupt download, not the expected
    modeling offset.
    """
    boundary = 24
    low_row = df_low[df_low["edad_meses"] == boundary]
    high_row = df_high[df_high["edad_meses"] == boundary]
    if not low_row.empty and not high_row.empty:
        l_diff = abs(float(low_row["L"].iloc[0]) - float(high_row["L"].iloc[0]))
        s_diff = abs(float(low_row["S"].iloc[0]) - float(high_row["S"].iloc[0]))
        # M is expected to differ systematically (~0.7cm recumbent-vs-standing
        # convention) so we do NOT gate on M; L and S should still be close.
        if l_diff > MAX_L_DIFF or s_diff > MAX_S_DIFF:
            raise ValueError(
                f"{label}: boundary month {boundary} L/S mismatch too large "
                f"(L diff={l_diff}, S diff={s_diff}) -- check source files, "
                f"this looks like more than the expected recumbent/standing "
                f"modeling offset."
            )
    merged = pd.concat(
        [df_low[df_low["edad_meses"] < boundary], df_high], ignore_index=True
    )
    return merged.sort_values("edad_meses").reset_index(drop=True)


def convert_age_indexed_single(name: str, raw_filename: str) -> int:
    df = _read_age_table(RAW_DIR / raw_filename)
    df.to_csv(OUT_DIR / f"{name}.csv", index=False)
    return len(df)


def convert_age_indexed_split(name: str, raw_low: str, raw_high: str) -> int:
    df_low = _read_age_table(RAW_DIR / raw_low)
    df_high = _read_age_table(RAW_DIR / raw_high)
    merged = _merge_age_split(df_low, df_high, name)
    merged.to_csv(OUT_DIR / f"{name}.csv", index=False)
    return len(merged)


def convert_length_indexed(name: str, raw_filename: str, col_name: str) -> int:
    df = _read_length_table(RAW_DIR / raw_filename, col_name)
    df.to_csv(OUT_DIR / f"{name}.csv", index=False)
    return len(df)


def main() -> None:
    counts: dict[str, int] = {}

    # --- Length/height-for-age (edad_meses,L,M,S), split files merged ---
    counts["lhfa_boys"] = convert_age_indexed_split(
        "lhfa_boys", "lhfa_boys_0-2y.xlsx", "lhfa_boys_2-5y.xlsx"
    )
    counts["lhfa_girls"] = convert_age_indexed_split(
        "lhfa_girls", "lhfa_girls_0-2y.xlsx", "lhfa_girls_2-5y.xlsx"
    )

    # --- Weight-for-age (single 0-5y file per sex) ---
    counts["wfa_boys"] = convert_age_indexed_single("wfa_boys", "wfa_boys_0-5y.xlsx")
    counts["wfa_girls"] = convert_age_indexed_single("wfa_girls", "wfa_girls_0-5y.xlsx")

    # --- BMI-for-age (split files merged) ---
    counts["bfa_boys"] = convert_age_indexed_split(
        "bfa_boys", "bmi_boys_0-2y.xlsx", "bmi_boys_2-5y.xlsx"
    )
    counts["bfa_girls"] = convert_age_indexed_split(
        "bfa_girls", "bmi_girls_0-2y.xlsx", "bmi_girls_2-5y.xlsx"
    )

    # --- Head-circumference-for-age (single 0-5y file per sex) ---
    counts["hcfa_boys"] = convert_age_indexed_single("hcfa_boys", "hcfa_boys_0-5y.xlsx")
    counts["hcfa_girls"] = convert_age_indexed_single("hcfa_girls", "hcfa_girls_0-5y.xlsx")

    # --- Arm-circumference-for-age / MUAC (single file per sex, 3-60mo) ---
    counts["acfa_boys"] = convert_age_indexed_single("acfa_boys", "acfa_boys.xlsx")
    counts["acfa_girls"] = convert_age_indexed_single("acfa_girls", "acfa_girls.xlsx")

    # --- Weight-for-length (0-2y, recumbent) / weight-for-height (2-5y, standing) ---
    # Kept as FOUR separate csvs (not merged) -- which one applies is a
    # runtime decision based on measurement type, not table coverage.
    counts["wfl_boys_0_2y"] = convert_length_indexed(
        "wfl_boys_0_2y", "wfl_boys_0-2y.xlsx", "Length"
    )
    counts["wfh_boys_2_5y"] = convert_length_indexed(
        "wfh_boys_2_5y", "wfh_boys_2-5y.xlsx", "Height"
    )
    counts["wfl_girls_0_2y"] = convert_length_indexed(
        "wfl_girls_0_2y", "wfl_girls_0-2y.xlsx", "Length"
    )
    counts["wfh_girls_2_5y"] = convert_length_indexed(
        "wfh_girls_2_5y", "wfh_girls_2-5y.xlsx", "Height"
    )

    print("Wrote CSVs:")
    for k, v in counts.items():
        print(f"  {k}.csv: {v} rows")


if __name__ == "__main__":
    main()
