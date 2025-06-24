---
config:
  theme: neutral
  look: neo
  layout: fixed
---
flowchart LR
 subgraph RAW["🟦 RAW – Landing"]
    direction TB
        P["/patients/"]
        E["/encounters/"]
        C["/claims/"]
        PR["/providers/"]
        FDBK["/feedback/"]
        DEV["/device/"]
  end
 subgraph BRZ["🟫 Bronze – Auto Loader (Streaming)"]
    direction TB
        BP["bronze_patients"]
        BE["bronze_encounters"]
        BC["bronze_claims"]
  end
 subgraph SIL["🥈 Silver – Clean & Modeled"]
    direction TB
        SP["silver_patients"]
        SE["silver_encounters"]
        SC["silver_claims_current"]
        SProv["silver_providers_dim"]
        SFB["silver_feedback"]
        SDHR["silver_device_5m_hr"]
        WIDE_PE["silver_patient_encounter"]
        WIDE_PEC["silver_claims_enriched"]
  end
 subgraph GLD["🥇 Gold – BI / KPI"]
    direction TB
        G1["vw_gender_breakdown"]
        G2["vw_encounters_by_month"]
        G3["gold_claims_kpi_hour"]
        G5["gold_patient_sentiment_daily"]
        G6["gold_hr_alerts"]
  end
    P -- Auto Loader --> BP
    E -- Auto Loader --> BE
    C -- Auto Loader --> BC
    PR -- Nightly COPY INTO --> SProv
    FDBK -- Batch JSON --> SFB
    DEV -- Hourly Parquet --> SDHR
    BP -- CDF --> SP
    BE -- CDF --> SE
    BC -- "SCD-1" --> SC
    SP -. PK .-> WIDE_PE
    SE -. FK .-> WIDE_PE
    SC -- join ProviderID --> WIDE_PEC
    SProv -- join ProviderID --> WIDE_PEC
    WIDE_PE --> G1 & G2
    WIDE_PEC --> G3
    SFB --> G5
    SDHR -- agg 5 min --> G6
