# Task2_Students-edu-Analytics-
An enterprise-grade, end-to-end data analytics and student performance monitoring system built for the **Kayfa Ed-Tech Platform**. This interactive dashboard processes data from **8 disparate file formats** (including Live JSON normalization, multi-sheet Excel parsing, and multiple relational CSVs) to deliver actionable insights, predict student churn, and automate institutional decision-making.

---

## 🚀 Key Features & Architectural Highlights

* **Advanced Student Risk Scoring (Early Intervention System):** Implementation of a hybrid weighting algorithm combining **Absence Rates (35%)**, **Conceptual Failures (35%)**, and **Platform Under-Engagement (30%)** to catch at-risk students before final assessments.
* **Euclidean Machine Learning Recommendation:** A data-driven approach using Euclidean distance matrices over conceptual performance profiles to suggest optimal peer-group merging strategies for under-sized student cohorts.
* **Live Data Ingestion & ETL Pipeline:** Dynamic cleaning, outlier rejection (e.g., negative grade fixes, age bound constraints), and automatic live joining across 6 core data dimensions.
* **Beautiful UI/UX Layout:** Tailored modern dark-themed executive interface utilizing Streamlit custom CSS injections and responsive full-width Plotly charts.

---

## 📈 Dashboard Structure & Analytical Coverage

The executive analytics suite is structurally segmented into **5 Specialized Hubs** containing **15 Interactive Charts**:

### 1. Demographics & Core Performance
* **Attendance Disparity:** Cross-group attendance rates vs. the overall platform baseline benchmark.
* **Volatility & Grade Spread:** Comprehensive Box and Violin plots tracking score dispersion across course disciplines and assessment variants.
* **Statistical Correlation:** Quantitative correlation analysis (Pearson $r$) proving the direct mathematical impact of attendance frequency on absolute final academic grades.

### 2. Behavioral Patterns & Device Analytics
* **Submission Velocity:** Multi-line week-over-week tracking of assignment submissions to trace behavioral trends.
* **Mid-Course Slump Testing:** Time-series analysis of platform login events to detect and flag the exact weeks where student motivation drops.
* **UI/UX Device Auditing:** Stratified performance evaluation across different hardware types (Mobile vs. Desktop) to isolate potential platform bugs.

### 3. Lateness Impact & Conceptual Bottlenecks
* **Pacing vs. Attempts:** Scatter distribution tracking if multiple submission attempts are caused by true content complexity or student procrastination.
* **Conceptual Red-Zones:** Ranking of specific academic concepts from hardest to easiest to immediately flag curriculum parts needing instructional support.

### 4. Cohort Discrepancy & Strategic Segmentation
* **Data Integrity Auditing:** Discrepancy charts mapping stated group sizes (metadata) against actual student counts to catch systemic database synchronization leaks.
* **Strategic Profiling (Pie Matrix):** Dynamic slicing of the student population into operational cohorts: *High-Achievers 🌟*, *Struggling Despite Effort 🔄*, *Disengaged At-Risk 🚨*, and *Under-Performers ⚠️*.

---

## 🛠️ Tech Stack & Dependencies

* **Core Logic & Engine:** Python 3.10+
* **Web Framework & UI:** Streamlit (Custom Custom CSS Injection)
* **Data Manipulation & ETL:** Pandas, NumPy, JSON, OpenPyXL
* **Advanced Interactive Graphics:** Plotly Express & Plotly Graph Objects (Subplots Architecture)

---

## 🖥️ Installation & Local Deployment

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/kayfa-analytics-dashboard.git](https://github.com/your-username/kayfa-analytics-dashboard.git)
   cd kayfa-analytics-dashboard
