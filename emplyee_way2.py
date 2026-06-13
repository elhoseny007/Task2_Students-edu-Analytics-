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

warnings.filterwarnings("ignore")

# ====================== PAGE CONFIG (يجب يكون أول أمر) ======================
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

    /* ── Insight / Recommendation boxes ── */
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
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#ffffff"),
        title=dict(
            font=dict(size=16, family="Arial, sans-serif", color="#ffffff"),
            x=0, y=0.95
        ),
        margin=dict(l=40, r=40, t=60, b=50),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, title_text="",
            font=dict(color="#ffffff", size=12)
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
    st.markdown("<p style='color:#bae6fd;margin:0;'>Task 2 – Kayfa Analytics · Internship Program</p>",
                unsafe_allow_html=True)

st.write("---")


# ====================== DATA LOADING ======================
# ⚠️  غيّر المسارات دي لو شغّالت من MongoDB أو حاجة تانية
DATA_DIR = r"d:\Desktop\Data Analysis\Internship"   # ← عدّل هنا فقط

@st.cache_data(show_spinner="⏳ جاري تحميل البيانات …")
def load_all_data(data_dir: str):
    # ── CSV files ──
    courses     = pd.read_csv(os.path.join(data_dir, "courses.csv"))
    groups      = pd.read_csv(os.path.join(data_dir, "groups.csv"))
    students    = pd.read_csv(os.path.join(data_dir, "students.csv"))
    concepts    = pd.read_csv(os.path.join(data_dir, "concepts_performance.csv"))
    engagement  = pd.read_csv(os.path.join(data_dir, "engagement_events.csv"))
    submissions = pd.read_csv(os.path.join(data_dir, "assignment_submissions.csv"))

    # ── JSON grades ──
    with open(os.path.join(data_dir, "grades.json"), "r", encoding="utf-8") as f:
        raw_grades = json.load(f)
    grades = pd.json_normalize(
        raw_grades,
        record_path=["grades"],
        meta=["student_id", "course_id", "group_id"]
    )

    # ── Excel attendance (دمج كل الـ sheets) ──
    excel_file = pd.ExcelFile(os.path.join(data_dir, "attendance.xlsx"))
    attendance = pd.concat(
        [pd.read_excel(excel_file, sheet_name=s) for s in excel_file.sheet_names],
        ignore_index=True
    )

    # ── Merge & clean final_df ──
    merged = students.merge(groups,   on="group_id",   how="left", suffixes=("_student", "_group"))
    merged = merged.merge(courses,    on="course_id",  how="left")
    final_df = merged.merge(grades,   on="student_id", how="left", suffixes=("", "_grades"))

    # تنظيف الدرجات والأعمار
    final_df.dropna(subset=["score"], inplace=True)
    final_df["age"]   = final_df["age"].abs()
    final_df          = final_df[final_df["age"] <= 50]
    final_df.loc[final_df["score"] < 0, "score"] = 0

    over_mask = final_df["score"] > final_df["max_score"]
    final_df.loc[over_mask, "score"] = final_df.loc[over_mask, "max_score"]
    final_df["date"]  = pd.to_datetime(final_df["date"])

    # تنظيف الحضور
    attendance["status_clean"] = attendance["status"].astype(str).str.strip().str.lower()
    attendance["is_present"]   = attendance["status_clean"].apply(
        lambda x: 1 if ("attend" in x or "present" in x) else 0
    )

    # تنظيف تواريخ التسليم والتفاعل
    submissions["submitted_at"] = pd.to_datetime(submissions["submitted_at"])
    if "event_datetime" in engagement.columns:
        engagement["event_datetime"] = pd.to_datetime(engagement["event_datetime"])

    # عمود is_failed في concepts
    concepts["is_failed"] = concepts["score_pct"] < 50

    return final_df, attendance, concepts, engagement, submissions, groups, students


# تحميل البيانات مرة واحدة
try:
    final_analysis_df, attendance, concepts, engagement, submissions, groups, students = load_all_data(DATA_DIR)
except Exception as e:
    st.error(f"❌ خطأ في تحميل البيانات: {e}")
    st.stop()

if final_analysis_df.empty:
    st.warning("⚠️ البيانات فارغة! تأكد من مسارات الملفات.")
    st.stop()


# ====================== SIDEBAR ======================
st.sidebar.header("🔍 لوحة التحكم والتصفية")

with st.sidebar:
    if os.path.exists("Kayfa_logo.png"):
        st.image("Kayfa_logo.png", width=160)

