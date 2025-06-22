%% KardiaFlow Phase-4 Medallion Architecture
%% paste this verbatim into README.md or a Databricks markdown cell

flowchart TD
  %% ───────── Raw Landing ─────────
  subgraph RAW["🟦 RAW Land Zone (CSV folders)"]
    direction TB
    RP["/incoming/patients/ \n(new CSV every ~15 s)"]
    RE["/incoming/encounters/ \n(new CSV every ~15 s)"]
  end

  %% ───────── Bronze ─────────
  subgraph BRZ["🟫 Bronze — Auto Loader Tables"]
    direction TB
    BP[bronze_patients]
    BE[bronze_encounters]
  end

  %% ───────── CDC / CDF views ─────────
  subgraph CDF["🪞 CDF Views (no storage)"]
    direction TB
    BPC[bronze_patients_changes\n(table_changes)]
    BEC[bronze_encounters_changes\n(table_changes)]
  end

  %% ───────── Silver ─────────
  subgraph SIL["🥈 Silver — Clean & Modeled"]
    direction TB
    SP[silver_patients]
    SE[silver_encounters]
    SPE[silver_patients_encounters\n(wide join)]
  end

  %% ───────── Gold ─────────
  subgraph GLD["🥇 Gold — BI Layer"]
    direction TB
    G1[vw_gender_breakdown\n(materialized)]
    G2[vw_encounters_by_month\n(materialized)]
    G3[vw_patient_load_stats\n(view)]
    G4[gold_patient_summary\n(final table)]
  end

  %% ───────── Edges / flow arrows ─────────
  RP -- "Auto Loader\ncloudFiles.format=csv" --> BP
  RE -- "Auto Loader\ncloudFiles.format=csv" --> BE

  BP -- "Delta CDF\n(table_changes)" --> BPC
  BE -- "Delta CDF\n(table_changes)" --> BEC

  BPC -- "MERGE INTO\n(dedup, mask)" --> SP
  BEC -- "MERGE INTO\n(clean)" --> SE

  SP -- "JOIN\npatient_id" --> SPE
  SE -- "JOIN\npatient_id" --> SPE

  SPE --> G1
  SPE --> G2
  SPE --> G3
  SPE --> G4
