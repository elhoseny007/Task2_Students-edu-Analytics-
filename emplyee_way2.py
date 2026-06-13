#libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import streamlit as st
import seaborn
import json
import os
import warnings
from pymongo import MongoClient

# ====================== DATA LOADING & PIPELINE FROM MONGO ======================
@st.cache_data # لمنع إعادة تحميل الداتا مع كل حركة في الداشبورد
def load_all_pipeline_data_from_mongo():
    # 1. الاتصال بـ MongoDB أطلس
    client = MongoClient('mongodb+srv://elhosenyhassan007_db_user:r430XpUrMLzqI1EC@cluster0.x5jk1ox.mongodb.net/')
    
    # 2. اسم قاعدة البيانات من الأطلس
    db = client['kayfa_analytics']
    
    # 3. سحب الـ Collections وتحويلها فوراً لـ DataFrames
    students_summary_df = pd.DataFrame(list(db['students_summary'].find())) if 'students_summary' in db.list_collection_names() else pd.DataFrame()
    attendance          = pd.DataFrame(list(db['attendance'].find())) if 'attendance' in db.list_collection_names() else pd.DataFrame()
    concepts            = pd.DataFrame(list(db['concepts'].find())) if 'concepts' in db.list_collection_names() else pd.DataFrame()
    engagement          = pd.DataFrame(list(db['engagement'].find())) if 'engagement' in db.list_collection_names() else pd.DataFrame()
    submissions         = pd.DataFrame(list(db['submissions'].find())) if 'submissions' in db.list_collection_names() else pd.DataFrame()
    groups              = pd.DataFrame(list(db['groups'].find())) if 'groups' in db.list_collection_names() else pd.DataFrame()
    
    # 4. تنظيف عمود الـ _id الخاص بمونجو لمنع التضارب في الـ Joins أو العرض
    for df in [students_summary_df, attendance, concepts, engagement, submissions, groups]:
        if df is not None and not df.empty and '_id' in df.columns:
            df.drop(columns=['_id'], inplace=True)
            
    return students_summary_df, attendance, concepts, engagement, submissions, groups

# تشغيل الـ Pipeline وسحب الداتا
students_summary_df, attendance, concepts, engagement, submissions, groups = load_all_pipeline_data_from_mongo()

# ====================== PAGE CONFIGURATION ======================
st.set_page_config(
    page_title="Kayfa Platform - Full Executive Analytics",
    layout="wide",
    page_icon="📊"
)

