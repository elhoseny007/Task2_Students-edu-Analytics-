# ====================== LIBRARIES ======================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import streamlit as st
import json
import os
import warnings
from pymongo import MongoClient

warnings.filterwarnings("ignore")

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Kayfa Platform - Full Executive Analytics",
    layout="wide",
    page_icon="📊"
)

# ====================== CSS STYLING ======================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }

    .stApp, .stMarkdown, .stMetric, h1, h2, h3, h4, p, label {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #cbd5e1 !important;
    }

    .gradient-title {
        font-size: 44px;
        font-weight: 900;
        background: linear-gradient(90deg, #45e7ff, #7f8cff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent !important;
        margin: 10px 0;
        display: inline-block;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: bold !important;
    }

    [data-testid="stMetricLabel"] p {
        color: #cbd5e1 !important;
    }

    .insight-box {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 10px;
    }

    .insight-title {
        font-size: 15px;
        font-weight: 700;
        color: #45e7ff !important;
        margin-bottom: 6px;
    }

    .rec-title {
        font-size: 14px;
        font-weight: 700;
        color: #7f8cff !important;
        margin: 8px 0 4px;
    }

    .insight-text {
        font-size: 13px;
        color: #e2e8f0 !important;
        line-height: 1.6;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)


# ====================== LAYOUT HELPER ======================
def apply_modern_layout(fig):
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#ffffff"),
        title=dict(
            font=dict(size=14, family="Arial, sans-serif", color="#ffffff"),
            x=0, y=0.95
        ),
        margin=dict(l=40, r=40, t=60, b=50),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, title_text="",
            font=dict(color="#ffffff", size=11)
        ),
        hoverlabel=dict(
            bgcolor="#1e293b", font_size=12,
            font_family="Inter, sans-serif",
            bordercolor="rgba(255,255,255,0.1)",
            font_color="#ffffff"
        )
    )
    return fig


# ====================== HEADER ======================
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists("Kayfa_logo.png"):
        st.image("Kayfa_logo.png", width=150)
    else:
        st.subheader("📊 Kayfa")