available_groups = sorted(final_analysis_df["group_id"].unique())
selected_group   = st.sidebar.selectbox("اختر المجموعة المستهدفة (Group ID):", available_groups)

# فلترة البيانات للمجموعة المختارة
filtered_final  = final_analysis_df[final_analysis_df["group_id"] == selected_group]
group_studs     = filtered_final["student_id"].unique()
filtered_att    = attendance[attendance["student_id"].isin(group_studs)]


# ====================== KPIs ======================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    total_active = filtered_final["student_id"].nunique()
    st.metric("👥 الطلاب النشطون", f"{total_active} طالب", "مستقر")

with kpi2:
    avg_score      = filtered_final["score"].mean() if not filtered_final.empty else 0.0
    benchmark      = 70.0
    st.metric("🎯 متوسط درجات المجموعة", f"{avg_score:.1f}%",
              f"{avg_score - benchmark:+.1f}% vs المنصة")

with kpi3:
    att_rate = filtered_att["is_present"].mean() * 100 if not filtered_att.empty else 0.0
    st.metric("📅 معدل الحضور", f"{att_rate:.1f}%",
              "-2.1%" if att_rate < 75 else "+OK")

with kpi4:
    perf_check   = filtered_final.groupby("student_id")["score"].mean()
    at_risk_count = (perf_check < 60).sum() if not perf_check.empty else 0
    risk_ratio   = (at_risk_count / total_active * 100) if total_active > 0 else 0
    st.metric("🚨 نسبة الخطورة", f"{risk_ratio:.1f}%",
              f"{at_risk_count} طلاب يحتاجون تدخل", delta_color="inverse")

st.write("---")


# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Q1-Q3: Demographics & Core Performance",
    "🕒 Q4-Q6: Submissions & Device Trends",
    "🎯 Q7-Q9: Behavior & Lateness Impact",
    "📊 Q10-Q12: Age Bands & Stratified Segments",
    "🚨 Q13-Q15: Advanced Risks & Group Merging"
])


# ─────────────────────────────────────────────────────────
# TAB 1 – Demographics & Core Performance  (Q1, Q2, Q3)
# ─────────────────────────────────────────────────────────
with tab1:
    st.subheader("📌 الشريحة الأولى: تحليلات الحضور، توزيع الدرجات، وعوامل السن الأكاديمية")

    c1, c2 = st.columns(2)

    with c1:
        grp_att = (attendance.groupby("group_id")["is_present"]
                   .mean().reset_index())
        grp_att["attendance_rate"] = grp_att["is_present"] * 100
        plat_avg = grp_att["attendance_rate"].mean()

        fig1 = px.bar(
            grp_att, x="group_id", y="attendance_rate",
            title="Attendance Rate per Group vs Platform Average (Q-1)",
            labels={"attendance_rate": "Attendance Rate (%)"},
            text_auto=".1f",
            color="attendance_rate",
            color_continuous_scale="RdYlGn"
        )
        fig1.add_hline(
            y=plat_avg, line_dash="dash", line_color="red",
            annotation_text=f"Platform Avg ({plat_avg:.1f}%)"
        )
        fig1.update_xaxes(title_text="Group ID")
        fig1.update_yaxes(title_text="Attendance Rate (%)")
        st.plotly_chart(apply_modern_layout(fig1), use_container_width=True)

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-1)</div>
            <p class="insight-text">• يظهر التباين واضحاً بين المجموعات؛ بعضها يسجّل تراجعاً حاداً تحت خط متوسط المنصة (الخط الأحمر).</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• مراجعة المجموعات منخفضة الحضور وربطها بجداول المحاضرين لمعالجة ضعف التفاعل.</p>
        </div>""", unsafe_allow_html=True)

    with c2:
        fig2 = px.box(
            filtered_final, x="type", y="score", color="type",
            title="Score Distribution & Volatility by Assessment Type (Q-2 Pt.1)",
            labels={"type": "Assessment Type", "score": "Score (%)"},
            points="all",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(apply_modern_layout(fig2), use_container_width=True)

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
        fig3 = px.box(
            filtered_final, x="course_name", y="score", color="course_name",
            title="Course Grade Spread & Average Disparity (Q-2 Pt.2)",
            labels={"course_name": "Course Name", "score": "Score (%)"},
            points="all",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(apply_modern_layout(fig3), use_container_width=True)

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-2 Pt.2)</div>
            <p class="insight-text">• فارق ملحوظ في متوسط الدرجات بين الكورسات يشير لوجود مقررات عنق زجاجة (Bottleneck).</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توحيد معايير التصحيح وتزويد المقررات الضعيفة بمحتوى تعويضي إضافي.</p>
        </div>""", unsafe_allow_html=True)

    with c4:
        stud_grades = filtered_final.groupby("student_id")["score"].mean().reset_index(name="avg_score")
        stud_att    = (attendance.groupby("student_id")["is_present"]
                       .mean().reset_index(name="attendance_rate"))
        stud_att["attendance_rate"] *= 100
        corr_df = stud_grades.merge(stud_att, on="student_id", how="inner")

        if len(corr_df) > 1:
            r = corr_df["attendance_rate"].corr(corr_df["avg_score"])
            st.metric("🔢 Pearson r (حضور ↔ درجات)", f"{r:.2f}")

            fig_c = px.scatter(
                corr_df, x="attendance_rate", y="avg_score",
                title="Attendance Rate vs. Average Grade (Q-3)",
                labels={"attendance_rate": "Attendance Rate (%)", "avg_score": "Average Grade (%)"},
                trendline="ols", trendline_color_override="red", opacity=0.7
            )
            st.plotly_chart(apply_modern_layout(fig_c), use_container_width=True)

            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-3)</div>
                <p class="insight-text">• معامل الارتباط ({r:.2f}) يثبت الأثر الطردي القوي للحضور على الدرجات.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• تفعيل تنبيه آلي فور انخفاض نسبة حضور أي طالب تجنباً للانهيار الأكاديمي.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات متقاطعة كافية لحساب الارتباط لهذه المجموعة.")


