# WHO Child Growth Standards — data provenance

All L/M/S values in `apps/who_standards/data/*.csv` are copied verbatim
(no recomputation, no manual edits) from the official WHO Child Growth
Standards `.xlsx` files below, downloaded on **2026-08-07** via
`apps/who_standards/data/_convert_raw.py` from the raw files in
`apps/who_standards/data/raw/`.

Row counts are for the **final normalized CSV**, after merging the 0-2y /
2-5y split files for age-indexed indicators (see "Boundary handling" note
below the table).

| Output CSV | Source raw file(s) | Source URL | Download date | Rows |
|---|---|---|---|---|
| `lhfa_boys.csv` | `lhfa_boys_0-2y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/length-height-for-age/lhfa_boys_0-to-2-years_zscores.xlsx?sfvrsn=30e044c_9 | 2026-08-07 | 61 |
| | `lhfa_boys_2-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/length-height-for-age/lhfa_boys_2-to-5-years_zscores.xlsx?sfvrsn=17e5ad91_9 | 2026-08-07 | |
| `lhfa_girls.csv` | `lhfa_girls_0-2y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/length-height-for-age/lhfa_girls_0-to-2-years_zscores.xlsx?sfvrsn=e9e66a95_11 | 2026-08-07 | 61 |
| | `lhfa_girls_2-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/length-height-for-age/lhfa_girls_2-to-5-years_zscores.xlsx?sfvrsn=2ec187b9_11 | 2026-08-07 | |
| `wfa_boys.csv` | `wfa_boys_0-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-age/wfa_boys_0-to-5-years_zscores.xlsx?sfvrsn=97a05331_9 | 2026-08-07 | 61 |
| `wfa_girls.csv` | `wfa_girls_0-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-age/wfa_girls_0-to-5-years_zscores.xlsx?sfvrsn=4c03b8db_7 | 2026-08-07 | 61 |
| `bfa_boys.csv` | `bmi_boys_0-2y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/body-mass-index-for-age/bmi_boys_0-to-2-years_zcores.xlsx?sfvrsn=df725cc9_7 | 2026-08-07 | 61 |
| | `bmi_boys_2-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/body-mass-index-for-age/bmi_boys_2-to-5-years_zscores.xlsx?sfvrsn=73010c9b_5 | 2026-08-07 | |
| `bfa_girls.csv` | `bmi_girls_0-2y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/body-mass-index-for-age/bmi_girls_0-to-2-years_zscores.xlsx?sfvrsn=2be9859c_7 | 2026-08-07 | 61 |
| | `bmi_girls_2-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/body-mass-index-for-age/bmi_girls_2-to-5-years_zscores.xlsx?sfvrsn=452aca36_7 | 2026-08-07 | |
| `hcfa_boys.csv` | `hcfa_boys_0-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/head-circumference-for-age/hcfa-boys-0-5-zscores.xlsx?sfvrsn=adf57aa4_8 | 2026-08-07 | 61 |
| `hcfa_girls.csv` | `hcfa_girls_0-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/head-circumference-for-age/hcfa-girls-0-5-zscores.xlsx?sfvrsn=8f959f88_6 | 2026-08-07 | 61 |
| `acfa_boys.csv` | `acfa-boys-3-5-zscores.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/arm-circumference-for-age/acfa-boys-3-5-zscores.xlsx?sfvrsn=13c24647_8 | 2026-08-07 | 58 |
| `acfa_girls.csv` | `acfa-girls-3-5-zscores.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/arm-circumference-for-age/acfa-girls-3-5-zscores.xlsx?sfvrsn=df311d8b_13 | 2026-08-07 | 58 |
| `wfl_boys_0_2y.csv` | `wfl_boys_0-2y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-length-height/wfl_boys_0-to-2-years_zscores.xlsx?sfvrsn=e27a9da3_7 | 2026-08-07 | 131 |
| `wfh_boys_2_5y.csv` | `wfh_boys_2-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-length-height/wfh_boys_2-to-5-years_zscores.xlsx?sfvrsn=202c0545_7 | 2026-08-07 | 111 |
| `wfl_girls_0_2y.csv` | `wfl_girls_0-2y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-length-height/wfl_girls_0-to-2-years_zscores.xlsx?sfvrsn=288bc4e4_7 | 2026-08-07 | 131 |
| `wfh_girls_2_5y.csv` | `wfh_girls_2-5y.xlsx` | https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-length-height/wfh_girls_2-to-5-years_zscores.xlsx?sfvrsn=4d66af6a_7 | 2026-08-07 | 111 |

**Total: 18 raw WHO source files → 14 normalized CSVs.**

## Format notes confirmed by direct inspection

- Age-indexed raw files (`lhfa`, `wfa`, `bfa`, `hcfa`, `acfa`) use integer
  `Month` values, one row per whole month.
- Length/height-indexed raw files (`wfl`, `wfh`) use `Length`/`Height` in
  **0.5 cm increments** (confirmed by inspection — not assumed): `wfl` runs
  45.0–110.0 cm, `wfh` runs 65.0–120.0 cm.
- `acfa-*-3-5-zscores.xlsx`: despite the "3-5" in the filename (which
  suggested years), the `Month` column actually runs **3 to 60 (months)**,
  confirmed by direct inspection of the sheet — consistent with WHO's
  documented arm-circumference-for-age standard, which covers ages 3–60
  months. The "3-5" in the filename refers to (a truncated/ambiguous)
  "3 months to 5 years", not "3 to 5 years" starting at birth.
- One raw source file (`lhfa_boys_2-5y.xlsx`, `lhfa_girls_2-5y.xlsx`) has a
  column literally named `"M       "` (trailing whitespace) instead of
  `"M"`. The conversion script strips whitespace from all column names
  before selecting columns, so this is handled, but it's noted here in case
  future re-downloads of WHO files need the same defensive handling.

## Boundary handling (0-2y / 2-5y split files → single 0-60mo CSV)

For `lhfa_*` and `bfa_*`, WHO publishes two separate files per sex: one for
0-2 years and one for 2-5 years, both of which include a row for month 24.
Both rows were inspected directly:

```
lhfa_boys_0-2y.xlsx  month 24: L=1, M=87.8161, S=0.03479
lhfa_boys_2-5y.xlsx  month 24: L=1, M=87.1161, S=0.03507   (diff in M = 0.7000 exactly)