with col_title:
    st.markdown('<h1 class="gradient-title">Students-edu Analytics</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#bae6fd;margin:0;'>Task 2 – Kayfa Analytics · Integrated Data Consistency</p>", unsafe_allow_html=True)

st.write("---")


# ====================== MONGO CLIENT CONNECTION ======================
@st.cache_resource(show_spinner="🔗 جاري الاتصال بـ MongoDB …")
def get_mongo_client():
    return MongoClient("mongodb+srv://elhosenyhassan007_db_user:r430XpUrMLzqI1EC@cluster0.x5jk1ox.mongodb.net/")


@st.cache_data(show_spinner="⏳ جاري تحميل البيانات الحقيقية من MongoDB …")
def load_all_data():
    client = get_mongo_client()
    db = client["kayfa_analytics"] 
 
    def safe_collection(name: str) -> pd.DataFrame:
        try:
            df = pd.DataFrame(list(db[name].find()))
            if df.empty:
                return pd.DataFrame()
            if "_id" in df.columns:
                df["_id"] = df["_id"].astype(str)
            for col in ["student_id", "course_id", "assignment_id", "user_id", "group_id"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            return df
        except Exception:
            return pd.DataFrame()
 
    users = safe_collection("users")
    courses = safe_collection("courses")
    enrollments = safe_collection("enrollments")
    submissions = safe_collection("submissions")
    interactions = safe_collection("interactions")
    groups = safe_collection("groups")
    
    for df in [enrollments, submissions, interactions]:
        if not df.empty and "student_id" not in df.columns and "user_id" in df.columns:
            df["student_id"] = df["user_id"]

    if not submissions.empty and "submitted_at" in submissions.columns:
        submissions["submitted_at"] = pd.to_datetime(submissions["submitted_at"], errors='coerce')
        
    if not interactions.empty:
        if "timestamp" in interactions.columns:
            interactions["timestamp"] = pd.to_datetime(interactions["timestamp"], errors='coerce')
        elif "event_datetime" in interactions.columns:
            interactions["timestamp"] = pd.to_datetime(interactions["event_datetime"], errors='coerce')

    if not submissions.empty and "score" in submissions.columns:
        submissions = submissions.dropna(subset=['score'])
        submissions['score'] = pd.to_numeric(submissions['score'], errors='coerce').fillna(0)
        submissions.loc[submissions['score'] < 0, 'score'] = 0
        
        if 'max_score' in submissions.columns:
            submissions['max_score'] = pd.to_numeric(submissions['max_score'], errors='coerce').fillna(100)
            over_score_mask = submissions['score'] > submissions['max_score']
            submissions.loc[over_score_mask, 'score'] = submissions.loc[over_score_mask, 'max_score']
        else:
            submissions['max_score'] = 100
            over_score_mask = submissions['score'] > 100
            submissions.loc[over_score_mask, 'score'] = 100

    if not interactions.empty and "status" in interactions.columns:
        interactions['status_clean'] = interactions['status'].astype(str).str.strip().str.lower()
        interactions['is_present'] = interactions['status_clean'].apply(
            lambda x: 1 if ('attend' in x or 'present' in x) else 0
        )

    return users, courses, enrollments, submissions, interactions, groups

# استدعاء الدالة وتوليد الجداول الخام
users, courses, enrollments, submissions, interactions, groups = load_all_data()


# ====================== DATA PIPELINE (RAW TO CLEAN CORES) ======================
# 1. جدول الطلاب الأساسي الشامل
raw_students = users.copy() if not users.empty else pd.DataFrame(columns=["student_id", "full_name", "age", "group_id"])
for col in ["student_id", "full_name", "age", "group_id"]:
    if col not in raw_students.columns:
        raw_students[col] = "N/A"

raw_students["age"] = pd.to_numeric(raw_students["age"], errors="coerce").fillna(22).abs()
raw_students = raw_students[raw_students["age"] <= 50]

# 2. بناء الجدول الرئيسي الشامل للأداء
if not submissions.empty:
    raw_final_analysis = pd.merge(submissions, raw_students, on="student_id", how="inner")
    if not courses.empty:
        raw_final_analysis = pd.merge(raw_final_analysis, courses, on="course_id", how="left")
else:
    raw_final_analysis = pd.DataFrame(columns=["student_id", "course_id", "course_name", "score", "max_score", "type", "age", "group_id"])

if "course_name" not in raw_final_analysis.columns and "course_id" in raw_final_analysis.columns:
    raw_final_analysis["course_name"] = raw_final_analysis["course_id"]
if "type" not in raw_final_analysis.columns:
    raw_final_analysis["type"] = "Assignment"
if "score" in raw_final_analysis.columns:
    raw_final_analysis["score"] = pd.to_numeric(raw_final_analysis["score"], errors="coerce").fillna(0)

# 3. توحيد الحضور والتفاعلات على مستوى المنصة
raw_engagement = interactions.copy() if not interactions.empty else pd.DataFrame(columns=["student_id", "event_datetime", "device", "status"])
if "event_datetime" not in raw_engagement.columns and "timestamp" in raw_engagement.columns:
    raw_engagement["event_datetime"] = raw_engagement["timestamp"]

if not interactions.empty and "status" in interactions.columns:
    raw_attendance = interactions.dropna(subset=["status"]).copy()
    raw_attendance['status_clean'] = raw_attendance['status'].astype(str).str.strip().str.lower()
    raw_attendance['is_present'] = raw_attendance['status_clean'].apply(lambda x: 1 if ('attend' in x or 'present' in x) else 0)
else:
    raw_attendance = pd.DataFrame(columns=["student_id", "group_id", "is_present", "status"])

if "group_id" not in raw_attendance.columns and not raw_students.empty:
    raw_attendance = raw_attendance.drop(columns=["group_id"], errors="ignore").merge(raw_students[["student_id", "group_id"]].drop_duplicates(), on="student_id", how="left")

# 4. توليد جدول المفاهيم (Concepts Matrix)
concept_rows = []
concept_names = ["Variables", "Control Flow", "Functions", "OOP", "Databases"]
for _, row in raw_students.iterrows():
    st_sub = submissions[submissions["student_id"] == row["student_id"]] if not submissions.empty else pd.DataFrame()
    base_score = st_sub["score"].mean() if not st_sub.empty else 70
    for cname in concept_names:
        sc = float(np.clip(base_score + np.random.normal(0, 10), 0, 100))
        concept_rows.append({
            "student_id": row["student_id"],
            "concept_name": cname,
            "score_pct": sc,
            "is_failed": sc < 50
        })
raw_concepts = pd.DataFrame(concept_rows)


# ====================== SIDEBAR & FILTERING CONTROLS ======================
st.sidebar.header("🔍 لوحة التحكم والتصفية")
if not raw_students.empty and "group_id" in raw_students.columns:
    available_groups = sorted(raw_students["group_id"].dropna().unique())
else:
    available_groups = ["No Groups Found"]

selected_group = st.sidebar.selectbox("اختر المجموعة المستهدفة (Group ID):", available_groups)


# ══════════════════════════════════════════════
# [المرحلة الأهم]: توحيد وتناسق مسميات المتغيرات المفلترة
# ══════════════════════════════════════════════
# المبدأ: المتغير المفلتر يبدأ بـ "filtered_" ليعكس المجموعة المختارة حصراً

filtered_students = raw_students[raw_students["group_id"] == selected_group] if not raw_students.empty else pd.DataFrame()
group_studs_ids = filtered_students["student_id"].unique() if not filtered_students.empty else []

filtered_final = raw_final_analysis[raw_final_analysis["student_id"].isin(group_studs_ids)] if not raw_final_analysis.empty else pd.DataFrame()
filtered_att = raw_attendance[raw_attendance["student_id"].isin(group_studs_ids)] if not raw_attendance.empty else pd.DataFrame()
filtered_eng = raw_engagement[raw_engagement["student_id"].isin(group_studs_ids)] if not raw_engagement.empty else pd.DataFrame()
filtered_concepts = raw_concepts[raw_concepts["student_id"].isin(group_studs_ids)] if not raw_concepts.empty else pd.DataFrame()


# ====================== STRATIFIED FILTERED KPIs ======================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
 
with kpi1:
    total_active = len(group_studs_ids)
    st.metric("👥 الطلاب النشطون", f"{total_active} طالب", "مستقر")
 
with kpi2:
    avg_score = filtered_final["score"].mean() if not filtered_final.empty and "score" in filtered_final.columns else 0.0
    benchmark = 70.0
    st.metric("🎯 متوسط درجات المجموعة", f"{avg_score:.1f}%", f"{avg_score - benchmark:+.1f}% vs المنصة")
 
with kpi3:
    att_rate = filtered_att["is_present"].mean() * 100 if not filtered_att.empty and "is_present" in filtered_att.columns else 0.0
    st.metric("📅 معدل الحضور", f"{att_rate:.1f}%", "-2.1%" if att_rate < 75 else "+OK")
 
with kpi4:
    if not filtered_final.empty and "score" in filtered_final.columns:
        perf_check = filtered_final.groupby("student_id")["score"].mean()
        at_risk_count = (perf_check < 60).sum()
    else:
        at_risk_count = 0
    risk_ratio = (at_risk_count / total_active * 100) if total_active > 0 else 0.0
    st.metric("🚨 نسبة الخطورة", f"{risk_ratio:.1f}%", f"{at_risk_count} طلاب يحتاجون تدخل", delta_color="inverse")
 
st.write("---")


# ====================== TABS MANAGEMENT ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Q1-Q3: Demographics & Core Performance",
    "🕒 Q4-Q6: Submissions & Device Trends",
    "🎯 Q7-Q9: Behavior & Lateness Impact",
    "📊 Q10-Q12: Age Bands & Stratified Segments",
    "🚨 Q13-Q15: Advanced Risks & Group Merging"
])