# ─────────────────────────────────────────────────────────
# TAB 2 – Submissions & Device Trends  (Q4, Q5, Q6)
# ─────────────────────────────────────────────────────────
with tab2:
    st.subheader("📌 الشريحة الثانية: تتبع وتيرة التسليمات وتفاعل الأجهزة الذكية")

    c5, c6 = st.columns(2)

    with c5:
        submissions["submission_week"] = submissions["submitted_at"].dt.isocalendar().week
        sub_trends = (submissions.groupby(["course_id", "submission_week"])
                      .size().reset_index(name="total_submissions"))

        fig4 = px.line(
            sub_trends, x="submission_week", y="total_submissions", color="course_id",
            title="Assignment Submission Trends Across Calendar Weeks (Q-4)",
            labels={"submission_week": "Calendar Week", "total_submissions": "Submissions Count"},
            markers=True
        )
        fig4.update_layout(xaxis_type="category")
        st.plotly_chart(apply_modern_layout(fig4), use_container_width=True)

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-4)</div>
            <p class="insight-text">• قمم (Peaks) محددة متبوعة بانهيار مفاجئ تكشف غياب الاستمرارية في التسليم.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توزيع الـ Deadlines بشكل متوازن على مدار الشهر لتخفيف الضغط.</p>
        </div>""", unsafe_allow_html=True)

    with c6:
        engagement["engagement_week"] = engagement["event_datetime"].dt.isocalendar().week
        weekly_eng = (engagement.groupby("engagement_week")
                      .size().reset_index(name="total_events"))

        fig5 = px.line(
            weekly_eng, x="engagement_week", y="total_events",
            title="Total Engagement Events Across Weeks – Mid-Course Slump (Q-5)",
            labels={"engagement_week": "Calendar Week", "total_events": "Total Events"},
            markers=True
        )
        fig5.update_traces(line_color="purple", line_width=3)
        fig5.update_layout(xaxis_type="category")
        st.plotly_chart(apply_modern_layout(fig5), use_container_width=True)

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-5)</div>
            <p class="insight-text">• انخفاض ملحوظ في التفاعل بمنتصف الكورس (Mid-Course Slump) مؤشر نفسي خطير.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• إطلاق مسابقات Gamification في الأسابيع الحرجة لإعادة تنشيط الحركة الرقمية.</p>
        </div>""", unsafe_allow_html=True)

    st.write("---")
    c7, c8 = st.columns(2)

    with c7:
        student_device = (engagement.groupby("student_id")["device"]
                          .agg(lambda x: x.mode()[0])
                          .reset_index(name="primary_device"))
        device_perf = filtered_final.merge(student_device, on="student_id", how="inner")

        if not device_perf.empty:
            fig6 = px.box(
                device_perf, x="primary_device", y="score", color="primary_device",
                title="Academic Performance by Device Type (Q-6)",
                labels={"primary_device": "Primary Device", "score": "Final Score"},
                points="outliers"
            )
            st.plotly_chart(apply_modern_layout(fig6), use_container_width=True)

            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-6)</div>
                <p class="insight-text">• فارق في الأداء بين الأجهزة يلمح لفجوة فنية في التطبيق على بعض المنصات.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• تحسين UI/UX والتأكد من التوافق الكامل مع شاشات الموبايل.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.warning("لا توجد بيانات أجهزة مطابقة للمجموعة الحالية.")

    with c8:
        st.success("📊 **ملخص:** يربط التحليل أعلاه بين البنية التحتية لتجربة الطالب الرقمية ومخرجاته الأكاديمية.")

    # Engagement ↔ Performance scatter (full-width)
    stud_perf = filtered_final.groupby("student_id")["score"].mean().reset_index(name="avg_score")
    stud_eng  = engagement.groupby("student_id").size().reset_index(name="total_engagement_events")
    eng_df    = stud_perf.merge(stud_eng, on="student_id", how="inner")

    if len(eng_df) > 1:
        eng_r = eng_df["total_engagement_events"].corr(eng_df["avg_score"])
        st.metric("🔢 Engagement ↔ Grade Correlation (r)", f"{eng_r:.2f}")

        fig_eng = px.scatter(
            eng_df, x="total_engagement_events", y="avg_score",
            title="Platform Engagement vs. Academic Performance",
            labels={"total_engagement_events": "Total Engagement Events",
                    "avg_score": "Average Grade (%)"},
            trendline="ols", trendline_color_override="#7f8cff", opacity=0.7
        )
        st.plotly_chart(apply_modern_layout(fig_eng), use_container_width=True)

        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Engagement)</div>
            <p class="insight-text">• ارتباط بقيمة ({eng_r:.2f}) يبرهن أن التفاعل المستمر هو المحرك الرئيسي للثبات الأكاديمي.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تصميم نظام Push Notifications للطلاب الخاملين لرفع معدلات الدخول اليومية.</p>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# TAB 3 – Behavior & Lateness Impact  (Q7, Q8, Q9)
# ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("📌 الشريحة الثالثة: سلوكيات التأخير، الوقت المستغرق والمفاهيم الأصعب")

    c11, c12 = st.columns(2)

    with c11:
        fig7 = px.scatter(
            submissions, x="time_spent_minutes", y="attempts",
            title="Time Spent vs. Number of Attempts (Q-7 Pt.1)",
            labels={"time_spent_minutes": "Time Spent (min)", "attempts": "Attempts"},
            trendline="ols", trendline_color_override="darkblue", opacity=0.5
        )
        st.plotly_chart(apply_modern_layout(fig7), use_container_width=True)

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-7 Pt.1)</div>
            <p class="insight-text">• زيادة الوقت ترتبط طردياً بزيادة المحاولات، مما يشير لصعوبة بالغة في بعض الأسئلة.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تقسيم الواجبات المُعقَّدة إلى أجزاء تدريجية أصغر لتخفيف الارتباك.</p>
        </div>""", unsafe_allow_html=True)

    with c12:
        fig8 = px.box(
            submissions, x="is_late", y="time_spent_minutes", color="is_late",
            title="Time Spent: On-Time vs. Late Submissions (Q-7 Pt.2)",
            labels={"is_late": "Is Late?", "time_spent_minutes": "Time Spent (min)"},
            color_discrete_map={True: "#ef4444", False: "#22c55e"}
        )
        st.plotly_chart(apply_modern_layout(fig8), use_container_width=True)

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-7 Pt.2)</div>
            <p class="insight-text">• الطلاب المتأخرون يسجلون أوقات حل أقل، مما يعني مماطلة وحل متسرّع لا صعوبة.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• فرض غرامات درجات تصاعدية طفيفة على التأخير لتحفيز الالتزام المبكر.</p>
        </div>""", unsafe_allow_html=True)

    st.write("---")
    c13, c14 = st.columns(2)

    with c13:
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

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-8)</div>
            <p class="insight-text">• المفاهيم باللون الأحمر الداكن هي الأشد صعوبةً وتحتاج أولوية في المراجعة.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توجيه المحاضرين بإعادة شرح هذه المفاهيم وبث مسودات مراجعة إضافية فورية.</p>
        </div>""", unsafe_allow_html=True)

    with c14:
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

            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-9)</div>
                <p class="insight-text">• انخفاض حاد وتركيز للدرجات المتدنية لدى المتأخرين مزمنياً مقارنة بالملتزمين.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• إرشاد أكاديمي مبكر لشريحة "التأخير المزمن" وتأهيلهم لإدارة الوقت.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("بيانات سلوك التسليم غير متوفرة للمجموعة الحالية.")


# ─────────────────────────────────────────────────────────
# TAB 4 – Age Bands & Stratified Segments  (Q10, Q11, Q12)
# ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("📌 الشريحة الرابعة: الفئات العمرية والشرائح الاستراتيجية ومطابقة أعداد المجموعات")

    # جمع المؤشرات على مستوى الطالب
    stud_scores_all = final_analysis_df.groupby("student_id")["score"].mean().reset_index(name="avg_score")
    stud_att_all    = (attendance.groupby("student_id")["is_present"]
                       .mean().reset_index(name="attendance_rate"))
    stud_att_all["attendance_rate"] *= 100
    stud_eng_all    = engagement.groupby("student_id").size().reset_index(name="total_engagement")

    c15, c16 = st.columns(2)

    with c15:
        age_df = students[["student_id", "age"]].drop_duplicates()
        age_df = (age_df
                  .merge(stud_scores_all, on="student_id", how="left")
                  .merge(stud_att_all,    on="student_id", how="left")
                  .merge(stud_eng_all,    on="student_id", how="left"))

        age_df["age_band"] = pd.cut(
            age_df["age"], bins=[0, 22, 26, 100],
            labels=["Under 22", "22-26", "Above 26"], right=False
        )
        age_stats = (age_df.groupby("age_band", observed=False)
                     [["avg_score", "attendance_rate", "total_engagement"]]
                     .mean().reset_index())

        fig11 = make_subplots(rows=1, cols=3,
                              subplot_titles=("Avg Score", "Attendance %", "Total Engagement"))
        fig11.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["avg_score"],
                               name="Score", marker_color="teal"), row=1, col=1)
        fig11.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["attendance_rate"],
                               name="Attendance", marker_color="coral"), row=1, col=2)
        fig11.add_trace(go.Bar(x=age_stats["age_band"], y=age_stats["total_engagement"],
                               name="Engagement", marker_color="indigo"), row=1, col=3)
        fig11.update_layout(title_text="Impact of Age Bands on Outcomes (Q-10)",
                            showlegend=False, height=400)
        st.plotly_chart(apply_modern_layout(fig11), use_container_width=True)

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-10)</div>
            <p class="insight-text">• الفئات الأصغر سناً أكثر تفاعلاً رقمياً لكن أقل التزاماً في الحضور.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تخصيص أساليب المتابعة حسب الفئة العمرية لضمان أعلى نسب استبقاء.</p>
        </div>""", unsafe_allow_html=True)

    with c16:
        stud_fails = (concepts.groupby("student_id")["is_failed"]
                      .sum().reset_index(name="failed_concepts_count"))

        seg_df = (students[["student_id", "group_id"]].drop_duplicates()
                  .merge(stud_scores_all, on="student_id", how="left")
                  .merge(stud_att_all,    on="student_id", how="left")
                  .merge(stud_eng_all,    on="student_id", how="left")
                  .merge(stud_fails,      on="student_id", how="left")
                  .fillna(0))

        median_eng = seg_df["total_engagement"].median()

        def assign_segment(row):
            if (row["avg_score"] >= 75
                    and row["attendance_rate"] >= 75
                    and row["failed_concepts_count"] == 0):
                return "High-Achievers 🌟"
            elif (row["avg_score"] < 60
                  and row["attendance_rate"] < 50
                  and row["total_engagement"] > median_eng):
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
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
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

        # اكتشاف اسم العمود الصحيح في جدول المجموعات
        stated_col = next(
            (c for c in ("stated_num_students", "num_students") if c in groups.columns),
            groups.columns[1]
        )
        disc_df = (groups[["group_id", stated_col]].drop_duplicates()
                   .merge(actual_sizes, on="group_id", how="left")
                   .fillna(0))

        df_melt = disc_df.melt(
            id_vars=["group_id"],
            value_vars=[stated_col, "actual_student_count"],
            var_name="Count_Type", value_name="Student_Count"
        )
        df_melt["Count_Type"] = df_melt["Count_Type"].replace({
            stated_col: "Stated (Metadata)",
            "actual_student_count": "Actual (Students File)"
        })

        fig13 = px.bar(
            df_melt, x="group_id", y="Student_Count", color="Count_Type",
            barmode="group",
            title="Discrepancy: Stated vs. Actual Student Counts (Q-12)",
            labels={"group_id": "Group ID", "Student_Count": "# Students"},
            text_auto=True,
            color_discrete_map={
                "Stated (Metadata)": "#aec7e8",
                "Actual (Students File)": "#1f77b4"
            }
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


# ─────────────────────────────────────────────────────────
# TAB 5 – Advanced Risks & Group Merging  (Q13, Q14, Q15)
# ─────────────────────────────────────────────────────────
with tab5:
    st.subheader("📌 الشريحة الخامسة: خوارزميات الدمج الذكي ونظام التدخل المبكر للمخاطر")

    c19, c20 = st.columns(2)

    with c19:
        actual_sizes_raw = (students[["student_id", "group_id"]].drop_duplicates()
                            .groupby("group_id").size().reset_index(name="size"))
        smallest_group = actual_sizes_raw.sort_values("size").iloc[0]["group_id"]

        # مصفوفة الأداء المفهومي
        concept_matrix = (concepts.pivot_table(
            index="student_id", columns="concept_name",
            values="score_pct", aggfunc="mean"
        ).fillna(0))

        stud_grp_lookup = (students[["student_id", "group_id"]].drop_duplicates()
                           .set_index("student_id"))
        matrix_with_grp = concept_matrix.join(stud_grp_lookup, how="inner")

        small_studs  = matrix_with_grp[matrix_with_grp["group_id"] == smallest_group].drop(columns=["group_id"])
        other_studs  = matrix_with_grp[matrix_with_grp["group_id"] != smallest_group]

        recommend_list = []
        for _, s_profile in small_studs.iterrows():
            min_dist, target_g = float("inf"), None
            for _, other_row in other_studs.iterrows():
                dist = np.linalg.norm(s_profile.values - other_row.drop("group_id").values)
                if dist < min_dist:
                    min_dist, target_g = dist, other_row["group_id"]
            recommend_list.append({"Recommended_Target_Group": target_g})

        rec_df = pd.DataFrame(recommend_list)

        if not rec_df.empty:
            fig14 = px.histogram(
                rec_df, x="Recommended_Target_Group",
                title=f"Euclidean Merge Recommendation for {smallest_group} (Q-13)",
                labels={"Recommended_Target_Group": "Suggested Target Group"},
                color_discrete_sequence=["#ff7f0e"]
            )
            st.plotly_chart(apply_modern_layout(fig14), use_container_width=True)

            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-13)</div>
                <p class="insight-text">• الخوارزمية وزّعت طلاب {smallest_group} إقليدياً على المجموعات الكبرى حسب القرب الأكاديمي.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• اعتماد الدمج المقترح لضمان تجانس مستوى الطلاب بعد الدمج.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات كافية لحساب المسافة الإقليدية.")

    with c20:
        # حساب مؤشر الخطورة المركّب
        stud_abs = (attendance.groupby("student_id")["is_present"]
                    .mean().reset_index())
        stud_abs["absence_rate"] = 1 - stud_abs["is_present"]

        stud_eng_c = engagement.groupby("student_id").size().reset_index(name="total_eng")
        mx_e, mn_e = stud_eng_c["total_eng"].max(), stud_eng_c["total_eng"].min()
        stud_eng_c["low_eng_score"] = 1 - ((stud_eng_c["total_eng"] - mn_e) / (mx_e - mn_e + 1e-5))

        stud_fc = concepts.groupby("student_id")["is_failed"].sum().reset_index(name="failed_concepts")
        mx_f = stud_fc["failed_concepts"].max() if not stud_fc.empty else 1
        stud_fc["failed_concepts_score"] = stud_fc["failed_concepts"] / mx_f

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

        fig15 = px.bar(
            top10, x="risk_score", y="full_name", orientation="h",
            title="Top 10 At-Risk Students – Immediate Intervention (Q-14)",
            labels={"risk_score": "Risk Severity Score (%)", "full_name": "Student Name"},
            text="risk_score",
            color="risk_score", color_continuous_scale="Reds"
        )
        fig15.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(apply_modern_layout(fig15), use_container_width=True)

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-14)</div>
            <p class="insight-text">• نظام الأوزان الهجين فرز أعلى 10 طلاب مهددين بالرسوب أو الانسحاب الفوري.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• إسناد هذه القائمة لقسم الرعاية الأكاديمية فوراً لتقديم دعم مكثف قبل الاختبارات.</p>
        </div>""", unsafe_allow_html=True)