# ====================== CSS STYLING ======================
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117; 
    }
    
    .stApp, .stMarkdown, .stMetric, h1, h2, h3, h4, p, label, .css-1d391kg, .st-emotion-cache {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #111827 !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
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
        background-color: #1e293b;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 5px solid #38bdf8;
    }
    .insight-title {
        font-weight: bold;
        color: #38bdf8;
        margin-bottom: 5px;
    }
    .rec-title {
        font-weight: bold;
        color: #34d399;
        margin-top: 5px;
    }
    .insight-text {
        color: #e2e8f0 !important;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# ====================== MODERN LAYOUT FUNCTION ======================
def apply_modern_layout(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#ffffff"),
        title=dict(font=dict(size=16, family="Arial, sans-serif", weight="bold", color="#ffffff"), x=0, y=0.95),
        margin=dict(l=40, r=40, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="", font=dict(color="#ffffff", size=12)),
        hoverlabel=dict(bgcolor="#1e293b", font_size=12, font_family="Inter, sans-serif", bordercolor="rgba(255,255,255,0.1)", font_color="#ffffff")
    )
    return fig

# ====================== HEADER LAYOUT ======================
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists("Kayfa_logo.png"):
        st.image("Kayfa_logo.png", width=150)
    else:
        st.subheader(" 📊 Kayfa ")

with col_title:
    st.markdown('<h1 class="gradient-title">Students-edu Analytics</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#bae6fd; margin:0;'>Task 2 kayfa Analytics - MongoDB Atlas Live Sync</p>", unsafe_allow_html=True)

st.write("---")

# ====================== SIDEBAR FILTER ======================
st.sidebar.header("🔍 لوحة التحكم والتصفية")

if not students_summary_df.empty and 'group_id' in students_summary_df.columns:
    available_groups = sorted(students_summary_df['group_id'].dropna().unique())
else:
    available_groups = ["G01", "G04", "G06"]  # Fallback

selected_group = st.sidebar.selectbox("اختر المجموعة المستهدفة (Group ID):", available_groups)

if os.path.exists("Kayfa_logo.png"):
    with st.sidebar:
        st.image("Kayfa_logo.png", width=160)

# تصفية الداتا بناءً على المجموعة المختارة
if not students_summary_df.empty and 'group_id' in students_summary_df.columns:
    filtered_students = students_summary_df[students_summary_df['group_id'] == selected_group]
else:
    filtered_students = students_summary_df.copy()

# ====================== KPI METRICS ======================
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    total_active_students = filtered_students['student_id'].nunique() if 'student_id' in filtered_students.columns else 0
    st.metric(label="👥 الطلاب النشطون (Active Students)", value=f"{total_active_students} طالب", delta="مستقر على الكلاود")

with kpi_col2:
    avg_cohort_score = filtered_students['avg_grade'].mean() if (not filtered_students.empty and 'avg_grade' in filtered_students.columns) else 0.0
    platform_benchmark = 70.0
    score_delta = avg_cohort_score - platform_benchmark
    st.metric(label="🎯 متوسط درجات المجموعة (Avg Grade)", value=f"{avg_cohort_score:.1f}%", delta=f"{score_delta:+.1f}% vs المنصة")

with kpi_col3:
    avg_attendance_rate = filtered_students['attendance_rate'].mean() if (not filtered_students.empty and 'attendance_rate' in filtered_students.columns) else 0.0
    st.metric(label="📅 معدل الحضور (Attendance Rate)", value=f"{avg_attendance_rate:.1f}%", delta="-3.5%" if avg_attendance_rate < 75 else "+ مستقر")

with kpi_col4:
    at_risk_count = 0
    risk_ratio = 0.0
    if not filtered_students.empty and 'avg_grade' in filtered_students.columns:
        at_risk_count = (filtered_students['avg_grade'] < 60).sum()
        risk_ratio = (at_risk_count / total_active_students * 100) if total_active_students > 0 else 0
    st.metric(label="🚨 نسبة الخطورة (At-Risk Ratio)", value=f"{risk_ratio:.1f}%", delta=f"{at_risk_count} طلاب يحتاجون دعم", delta_color="inverse")

st.write("---")

# ====================== 5 TABS WITH CHARTS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Q1-Q3: Demographics & Core Performance",
    "🕒 Q4-Q6: Submissions & Device Trends",
    "🎯 Q7-Q9: Behavior & Lateness Impact",
    "📊 Q10-Q12: Age Bands & Stratified Segments",
    "🚨 Q13-Q15: Advanced Risks"
])