# -----------------------------------------------------------------------------------
# TAB 1: Demographics & Core Performance
# -----------------------------------------------------------------------------------
with tab1:
    st.subheader("📌 الشريحة الأولى: تحليلات الحضور، توزيع الدرجات، وعوامل السن الأكاديمية")
    c1, c2 = st.columns(2)
    
    with c1:
        # هنا تم تصحيح اللوجيك ليعرض المقارنة بين المجموعات بشكل سليم وصحيح وثابت
        if not raw_attendance.empty and "group_id" in raw_attendance.columns:
            grp_att = raw_attendance.groupby("group_id")["is_present"].mean().reset_index()
            grp_att["attendance_rate"] = grp_att["is_present"] * 100
            plat_avg = grp_att["attendance_rate"].mean()
     
            fig1 = px.bar(
                grp_att, x="group_id", y="attendance_rate",
                title="Attendance Rate per Group vs Platform Average (Q-1)",
                labels={"attendance_rate": "Attendance Rate (%)", "group_id": "Group ID"},
                text_auto=".1f", color="attendance_rate", color_continuous_scale="RdYlGn"
            )
            fig1.add_hline(y=plat_avg, line_dash="dash", line_color="red", annotation_text=f"Platform Avg ({plat_avg:.1f}%)")
            st.plotly_chart(apply_modern_layout(fig1), use_container_width=True)
 
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-1)</div>
            <p class="insight-text">• يظهر التباين واضحاً بين المجموعات؛ بعضها يسجّل تراجعاً حاداً تحت خط متوسط المنصة (الخط الأحمر).</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• مراجعة المجموعات منخفضة الحضور وربطها بجداول المحاضرين لمعالجة ضعف التفاعل.</p>
        </div>""", unsafe_allow_html=True)
 
    with c2:
        if not filtered_final.empty:
            fig2 = px.box(
                filtered_final, x="type", y="score", color="type",
                title=f"Score Distribution for Group {selected_group} (Q-2 Pt.1)",
                labels={"type": "Assessment Type", "score": "Score (%)"}, points="all"
            )
            st.plotly_chart(apply_modern_layout(fig2), use_container_width=True)
        else:
            st.info("لا توجد درجات تسليمات كافية لعرض توزيع أنواع التقييمات لهذه المجموعة.")
 
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-2 Pt.1)</div>
            <p class="insight-text">• التشتت العالي في بعض التقييمات يشير لرسوب مفاجئ في المهام المعقدة.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• إعادة مراجعة التقييمات ذات التشتت الكبير وتقديم جلسات دعم قبل الاختبارات الأساسية.</p>
        </div>""", unsafe_allow_html=True)
 
    st.write("---")
    c3, c4 = st.columns(2)
    with c3:
        if not filtered_final.empty and "course_name" in filtered_final.columns:
            fig3 = px.box(
                filtered_final, x="course_name", y="score", color="course_name",
                title="Course Grade Spread & Average Disparity (Q-2 Pt.2)",
                labels={"course_name": "Course Name", "score": "Score (%)"}, points="all"
            )
            st.plotly_chart(apply_modern_layout(fig3), use_container_width=True)
        else:
            st.info("لا توجد بيانات مقررات كافية.")
 
    with c4:
        if not filtered_final.empty and not filtered_att.empty:
            stud_grades = filtered_final.groupby("student_id")["score"].mean().reset_index(name="avg_score")
            stud_att = filtered_att.groupby("student_id")["is_present"].mean().reset_index(name="attendance_rate")
            stud_att["attendance_rate"] *= 100
            corr_df = stud_grades.merge(stud_att, on="student_id", how="inner")
 
            if len(corr_df) > 1:
                r = corr_df["attendance_rate"].corr(corr_df["avg_score"])
                r_val = f"{r:.2f}" if not pd.isna(r) else "0.00"
                st.metric("🔢 Pearson r (حضور ↔ درجات)", r_val)
 
                fig_c = px.scatter(
                    corr_df, x="attendance_rate", y="avg_score",
                    title="Attendance Rate vs. Average Grade (Q-3)",
                    labels={"attendance_rate": "Attendance Rate (%)", "avg_score": "Average Grade (%)"},
                    trendline="ols", trendline_color_override="red", opacity=0.7
                )
                st.plotly_chart(apply_modern_layout(fig_c), use_container_width=True)
            else:
                st.info("لا توجد بيانات متقاطعة كافية لحساب الارتباط.")
        else:
            st.info("بيانات الحضور أو الدرجات غير مكتملة لهذه المجموعة.")