bmi_boys_0-2y.xlsx   month 24: L=-0.6473, M=15.7356, S=0.07771
bmi_boys_2-5y.xlsx   month 24: L=-0.6187, M=16.0189, S=0.07785
```

The `M` values differ by **exactly the WHO-documented 0.7cm** recumbent
length vs. standing height offset — this is expected, not a data error:
WHO's 0-2y tables are constructed from recumbent **length**, and its 2-5y
tables from standing **height** (standing height measures ~0.7cm shorter
than recumbent length for the same child). `L` and `S` at the boundary
were checked to be close (well within `MAX_L_DIFF=0.10` / `MAX_S_DIFF=0.01`
tolerances in `_convert_raw.py`); a bigger mismatch there would have meant
a bad download, not the expected modeling offset, and the script would
have raised instead of silently proceeding.

**Resolution:** per WHO's own measurement convention (children ≥24 months
are measured standing), the merged CSV keeps the **2-5y (standing-height)
row at month 24** and drops the 0-2y file's duplicate month-24 row. This
means `lhfa_boys.csv` / `bfa_boys.csv` (etc.) are internally consistent:
every row for `edad_meses < 24` is recumbent-length-based, every row for
`edad_meses >= 24` (including 24 itself) is standing-height-based. Callers
in `indicators.py` must apply the WHO 0.7cm correction to the child's own
measured value the same way (see the comment in `indicators.py::peso_para_talla`
and the equivalent handling needed for `talla_para_edad`).

## Conversion script

`apps/who_standards/data/_convert_raw.py` performs the raw → CSV
conversion described above and is kept in the repo (not deleted after use)
so the CSVs are reproducible/auditable from the raw files at any time.