# ────────────────────────────────────────────────────────
# TAB 1: Demographics & Core Performance
# ────────────────────────────────────────────────────────
with tab1:
    st.subheader("📌 الشريحة الأولى: تحليلات الحضور وتوزيع الدرجات وعلاقتها بالمجموعات")
    c1, c2 = st.columns(2)
    
    with c1:
        if not students_summary_df.empty and 'group_id' in students_summary_df.columns and 'attendance_rate' in students_summary_df.columns:
            group_attendance = students_summary_df.groupby('group_id')['attendance_rate'].mean().reset_index()
            plat_avg = group_attendance['attendance_rate'].mean()
            
            fig1 = px.bar(group_attendance, x='group_id', y='attendance_rate',
                          title='Attendance Rate per Group vs Platform Average (Q-1)',
                          labels={'attendance_rate': 'Attendance Rate (%)'}, text_auto='.1f',
                          color='attendance_rate', color_continuous_scale='RdYlGn')
            fig1.add_hline(y=plat_avg, line_dash="dash", line_color="red", annotation_text=f"Platform Avg ({plat_avg:.1f}%)")
            st.plotly_chart(apply_modern_layout(fig1), use_container_width=True)
        else:
            st.info("بيانات الحضور غير متوفرة حالياً.")

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-1)</div>
            <p class="insight-text">• يظهر التباين واضحاً بين المجموعات؛ حيث تسجل بعض المجموعات مثل G04 تراجعاً ملحوظاً في نسب الحضور مقارنة بغيرها.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• إرسال تنبيهات تلقائية لطلاب المجموعات التي يقل حضورها عن 70% لتحفيز التفاعل قبل الجلسات القادمة.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        if not filtered_students.empty and 'difficulty_level' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            fig2 = px.box(filtered_students, x='difficulty_level', y='avg_grade', color='difficulty_level',
                          title='Score Distribution by Course Difficulty Level (Q-2 Pt.1)',
                          labels={'difficulty_level': 'Difficulty Level', 'avg_grade': 'Average Grade (%)'},
                          points="all", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(apply_modern_layout(fig2), use_container_width=True)
        else:
            st.info("بيانات مستويات الصعوبة غير متوفرة للمجموعة المحددة.")
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-2 Pt.1)</div>
            <p class="insight-text">• مستويات المبتدئين (Beginner) تظهر تشتتاً واسعاً في الدرجات، مما يعكس تفاوت الخلفيات المعرفية للطلاب عند بداية التسجيل.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توفير مواد تمهيدية (Pre-requisites) قصيرة قبل الكورس لتقليص فجوة الأداء بين الطلاب المبتدئين.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c3, c4 = st.columns(2)
    
    with c3:
        if not filtered_students.empty and 'course_name' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            fig3 = px.box(filtered_students, x='course_name', y='avg_grade', color='course_name',
                          title='Course Grade Spread & Average Disparity (Q-2 Pt.2)',
                          labels={'course_name': 'Course Name', 'avg_grade': 'Average Grade (%)'},
                          points="all", color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(apply_modern_layout(fig3), use_container_width=True)
        else:
            st.info("بيانات أسماء الكورسات غير متوفرة للمجموعة المحددة.")
            
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-2 Pt.2)</div>
            <p class="insight-text">• يختلف توزيع درجات كورس مثل Python Programming عن غيره من تخصصات التصميم، مما يبرز طبيعة التقييمات البرمجية التراكمية.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تكثيف المراجعات العملية في النصف الأول من كورسات البرمجة لتثبيت مفاهيم الأساسيات كـ Control Flow.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c4:
        if not filtered_students.empty and 'attendance_rate' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            if len(filtered_students) > 1:
                correlation_value = filtered_students['attendance_rate'].corr(filtered_students['avg_grade'])
                st.metric(label="🔢 معامل الارتباط بين الحضور والدرجات لهذه المجموعة (Pearson r)", value=f"{correlation_value:.2f}")
                
                fig_corr = px.scatter(filtered_students, x='attendance_rate', y='avg_grade',
                                      title='Relationship: Student Attendance Rate vs. Average Grade (Q-3)',
                                      labels={'attendance_rate': 'Attendance Rate (%)', 'avg_grade': 'Average Grade (%)'},
                                      trendline='ols', trendline_color_override='red', opacity=0.7)
                st.plotly_chart(apply_modern_layout(fig_corr), use_container_width=True)
        else:
            st.info("لا توجد بيانات كافية لحساب معامل الارتباط.")