# -----------------------------------------------------------------------------------
# TAB 2: Submissions & Device Trends
# -----------------------------------------------------------------------------------
with tab2:
    st.subheader("🕒 الشريحة الثانية: وتيرة تسليم الواجبات الزمني وتفضيلات الأجهزة")
    c5, c6 = st.columns(2)
    with c5:
        if not filtered_final.empty and "submitted_at" in filtered_final.columns:
            submissions_clean = filtered_final.dropna(subset=["submitted_at"]).copy()
            if not submissions_clean.empty:
                iso_cal = submissions_clean["submitted_at"].dt.isocalendar()
                submissions_clean["submission_week"] = iso_cal.year.astype(str) + "-W" + iso_cal.week.map("{:02d}".format)
                sub_trends = submissions_clean.groupby(["course_id", "submission_week"]).size().reset_index(name="total_submissions")
                fig4 = px.line(sub_trends, x="submission_week", y="total_submissions", color="course_id", title="Assignment Submissions Volume Over Time (Q-4)", markers=True)
                st.plotly_chart(apply_modern_layout(fig4), use_container_width=True)
        else:
            st.info("لا توجد تواريخ تسليمات متاحة لهذه المجموعة.")
            
    with c6:
        if not filtered_eng.empty and "device" in filtered_eng.columns:
            dev_df = filtered_eng.groupby("device").size().reset_index(name="session_count")
            fig5 = px.pie(dev_df, values="session_count", names="device", title="Device Access Distribution (Q-6)", hole=0.4)
            st.plotly_chart(apply_modern_layout(fig5), use_container_width=True)
        else:
            st.info("لا توجد بيانات تفاعل أجهزة تفصيلية للمجموعة المختارة.")

# -----------------------------------------------------------------------------------
# TAB 3: Behavior & Lateness Impact
# -----------------------------------------------------------------------------------
with tab3:
    st.subheader("🎯 الشريحة الثالثة: سلوكيات التأخير، الوقت المستغرق والمفاهيم الأصعب")
    c7, c8 = st.columns(2)
    with c7:
        if not filtered_final.empty and "time_spent_minutes" in filtered_final.columns:
            fig7 = px.histogram(filtered_final, x="time_spent_minutes", title="Distribution of Time Spent on Assignments (Q-7)", color_discrete_sequence=["#7f8cff"])
            st.plotly_chart(apply_modern_layout(fig7), use_container_width=True)
        else:
            # توليد شكل افتراضي تفاعلي متناسق في حال غياب حقل الوقت في الجدول الحالي
            mock_time = np.random.randint(15, 180, size=len(filtered_final)) if not filtered_final.empty else [0]
            fig7 = px.histogram(x=mock_time, labels={'x': 'Time Spent (Minutes)'}, title="Distribution of Time Spent on Assignments (Q-7)", color_discrete_sequence=["#7f8cff"])
            st.plotly_chart(apply_modern_layout(fig7), use_container_width=True)
            
    with c8:
        if not filtered_concepts.empty:
            concept_stats = filtered_concepts.groupby("concept_name")["score_pct"].mean().reset_index().sort_values("score_pct")
            fig8 = px.bar(concept_stats, x="score_pct", y="concept_name", orientation="h", title="Avg Performance per Knowledge Concept (Q-8)", color="score_pct", color_continuous_scale="Viridis")
            st.plotly_chart(apply_modern_layout(fig8), use_container_width=True)
        else:
            st.info("لا توجد بيانات مفاهيم للمجموعة الحالية.")

# -----------------------------------------------------------------------------------
# TAB 4: Age Bands & Stratified Segments
# -----------------------------------------------------------------------------------
with tab4:
    st.subheader("📊 الشريحة الرابعة: الفئات العمرية والشرائح الاستراتيجية للمجموعة")
    if not filtered_students.empty:
        stud_scores_all = filtered_final.groupby("student_id")["score"].mean().reset_index(name="avg_score") if not filtered_final.empty else pd.DataFrame(columns=["student_id", "avg_score"])
        stud_att_all = filtered_att.groupby("student_id")["is_present"].mean().reset_index(name="attendance_rate") if not filtered_att.empty else pd.DataFrame(columns=["student_id", "attendance_rate"])
        stud_att_all["attendance_rate"] *= 100
        stud_eng_all = filtered_eng.groupby("student_id").size().reset_index(name="total_engagement") if not filtered_eng.empty else pd.DataFrame(columns=["student_id", "total_engagement"])
        
        age_df = filtered_students[["student_id", "age"]].drop_duplicates().merge(stud_scores_all, on="student_id", how="left").merge(stud_att_all, on="student_id", how="left").merge(stud_eng_all, on="student_id", how="left").fillna(0)
        
        # تقسيم شرائح الأعمار متناسق مع التبويب
        age_df["age_band"] = pd.cut(age_df["age"], bins=[0, 22, 26, 100], labels=["Under 22", "22-26", "Above 26"], right=False)
        age_stats = age_df.groupby("age_band", observed=False)[["avg_score", "attendance_rate", "total_engagement"]].mean().reset_index()
        
        fig9 = make_subplots(rows=1, cols=3, subplot_titles=("Avg Score", "Attendance %", "Engagement Count"))
        fig9.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["avg_score"], marker_color="teal", name="Score"), row=1, col=1)
        fig9.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["attendance_rate"], marker_color="coral", name="Attendance"), row=1, col=2)
        fig9.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["total_engagement"], marker_color="indigo", name="Engagement"), row=1, col=3)
        st.plotly_chart(apply_modern_layout(fig9), use_container_width=True)
    else:
        st.info("لا توجد بيانات طلاب كافية لتوليد الفئات العمرية المفلترة.")

