## Databricks Data + AI Summit 2025: Reflections

In June 2025, I attended the Databricks Data + AI Summit in San Francisco, where I completed **24 hours of intensive, hands-on training** across six in-depth labs.

---

### Lakeflow Connect  

The summit began with the **Lakeflow Connect** workshop, which focused on data ingestion strategies.  

A key takeaway was mastering **Auto Loader** for incremental ingestion from CSV, Avro, and Parquet. This directly influenced Kardiaflow’s Bronze layer design, enabling ingestion of evolving healthcare datasets with schema evolution and auditing via `_ingest_ts` and `_source_file` columns.

---

### Lakeflow Declarative Pipelines  

In the **Lakeflow Declarative Pipelines** session, I learned how to orchestrate automated ETL workflows. Although I chose not to implement Declarative Pipelines or DLT-specific syntax, the concepts of automated incremental batch and streaming updates guided my use of PySpark and Delta Lake.  

It reinforced the importance of explicit schema definitions in Kardiaflow’s Silver transformations, supporting reliable Change Data Feed-based updates and merges.

---

### Streaming and Lakeflow Pipelines Lab  

The **Databricks Streaming and Lakeflow Pipelines** lab deepened my understanding of Spark Structured Streaming and Auto Loader, especially around state management and stream-static joins. I applied this in Kardiaflow by using `availableNow=True` for bounded batch demos and `trigger(processingTime="30 seconds")` for continuous streaming.

---

### Unity Catalog  

The **Unity Catalog** session reshaped my thinking about data governance in Kardiaflow. Training on fine-grained access controls, external storage integrations, and lineage tracking highlighted the need for strict security.  

While I didn’t implement Unity Catalog directly, I applied its principles by enforcing **PHI masking and nullification** in the Silver layer.

---

### Data Warehousing Lab  

The **Data Warehousing** lab, led by Luca Gennari, improved my ability to deliver analytics. Learning advanced dashboard techniques with Databricks SQL and approaches to visualizing KPIs directly enhanced Kardiaflow’s Gold layer.  

As a result, Kardiaflow now includes clear patient lifecycle metrics and dashboards that are practical for healthcare decision-making.

---

### Lakeflow Jobs  

The **Lakeflow Jobs** session introduced orchestration techniques such as conditional task execution, checkpointing, and error handling.  

I integrated these into Kardiaflow by using job parameters for the Encounters pipeline, making it simple to switch between streaming and batch ingestion.

---

### Certifications  

I earned the **Databricks Associate Data Engineer** certification during the summit and later passed the **Databricks Professional Data Engineer** exam with a 91% score, reinforcing my understanding of Lakehouse fundamentals.

---

Attending the summit helped me shape Kardiaflow’s design, from ingestion to governance and analytics. The 
mix of labs, real-world techniques, and certification milestones made the experience not only valuable for learning but immediately useful in practice.