# ────────────────────────────────────────────────────────
# TAB 2: Submissions & Device Trends
# ────────────────────────────────────────────────────────
with tab2:
    st.subheader("📌 الشريحة الثانية: تتبع وتيرة التسليمات وتفاعل الأجهزة الذكية")
    c5, c6 = st.columns(2)
    
    with c5:
        if not submissions.empty and 'submitted_at' in submissions.columns:
            try:
                submissions['submitted_at'] = pd.to_datetime(submissions['submitted_at'])
                submissions['submission_week'] = submissions['submitted_at'].dt.isocalendar().week
                sub_trends = submissions.groupby(['course_id', 'submission_week']).size().reset_index(name='total_submissions')
                
                fig4 = px.line(sub_trends, x='submission_week', y='total_submissions', color='course_id',
                               title='Assignment Submission Trends Across Calendar Weeks (Q-4)',
                               labels={'submission_week': 'Calendar Week', 'total_submissions': 'Submissions Count'}, markers=True)
                fig4.update_layout(xaxis_type='category')
                st.plotly_chart(apply_modern_layout(fig4), use_container_width=True)
            except Exception as e:
                st.info("🕒 جاري معالجة وتحديث أزمنة التسليمات الفرعية.")
        else:
            st.info("🕒 بيانات تسليم الواجبات (Submissions) جاري تحديثها حالياً على الكلاود.")
            
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-4)</div>
            <p class="insight-text">• وتيرة التسليمات تكشف عن قمم (Peaks) محددة متبوعة بانهيار مفاجئ في الأسابيع التالية، مما يوضح غياب الاستمرارية.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توزيع الديدلاينز (Deadlines) بشكل متوازن على مدار الشهر بدلاً من تكديسها في أسبوع واحد لحماية الطلاب من الضغط.</p>
        </div>
        """, unsafe_allow_html=True)

    with c6:
        st.markdown("#### 📱 توزيع الأجهزة وتحليلات التفاعل")
        if not engagement.empty and 'student_id' in engagement.columns and 'device' in engagement.columns:
            try:
                # تجميع لتحديد الجهاز الأساسي لكل طالب
                student_device = engagement.groupby('student_id')['device'].agg(lambda x: x.mode()[0] if not x.mode().empty else "Unknown").reset_index()
                device_counts = student_device['device'].value_counts().reset_index()
                device_counts.columns = ['device', 'count']
                
                fig6 = px.pie(device_counts, values='count', names='device',
                              title='Primary Device Usage Distribution (Q-6)',
                              hole=0.4, color_discrete_sequence=px.colors.sequential.Teal_r)
                st.plotly_chart(apply_modern_layout(fig6), use_container_width=True)
            except Exception as e:
                st.info("📱 جاري مزامنة أنماط تفاعل الأجهزة الذكية للأعضاء.")
        else:
            st.info("📱 بيانات الأجهزة (Device Trends) غير متوفرة بشكل مباشر في كوليكشن الـ engagement.")

        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-5 & Q-6)</div>
            <p class="insight-text">• معظم التفاعلات تتم عبر أجهزة الهاتف المحمول، مما يستدعي تحسين واجهات المنصة لتناسب الهواتف، مع رصد خمول تدريجي في منتصف الكورس.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تصميم وتثبيت محتوى تفاعلي خفيف (Micro-learning) يسهل تصفحه عبر الموبايل لإعادة جذب الطلاب خلال فترة الخمول.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c7, c8 = st.columns(2)
    
    with c7:
        # تم تصحيح الـ Merge بالكامل ليعتمد على كوليكشن المونجو الحالية بدلا من الجداول المفقودة القديمة
        if not engagement.empty and 'student_id' in engagement.columns and not filtered_students.empty:
            try:
                student_device = engagement.groupby('student_id')['device'].agg(lambda x: x.mode()[0] if not x.mode().empty else "Unknown").reset_index()
                student_device.columns = ['student_id', 'primary_device']
                device_perf = pd.merge(filtered_students, student_device, on='student_id', how='inner')
                
                if not device_perf.empty and 'avg_grade' in device_perf.columns:
                    fig_dev_box = px.box(device_perf, x='primary_device', y='avg_grade', color='primary_device',
                                         title='Academic Performance Distribution Across Device Types (Q-6)',
                                         labels={'primary_device': 'Primary Device', 'avg_grade': 'Average Grade (%)'}, points="outliers")
                    st.plotly_chart(apply_modern_layout(fig_dev_box), use_container_width=True)
                else:
                    st.warning("لا توجد مطابقة بيانات أجهزة كافية للمجموعة الحالية.")
            except Exception as e:
                st.info("جاري تحديث ربط الأداء بأنماط الأجهزة الفرعية.")
        else:
            st.info("لا توجد بيانات أجهزة مطابقة للمجموعة الحالية.")

    with c8:
        # رسم علاقة عدد التفاعلات الإجمالي مع أداء الطلاب الأكاديمي
        if not engagement.empty and 'student_id' in engagement.columns and not filtered_students.empty:
            try:
                stud_eng = engagement.groupby('student_id').size().reset_index(name='total_engagement_events')
                eng_perf_df = pd.merge(filtered_students, stud_eng, on='student_id', how='inner')
                
                if not eng_perf_df.empty and len(eng_perf_df) > 1 and 'avg_grade' in eng_perf_df.columns:
                    eng_correlation = eng_perf_df['total_engagement_events'].corr(eng_perf_df['avg_grade'])
                    st.metric(label="🔢 قوة الرابط بين حجم التفاعل والدرجات (Correlation r)", value=f"{eng_correlation:.2f}")
                    
                    fig_eng_rel = px.scatter(eng_perf_df, x='total_engagement_events', y='avg_grade',
                                             title='Does Platform Engagement Relate to Academic Performance?',
                                             labels={'total_engagement_events': 'Total Activity Counts', 'avg_grade': 'Average Grade (%)'},
                                             trendline='ols', trendline_color_override='#7f8cff', opacity=0.7)
                    st.plotly_chart(apply_modern_layout(fig_eng_rel), use_container_width=True)
                else:
                    st.info("📈 بيانات تفاعل الطلاب الأسبوعية (Engagement) جاري ربطها.")
            except Exception as e:
                pass

# ────────────────────────────────────────────────────────
# TAB 3: Behavior & Lateness Impact
# ────────────────────────────────────────────────────────
with tab3:
    st.subheader("📌 الشريحة الثالثة: سلوكيات التأخير، الوقت المستغرق والمفاهيم الأكاديمية الأصعب")
    c11, c12 = st.columns(2)
    
    with c11:
        if not submissions.empty and 'time_spent_minutes' in submissions.columns and 'attempts' in submissions.columns:
            fig7 = px.scatter(submissions, x='time_spent_minutes', y='attempts',
                              title='Assignment Time Spent vs. Number of Attempts (Q-7 Pt.1)',
                              labels={'time_spent_minutes': 'Time Spent (Minutes)', 'attempts': 'Attempts'},
                              trendline='ols', trendline_color_override='darkblue', opacity=0.5)
            st.plotly_chart(apply_modern_layout(fig7), use_container_width=True)
        else:
            st.info("📊 بيانات الوقت المستغرق والمحاولات (Time spent / Attempts) غير متوفرة حالياً.")
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-7 Pt.1)</div>
            <p class="insight-text">• زيادة الوقت المهدور في الحل ترتبط طردياً بزيادة المحاولات، مما يشير لمعاناة الطلاب من صعوبة بالغة في بعض الأسئلة المحددة.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• الكشف عن الواجبات المسببة لارتفاع عدد المحاولات وتقسيمها إلى أجزاء تدريجية أصغر لتخفيف الارتباك الحاصل.</p>
        </div>
        """, unsafe_allow_html=True)

    with c12:
        if not submissions.empty and 'is_late' in submissions.columns and 'time_spent_minutes' in submissions.columns:
            fig8 = px.box(submissions, x='is_late', y='time_spent_minutes', color='is_late',
                          title='Time Spent: On-Time vs. Late Submissions (Q-7 Pt.2)',
                          labels={'is_late': 'Is Late?', 'time_spent_minutes': 'Time Spent (Minutes)'},
                          color_discrete_map={True: '#ef4444', False: '#22c55e'})
            st.plotly_chart(apply_modern_layout(fig8), use_container_width=True)
        else:
            st.info("📊 بيانات مقارنة أزمنة التأخير غير متوفرة الكوليكشن.")
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-7 Pt.2)</div>
            <p class="insight-text">• الطلاب المتأخرون يسجلون أوقات حل أقل، مما يعني أن التأخير نابع من المماطلة والحل المتسرع وليس الصعوبة الفنية للواجب.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• فرض غرامات درجات تصاعدية طفيفة على التأخير، وحث الطلاب على بدء حل التكليفات مبكراً.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c13, c14 = st.columns(2)
    
    with c13:
        if not concepts.empty and 'concept_name' in concepts.columns and 'score_pct' in concepts.columns:
            concept_stats = concepts.groupby('concept_name')['score_pct'].mean().reset_index().sort_values(by='score_pct', ascending=True)
            fig9 = px.bar(concept_stats, x='score_pct', y='concept_name', orientation='h',
                          title='Average Student Performance per Academic Concept (Q-8)',
                          labels={'concept_name': 'Concept', 'score_pct': 'Avg Score (%)'},
                          text_auto='.1f', color='score_pct', color_continuous_scale='Reds_r')
            st.plotly_chart(apply_modern_layout(fig9), use_container_width=True)
        else:
            st.info("📚 كوليكشن المفاهيم (Concepts) خالية أو لا تحتوي على الأعمدة الأساسية.")
            
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-8)</div>
            <p class="insight-text">• تحديد أدق للمفاهيم الحرجة والأصعب التي سجل فيها أغلب الطلاب درجات متدنية جداً لمراجعتها.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توجيه فريق المحاضرين بإعادة شرح وتغطية هذه المفاهيم المتعثرة فورا وبث مسودات مراجعة إضافية لها.</p>
        </div>
        """, unsafe_allow_html=True)

    with c14:
        if not submissions.empty and 'student_id' in submissions.columns and 'is_late' in submissions.columns:
            student_lateness = submissions.groupby('student_id')['is_late'].mean().reset_index()
            student_lateness.columns = ['student_id', 'late_rate']
            student_lateness['submission_behavior'] = student_lateness['late_rate'].apply(lambda x: 'Habitually Late (>30%)' if x > 0.3 else 'Mostly On-Time')
            
            late_perf_df = pd.merge(filtered_students, student_lateness, on='student_id', how='inner')
            
            if not late_perf_df.empty and 'avg_grade' in late_perf_df.columns:
                fig10 = px.violin(late_perf_df, x='submission_behavior', y='avg_grade', color='submission_behavior',
                                  box=True, points="all", title='Overall Score Distribution: On-Time vs. Habitually Late (Q-9)',
                                  labels={'submission_behavior': 'Behavior', 'avg_grade': 'Final Score'},
                                  color_discrete_map={'Mostly On-Time': 'green', 'Habitually Late (>30%)': 'crimson'})
                st.plotly_chart(apply_modern_layout(fig10), use_container_width=True)
            else:
                st.info("⚠️ تعذر مطابقة سلوك التأخير مع درجات المجموعة الحالية.")
        else:
            st.info("⚠️ بيانات ربط السلوك بالدرجات غير متاحة لعدم توفر مفاتيح الربط.")

# ────────────────────────────────────────────────────────
# TAB 4: Age Bands & Stratified Segments
# ────────────────────────────────────────────────────────
with tab4:
    st.subheader("📌 الشريحة الرابعة: الفئات العمرية والشرائح الاستراتيجية ومطابقة أعداد المجموعات")
    c15, c16 = st.columns(2)
    
    with c15:
        if not filtered_students.empty and 'age' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            age_df = filtered_students.copy()
            age_df['age_band'] = pd.cut(age_df['age'], bins=[0, 22, 26, 100], labels=['Under 22', '22-26', 'Above 26'], right=False)
            age_band_stats = age_df.groupby('age_band', observed=False)[['avg_grade', 'attendance_rate']].mean().reset_index()
            
            fig11 = make_subplots(rows=1, cols=2, subplot_titles=('Avg Score %', 'Attendance Rate %'))
            fig11.add_trace(go.Bar(x=age_band_stats['age_band'], y=age_band_stats['avg_grade'], name='Score', marker_color='teal'), row=1, col=1)
            fig11.add_trace(go.Bar(x=age_band_stats['age_band'], y=age_band_stats['attendance_rate'], name='Attendance', marker_color='coral'), row=1, col=2)
            fig11.update_layout(title_text='Impact of Age Bands on Outcomes (Q-10)', showlegend=False, height=400)
            st.plotly_chart(apply_modern_layout(fig11), use_container_width=True)
        else:
            st.info("📊 بيانات توزيع الأعمار والأداء الأكاديمي غير متوفرة للمجموعة المحددة.")
            
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-10)</div>
            <p class="insight-text">• تباين واضح في التفاعل والدرجات بين الفئات العمرية؛ حيث تسجل الفئات الأكبر سنّاً نسب التزام أعلى وأكثر استقراراً في مستويات الحضور.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تخصيص طابع وأساليب المتابعة التعليمية حسب الفئة العمرية للطلاب لضمان أعلى نسب استبقاء والتحام أكاديمي.</p>
        </div>
        """, unsafe_allow_html=True)

    with c16:
        if not filtered_students.empty and 'avg_grade' in filtered_students.columns and 'attendance_rate' in filtered_students.columns:
            def assign_segment(row):
                if row['avg_grade'] >= 75 and row['attendance_rate'] >= 75: return 'High-Achievers 🌟'
                elif row['avg_grade'] < 60 and row['attendance_rate'] < 60: return 'Disengaged At-Risk 🚨'
                elif row['attendance_rate'] >= 75 and row['avg_grade'] < 60: return 'Under-Performers ⚠️'
                else: return 'Average / Steady Learners 📈'
                
            seg_df = filtered_students.copy()
            seg_df['segment'] = seg_df.apply(assign_segment, axis=1)
            segment_counts = seg_df['segment'].value_counts().reset_index()
            segment_counts.columns = ['segment', 'count']
            
            fig12 = px.treemap(segment_counts, path=['segment'], values='count',
                               title='Strategic Student Segmentation Dashboard (Q-11)',
                               color='count', color_continuous_scale='Blues')
            st.plotly_chart(apply_modern_layout(fig12), use_container_width=True)
        else:
            st.info("📊 تعذر احتساب الشرائح التعليمية لعدم توفر متغيرات الدرجات والحضور.")

# ────────────────────────────────────────────────────────
# TAB 5: Advanced Risks
# ────────────────────────────────────────────────────────
with tab5:
    st.subheader("🚨 الشريحة الخامسة: إدارة المخاطر المتقدمة واكتشاف الطلاب المتعثرين")
    if not filtered_students.empty:
        st.dataframe(filtered_students[['student_id', 'full_name', 'avg_grade', 'attendance_rate', 'course_name']].sort_values(by='avg_grade'))
    else:
        st.info("لا توجد بيانات طلاب لعرضها في قائمة المخاطر المتقدمة.")