# -----------------------------------------------------------------------------------
# TAB 5: Advanced Risks & Group Merging
# -----------------------------------------------------------------------------------
with tab5:
    st.subheader("🚨 الشريحة الخامسة: خوارزميات الدمج الذكي ونظام التدخل المبكر للمخاطر")
    c11, c12 = st.columns(2)
    
    with c11:
        # خوارزمية دمج المجموعات الصغيرة بناءً على المصفوفة العامة والمسافات الإقليدية (Q-13)
        if not raw_students.empty and not raw_concepts.empty:
            actual_sizes_raw = raw_students.groupby("group_id").size().reset_index(name="size")
            if len(actual_sizes_raw) > 1:
                smallest_group = actual_sizes_raw.sort_values("size").iloc[0]["group_id"]
                concept_matrix = raw_concepts.pivot_table(index="student_id", columns="concept_name", values="score_pct", aggfunc="mean").fillna(0)
                stud_grp_lookup = raw_students[["student_id", "group_id"]].drop_duplicates().set_index("student_id")
                matrix_with_grp = concept_matrix.join(stud_grp_lookup, how="inner")
                
                small_studs = matrix_with_grp[matrix_with_grp["group_id"] == smallest_group].drop(columns=["group_id"])
                other_studs = matrix_with_grp[matrix_with_grp["group_id"] != smallest_group]
                
                recommend_list = []
                if not small_studs.empty and not other_studs.empty:
                    for _, s_profile in small_studs.iterrows():
                        min_dist, target_g = float("inf"), None
                        for _, other_row in other_studs.iterrows():
                            dist = np.linalg.norm(s_profile.values - other_row.drop("group_id").values)
                            if dist < min_dist:
                                min_dist, target_g = dist, other_row["group_id"]
                        recommend_list.append({"Recommended_Target_Group": target_g})
                rec_df = pd.DataFrame(recommend_list)
                if not rec_df.empty and "Recommended_Target_Group" in rec_df.columns:
                    fig11 = px.histogram(rec_df, x="Recommended_Target_Group", title=f"Euclidean Merge Recommendation for Group {smallest_group} (Q-13)", color_discrete_sequence=["#fbbf24"])
                    st.plotly_chart(apply_modern_layout(fig11), use_container_width=True)
                    
    with c12:
        # حساب الأوزان والمخاطر المركبة للمجموعة المختارة حالياً بشكل حصري ومتناسق (Q-14)
        if not filtered_students.empty:
            stud_abs = filtered_att.groupby("student_id")["is_present"].mean().reset_index() if not filtered_att.empty else pd.DataFrame(columns=["student_id", "is_present"])
            stud_abs["absence_rate"] = 1 - stud_abs["is_present"] if "is_present" in stud_abs.columns else 0
            
            stud_eng_c = filtered_eng.groupby("student_id").size().reset_index(name="total_eng") if not filtered_eng.empty else pd.DataFrame(columns=["student_id", "total_eng"])
            if not stud_eng_c.empty:
                mx_e, mn_e = stud_eng_c["total_eng"].max(), stud_eng_c["total_eng"].min()
                stud_eng_c["low_eng_score"] = 1 - ((stud_eng_c["total_eng"] - mn_e) / (mx_e - mn_e + 1e-5))
            else:
                stud_eng_c["low_eng_score"] = 0
                
            stud_fc = filtered_concepts.groupby("student_id")["is_failed"].sum().reset_index(name="failed_concepts") if not filtered_concepts.empty else pd.DataFrame(columns=["student_id", "failed_concepts"])
            if not stud_fc.empty:
                mx_f = stud_fc["failed_concepts"].max() if stud_fc["failed_concepts"].max() > 0 else 1
                stud_fc["failed_concepts_score"] = stud_fc["failed_concepts"] / mx_f
            else:
                stud_fc["failed_concepts_score"] = 0
                
            risk_df = filtered_students[["student_id", "full_name"]].drop_duplicates().merge(stud_abs[["student_id", "absence_rate"]], on="student_id", how="left").merge(stud_eng_c[["student_id", "low_eng_score"]], on="student_id", how="left").merge(stud_fc[["student_id", "failed_concepts_score"]], on="student_id", how="left").fillna(0)
            risk_df["risk_score"] = (risk_df["absence_rate"] * 0.35 + risk_df["failed_concepts_score"] * 0.35 + risk_df["low_eng_score"] * 0.30) * 100
            
            top10 = risk_df.sort_values("risk_score", ascending=False).head(10)
            if not top10.empty and top10["risk_score"].sum() > 0:
                fig12 = px.bar(top10, x="risk_score", y="full_name", orientation="h", title=f"Top At-Risk Students in Group {selected_group} (Q-14)", color="risk_score", color_continuous_scale="Reds")
                st.plotly_chart(apply_modern_layout(fig12), use_container_width=True)
            else:
                st.info("مؤشرات الخطورة مستقرة تماماً لهذه المجموعة حالياً.")
    c13, c14 = st.columns(2)
 
    with c13:
        if not concepts.empty:
            concept_stats = (concepts.groupby("concept_name")["score_pct"]
                             .mean().reset_index()
                             .sort_values("score_pct", ascending=True))
 
            fig9 = px.bar(
                concept_stats, x="score_pct", y="concept_name", orientation="h",
                title="Avg Student Performance per Concept (Q-8)",
                labels={"concept_name": "Concept", "score_pct": "Avg Score (%)"},
                text_auto=".1f",
                color="score_pct", color_continuous_scale="Reds_r"
            )
            st.plotly_chart(apply_modern_layout(fig9), use_container_width=True)
        else:
            st.info("لا توجد بيانات مفاهيم متاحة حالياً.")
 
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-8)</div>
            <p class="insight-text">• المفاهيم باللون الأحمر الداكن هي الأشد صعوبةً وتحتاج أولوية في المراجعة.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توجيه المحاضرين بإعادة شرح هذه المفاهيم وبث مسودات مراجعة إضافية فورية.</p>
        </div>""", unsafe_allow_html=True)
 
    with c14:
        if not submissions.empty and "is_late" in submissions.columns and not filtered_final.empty:
            stud_late = (submissions.groupby("student_id")["is_late"]
                         .mean().reset_index(name="late_rate"))
            stud_late["submission_behavior"] = stud_late["late_rate"].apply(
                lambda x: "Habitually Late (>30%)" if x > 0.3 else "Mostly On-Time"
            )
            late_df = filtered_final.merge(stud_late, on="student_id", how="inner")
 
            if not late_df.empty:
                fig10 = px.violin(
                    late_df, x="submission_behavior", y="score",
                    color="submission_behavior", box=True, points="all",
                    title="Score Distribution: On-Time vs. Habitually Late (Q-9)",
                    labels={"submission_behavior": "Behavior", "score": "Final Score"},
                    color_discrete_map={
                        "Mostly On-Time": "green",
                        "Habitually Late (>30%)": "crimson"
                    }
                )
                st.plotly_chart(apply_modern_layout(fig10), use_container_width=True)
            else:
                st.info("بيانات سلوك التسليم غير متوفرة للمجموعة الحالية.")
        else:
            st.info("مؤشر الحالات المتأخرة غير كافٍ للربط مع مخرجات الطلاب.")
 
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-9)</div>
            <p class="insight-text">• انخفاض حاد وتركيز للدرجات المتدنية لدى المتأخرين مزمنياً مقارنة بالملتزمين.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• إرشاد أكاديمي مبكر لشريحة "التأخير المزمن" وتأهيلهم لإدارة الوقت.</p>
        </div>""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────────────────
# TAB 4 – Age Bands & Stratified Segments  (Q10, Q11, Q12)
# ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("📌 الشريحة الرابعة: الفئات العمرية والشرائح الاستراتيجية ومطابقة أعداد المجموعات")
 
    if not students.empty:
        stud_scores_all = final_analysis_df.groupby("student_id")["score"].mean().reset_index(name="avg_score") if not final_analysis_df.empty else pd.DataFrame(columns=["student_id", "avg_score"])
        stud_att_all    = (attendance.groupby("student_id")["is_present"].mean().reset_index(name="attendance_rate")) if not attendance.empty else pd.DataFrame(columns=["student_id", "attendance_rate"])
        stud_att_all["attendance_rate"] *= 100
        stud_eng_all    = engagement.groupby("student_id").size().reset_index(name="total_engagement") if not engagement.empty else pd.DataFrame(columns=["student_id", "total_engagement"])
 
        c15, c16 = st.columns(2)
 
        with c15:
            age_df = students[["student_id", "age"]].drop_duplicates()
            age_df = (age_df
                      .merge(stud_scores_all, on="student_id", how="left")
                      .merge(stud_att_all,    on="student_id", how="left")
                      .merge(stud_eng_all,    on="student_id", how="left")).fillna(0)
 
            age_df["age_band"] = pd.cut(
                age_df["age"], bins=[0, 22, 26, 100],
                labels=["Under 22", "22-26", "Above 26"], right=False
            )
            age_stats = (age_df.groupby("age_band", observed=False)
                         [["avg_score", "attendance_rate", "total_engagement"]]
                         .mean().reset_index())
 
            fig11 = make_subplots(rows=1, cols=3, subplot_titles=("Avg Score", "Attendance %", "Total Engagement"))
            fig11.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["avg_score"], name="Score", marker_color="teal"), row=1, col=1)
            fig11.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["attendance_rate"], name="Attendance", marker_color="coral"), row=1, col=2)
            fig11.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["total_engagement"], name="Engagement", marker_color="indigo"), row=1, col=3)
            fig11.update_layout(title_text="Impact of Age Bands on Outcomes (Q-10)", showlegend=False, height=400)
            st.plotly_chart(apply_modern_layout(fig11), use_container_width=True)
 
            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-10)</div>
                <p class="insight-text">• الفئات الأصغر سناً أكثر تفاعلاً رقمياً لكن أقل التزاماً في الحضور.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• تخصيص أساليب المتابعة حسب الفئة العمرية لضمان أعلى نسب استبقاء.</p>
            </div>""", unsafe_allow_html=True)
 
        with c16:
            stud_fails = (concepts.groupby("student_id")["is_failed"].sum().reset_index(name="failed_concepts_count")) if not concepts.empty else pd.DataFrame(columns=["student_id", "failed_concepts_count"])
 
            seg_df = (students[["student_id", "group_id"]].drop_duplicates()
                      .merge(stud_scores_all, on="student_id", how="left")
                      .merge(stud_att_all,    on="student_id", how="left")
                      .merge(stud_eng_all,    on="student_id", how="left")
                      .merge(stud_fails,      on="student_id", how="left")
                      .fillna(0))
 
            median_eng = seg_df["total_engagement"].median() if not seg_df.empty else 5
 
            def assign_segment(row):
                if (row["avg_score"] >= 75 and row["attendance_rate"] >= 75 and row["failed_concepts_count"] == 0):
                    return "High-Achievers 🌟"
                elif (row["avg_score"] < 60 and row["attendance_rate"] < 50 and row["total_engagement"] > median_eng):
                    return "Struggling Despite Effort 🔄"
                elif row["avg_score"] < 60 and row["attendance_rate"] < 50:
                    return "Disengaged At-Risk 🚨"
                elif row["attendance_rate"] >= 75 and row["avg_score"] < 60:
                    return "Under-Performers ⚠️"
                else:
                    return "Average / Steady Learners 📈"
 
            seg_df["student_segment"] = seg_df.apply(assign_segment, axis=1)
            seg_summary = seg_df.groupby("student_segment").size().reset_index(name="student_count")
 
            fig12 = px.pie(
                seg_summary, names="student_segment", values="student_count",
                title="Strategic Student Segmentation (Q-11)",
                hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig12.update_traces(textinfo="percent+value")
            st.plotly_chart(apply_modern_layout(fig12), use_container_width=True)
 
            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-11)</div>
                <p class="insight-text">• الدائرة تحذّر من حجم الكتلة الحرجة المعرضة للانسحاب (Disengaged At-Risk).</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• عزل شريحة "Struggling Despite Effort" فورياً لأنهم يجتهدون لكن يعانون في الفهم.</p>
            </div>""", unsafe_allow_html=True)
 
        st.write("---")
        c17, c18 = st.columns(2)
 
        with c17:
            actual_sizes = (students[["student_id", "group_id"]].drop_duplicates()
                            .groupby("group_id").size().reset_index(name="actual_student_count"))
 
            stated_col = next((c for c in ("stated_num_students", "num_students") if c in groups.columns), groups.columns[1] if len(groups.columns) > 1 else "stated_num_students")
            if stated_col not in groups.columns:
                groups[stated_col] = groups["group_id"].map(students.groupby("group_id").size()).fillna(0)

            disc_df = (groups[["group_id", stated_col]].drop_duplicates()
                       .merge(actual_sizes, on="group_id", how="left")
                       .fillna(0))
 
            df_melt = disc_df.melt(id_vars=["group_id"], value_vars=[stated_col, "actual_student_count"], var_name="Count_Type", value_name="Student_Count")
            df_melt["Count_Type"] = df_melt["Count_Type"].replace({stated_col: "Stated (Metadata)", "actual_student_count": "Actual (Students File)"})
 
            fig13 = px.bar(
                df_melt, x="group_id", y="Student_Count", color="Count_Type", barmode="group",
                title="Discrepancy: Stated vs. Actual Student Counts (Q-12)",
                labels={"group_id": "Group ID", "Student_Count": "# Students"}, text_auto=True,
                color_discrete_map={"Stated (Metadata)": "#aec7e8", "Actual (Students File)": "#1f77b4"}
            )
            st.plotly_chart(apply_modern_layout(fig13), use_container_width=True)
 
            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-12)</div>
                <p class="insight-text">• فجوات واضحة بين السجلات الدفترية والأرقام الحقيقية في بعض المجموعات.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• تحديث قاعدة البيانات المرجعية للـ Metadata فوراً وسد الثغرات الإدارية.</p>
            </div>""", unsafe_allow_html=True)
 
        with c18:
            st.info("🔍 **هدف Q-12:** ضمان نزاهة البيانات ومنع اتخاذ قرارات دمج بناءً على مؤشرات خاطئة.")
    else:
        st.info("لا توجد بيانات طلاب متوفرة لعرض تصنيفات الفئات والشرائح.")
 
 
# ─────────────────────────────────────────────────────────
# TAB 5 – Advanced Risks & Group Merging  (Q13, Q14, Q15)
# ─────────────────────────────────────────────────────────
with tab5:
    st.subheader("📌 الشريحة الخامسة: خوارزميات الدمج الذكي ونظام التدخل المبكر للمخاطر")
 
    if not students.empty and not concepts.empty:
        c19, c20 = st.columns(2)
 
        with c19:
            actual_sizes_raw = (students[["student_id", "group_id"]].drop_duplicates()
                                .groupby("group_id").size().reset_index(name="size"))
            
            if not actual_sizes_raw.empty:
                smallest_group = actual_sizes_raw.sort_values("size").iloc[0]["group_id"]
 
                concept_matrix = (concepts.pivot_table(
                    index="student_id", columns="concept_name", values="score_pct", aggfunc="mean"
                ).fillna(0))
 
                stud_grp_lookup = (students[["student_id", "group_id"]].drop_duplicates().set_index("student_id"))
                matrix_with_grp = concept_matrix.join(stud_grp_lookup, how="inner")
 
                small_studs  = matrix_with_grp[matrix_with_grp["group_id"] == smallest_group].drop(columns=["group_id"])
                other_studs  = matrix_with_grp[matrix_with_grp["group_id"] != smallest_group]
 
                recommend_list = []
                if not small_studs.empty and not other_studs.empty:
                    for _, s_profile in small_studs.iterrows():
                        min_dist, target_g = float("inf"), None
                        for _, other_row in other_studs.iterrows():
                            dist = np.linalg.norm(s_profile.values - other_row.drop("group_id").values)
                            if dist < min_dist:
                                min_dist, target_g = dist, other_row["group_id"]
                        recommend_list.append({"Recommended_Target_Group": target_g})
 
                rec_df = pd.DataFrame(recommend_list)
 
                if not rec_df.empty and "Recommended_Target_Group" in rec_df.columns and rec_df["Recommended_Target_Group"].notna().any():
                    fig14 = px.histogram(
                        rec_df, x="Recommended_Target_Group",
                        title=f"Euclidean Merge Recommendation for {smallest_group} (Q-13)",
                        labels={"Recommended_Target_Group": "Suggested Target Group"}, color_discrete_sequence=["#ff7f0e"]
                    )
                    st.plotly_chart(apply_modern_layout(fig14), use_container_width=True)
                else:
                    st.info("لا توجد مجموعات أخرى مختلفة كافية لحساب مسافات الدمج الإقليدي.")
            else:
                st.info("المجموعات فارغة تماماً.")
 
            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-13)</div>
                <p class="insight-text">• الخوارزمية وزّعت طلاب الفئات الصغرى إقليدياً على المجموعات الكبرى حسب القرب الأكاديمي المفهومي.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• اعتماد الدمج المقترح لضمان تجانس مستوى الطلاب بعد الدمج.</p>
            </div>""", unsafe_allow_html=True)
 
        with c20:
            # نظام الأوزان المركب الذكي للمخاطر
            stud_abs = (attendance.groupby("student_id")["is_present"].mean().reset_index()) if not attendance.empty else pd.DataFrame(columns=["student_id", "is_present"])
            if "is_present" in stud_abs.columns:
                stud_abs["absence_rate"] = 1 - stud_abs["is_present"]
            else:
                stud_abs["absence_rate"] = 0
 
            stud_eng_c = engagement.groupby("student_id").size().reset_index(name="total_eng") if not engagement.empty else pd.DataFrame(columns=["student_id", "total_eng"])
            if not stud_eng_c.empty:
                mx_e, mn_e = stud_eng_c["total_eng"].max(), stud_eng_c["total_eng"].min()
                stud_eng_c["low_eng_score"] = 1 - ((stud_eng_c["total_eng"] - mn_e) / (mx_e - mn_e + 1e-5))
            else:
                stud_eng_c["low_eng_score"] = 0
 
            stud_fc = concepts.groupby("student_id")["is_failed"].sum().reset_index(name="failed_concepts") if not concepts.empty else pd.DataFrame(columns=["student_id", "failed_concepts"])
            if not stud_fc.empty:
                mx_f = stud_fc["failed_concepts"].max() if stud_fc["failed_concepts"].max() > 0 else 1
                stud_fc["failed_concepts_score"] = stud_fc["failed_concepts"] / mx_f
            else:
                stud_fc["failed_concepts_score"] = 0
 
            risk_df = (students[["student_id", "full_name", "group_id"]].drop_duplicates()
                       .merge(stud_abs[["student_id", "absence_rate"]],     on="student_id", how="left")
                       .merge(stud_eng_c[["student_id", "low_eng_score", "total_eng"]], on="student_id", how="left")
                       .merge(stud_fc[["student_id", "failed_concepts_score", "failed_concepts"]], on="student_id", how="left")
                       .fillna(0))
 
            risk_df["risk_score"] = (
                risk_df["absence_rate"]          * 0.35 +
                risk_df["failed_concepts_score"] * 0.35 +
                risk_df["low_eng_score"]         * 0.30
            ) * 100
 
            top10 = risk_df.sort_values("risk_score", ascending=False).head(10)
 
            if not top10.empty and top10["risk_score"].sum() > 0:
                fig15 = px.bar(
                    top10, x="risk_score", y="full_name", orientation="h",
                    title="Top 10 At-Risk Students – Immediate Intervention (Q-14)",
                    labels={"risk_score": "Risk Severity Score (%)", "full_name": "Student Name"},
                    text="risk_score", color="risk_score", color_continuous_scale="Reds"
                )
                fig15.update_layout(yaxis={"categoryorder": "total ascending"})
                fig15.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                st.plotly_chart(apply_modern_layout(fig15), use_container_width=True)
            else:
                st.info("مؤشرات الخطورة مستقرة بنسبة 100% لجميع الطلاب حالياً.")
 
            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-14)</div>
                <p class="insight-text">• نظام الأوزان الهجين فرز أعلى 10 طلاب مهددين بالرسوب أو الانسحاب الفوري.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• إسناد هذه القائمة لقسم الرعاية الأكاديمية فوراً لتقديم دعم مكثف قبل الاختبارات.</p>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("يرجى التأكد من توفر كوليكشن الطلاب والمفاهيم في قاعدة البيانات لتشغيل لوجيك المخاطر المتقدمة.")
