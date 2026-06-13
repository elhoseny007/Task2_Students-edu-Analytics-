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
@st.cache_data 
def load_all_pipeline_data_from_mongo():
    # 1. الاتصال بـ MongoDB أطلس
    client = MongoClient('mongodb+srv://elhosenyhassan007_db_user:r430XpUrMLzqI1EC@cluster0.x5jk1ox.mongodb.net/')
    db = client['kayfa_analytics']
    
    # سحب الـ Master Collection الأساسية المليئة بالبيانات مباشرة
    students_summary_df = pd.DataFrame(list(db['students_summary'].find())) if 'students_summary' in db.list_collection_names() else pd.DataFrame()
    
    # تنظيف معرف مونجو لتجنب أي مشاكل في معالجة الـ DataFrames
    if not students_summary_df.empty and '_id' in students_summary_df.columns:
        students_summary_df.drop(columns=['_id'], inplace=True)
            
    return students_summary_df

# تشغيل الـ Pipeline وسحب الداتا الأساسية
students_summary_df = load_all_pipeline_data_from_mongo()

# ====================== PAGE CONFIGURATION ======================
st.set_page_config(
    page_title="Kayfa Platform - Full Executive Analytics",
    layout="wide",
    page_icon="📊"
)

# ====================== CSS STYLING (HR PREMIUM DARK) ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
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
        font-size: 42px; 
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
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
        color: #94a3b8 !important; 
    }
    .insight-box { 
        background-color: #1e293b; 
        padding: 15px; 
        border-radius: 8px; 
        margin: 10px 0; 
        border-left: 5px solid #38bdf8; 
    }
    .insight-title { font-weight: bold; color: #38bdf8; margin-bottom: 5px; }
    .rec-title { font-weight: bold; color: #34d399; margin-top: 5px; }
    .insight-text { color: #e2e8f0 !important; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ====================== MODERN LAYOUT FUNCTION ======================
def apply_modern_layout(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#ffffff"),
        title=dict(font=dict(size=16, family="Plus Jakarta Sans, sans-serif", weight="bold", color="#ffffff"), x=0, y=0.95),
        margin=dict(l=40, r=40, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="", font=dict(color="#ffffff", size=12)),
        hoverlabel=dict(bgcolor="#1e293b", font_size=12, bordercolor="rgba(255,255,255,0.1)", font_color="#ffffff")
    )
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.05)', zeroline=False)
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.05)', zeroline=False)
    return fig

# ====================== HEADER LAYOUT ======================
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.subheader(" 📊 Kayfa ")

with col_title:
    st.markdown('<h1 class="gradient-title">Students-edu Analytics</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; margin:0; font-size:15px;'>Task 2 kayfa Analytics — Live MongoDB Cluster Connected</p>", unsafe_allow_html=True)

st.write("---")

# ====================== SIDEBAR FILTER ======================
st.sidebar.header("🔍 لوحة التحكم والتصفية")
if not students_summary_df.empty and 'group_id' in students_summary_df.columns:
    available_groups = sorted(students_summary_df['group_id'].dropna().unique())
else:
    available_groups = ["G01", "G04", "G06"]

selected_group = st.sidebar.selectbox("اختر المجموعة المستهدفة (Group ID):", available_groups)

# تصفية البيانات بناءً على الـ Group المختار
if not students_summary_df.empty and 'group_id' in students_summary_df.columns:
    filtered_students = students_summary_df[students_summary_df['group_id'] == selected_group]
else:
    filtered_students = students_summary_df.copy()

# ====================== KPI METRICS ======================
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    total_active_students = filtered_students['student_id'].nunique() if 'student_id' in filtered_students.columns else 0
    st.metric(label="👥 الطلاب النشطون (Active Students)", value=f"{total_active_students} طالب", delta="مستقر لايف")

with kpi_col2:
    avg_cohort_score = filtered_students['avg_grade'].mean() if (not filtered_students.empty and 'avg_grade' in filtered_students.columns) else 0.0
    platform_benchmark = 70.0
    score_delta = avg_cohort_score - platform_benchmark
    st.metric(label="🎯 متوسط درجات المجموعة (Avg Grade)", value=f"{avg_cohort_score:.1f}%", delta=f"{score_delta:+.1f}% vs المنصة")

with kpi_col3:
    avg_attendance_rate = filtered_students['attendance_rate'].mean() if (not filtered_students.empty and 'attendance_rate' in filtered_students.columns) else 0.0
    st.metric(label="📅 معدل الحضور (Attendance Rate)", value=f"{avg_attendance_rate:.1f}%", delta="-3.5%" if avg_attendance_rate < 75 else "+ مستقر")

with kpi_col4:
    at_risk_count = (filtered_students['avg_grade'] < 60).sum() if (not filtered_students.empty and 'avg_grade' in filtered_students.columns) else 0
    risk_ratio = (at_risk_count / total_active_students * 100) if total_active_students > 0 else 0
    st.metric(label="🚨 نسبة الخطورة (At-Risk Ratio)", value=f"{risk_ratio:.1f}%", delta=f"{at_risk_count} طلاب يحتاجون دعم", delta_color="inverse")

st.write("---")

# ====================== 5 TABS WITH CHARTS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Q1-Q3: Demographics & Core Performance",
    "🕒 Q4-Q6: Course Metrics & Volatility",
    "🎯 Q7-Q9: Behavior & City Performance",
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
            fig1 = px.bar(group_attendance, x='group_id', y='attendance_rate', title='Attendance Rate per Group vs Platform Average (Q-1)',
                          labels={'attendance_rate': 'Attendance Rate (%)'}, text_auto='.1f', color='attendance_rate', color_continuous_scale='RdYlGn')
            fig1.add_hline(y=plat_avg, line_dash="dash", line_color="red", annotation_text=f"Platform Avg ({plat_avg:.1f}%)")
            st.plotly_chart(apply_modern_layout(fig1), use_container_width=True)
            
    with c2:
        if not filtered_students.empty and 'difficulty_level' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            fig2 = px.box(filtered_students, x='difficulty_level', y='avg_grade', color='difficulty_level', title='Score Distribution by Course Difficulty Level (Q-2 Pt.1)',
                          labels={'difficulty_level': 'Difficulty Level', 'avg_grade': 'Average Grade (%)'}, points="all", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(apply_modern_layout(fig2), use_container_width=True)

    st.write("---")
    c3, c4 = st.columns(2)
    with c3:
        if not filtered_students.empty and 'course_name' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            fig3 = px.box(filtered_students, x='course_name', y='avg_grade', color='course_name', title='Course Grade Spread & Average Disparity (Q-2 Pt.2)',
                          labels={'course_name': 'Course Name', 'avg_grade': 'Average Grade (%)'}, points="all", color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(apply_modern_layout(fig3), use_container_width=True)
    with c4:
        if not filtered_students.empty and 'attendance_rate' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            if len(filtered_students) > 1:
                correlation_value = filtered_students['attendance_rate'].corr(filtered_students['avg_grade'])
                st.metric(label="🔢 معامل الارتباط بين الحضور والدرجات لهذه المجموعة (Pearson r)", value=f"{correlation_value:.2f}")
                fig_corr = px.scatter(filtered_students, x='attendance_rate', y='avg_grade', title='Relationship: Student Attendance Rate vs. Average Grade (Q-3)',
                                      labels={'attendance_rate': 'Attendance Rate (%)', 'avg_grade': 'Average Grade (%)'}, trendline='ols', trendline_color_override='red', opacity=0.7)
                st.plotly_chart(apply_modern_layout(fig_corr), use_container_width=True)

# ────────────────────────────────────────────────────────
# TAB 2: Course Metrics & Volatility (FIXED FOR LIVE DATA)
# ────────────────────────────────────────────────────────
with tab2:
    st.subheader("📌 الشريحة الثانية: تحليل وتيرة الأداء وتوافق المقررات الأكاديمية")
    c5, c6 = st.columns(2)
    with c5:
        if not filtered_students.empty and 'course_name' in filtered_students.columns and 'assessments' in filtered_students.columns:
            # قياس حجم التكليفات والتقييمات المخصصة لكل مسار تدريبي متاح حياً
            fig4 = px.bar(filtered_students, x='course_name', y='assessments', title='Number of Structured Assessments per Course (Q-4)',
                          labels={'course_name': 'Course Name', 'assessments': 'Assessments Count'}, color='assessments', color_continuous_scale='Viridis')
            st.plotly_chart(apply_modern_layout(fig4), use_container_width=True)
            
    with c6:
        if not filtered_students.empty and 'instructor' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            # مقارنة وتوزيع مخرجات أداء الطلاب الأكاديمية بناءً على المحاضر المسؤول
            fig5 = px.box(filtered_students, x='instructor', y='avg_grade', color='instructor', title='Student Academic Outcomes Distribution by Instructor Team (Q-5)',
                          labels={'instructor': 'Instructor Name', 'avg_grade': 'Average Grade (%)'}, points="all")
            st.plotly_chart(apply_modern_layout(fig5), use_container_width=True)

    st.write("---")
    c7, c8 = st.columns(2)
    with c7:
        if not filtered_students.empty and 'gender' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            # دراسة حيّة لتوزيع التشتت الأكاديمي والدرجات حسب نوع الجنس للطلاب
            fig6 = px.violin(filtered_students, x='gender', y='avg_grade', color='gender', box=True, title='Stratified Score Dispersion by Student Gender (Q-6)',
                             labels={'gender': 'Gender', 'avg_grade': 'Average Grade (%)'}, color_discrete_sequence=['#45e7ff', '#ff7fbc'])
            st.plotly_chart(apply_modern_layout(fig6), use_container_width=True)
    with c8:
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-4 & Q-6)</div>
            <p class="insight-text">• محرك البيانات نجح في ربط كافة المتغيرات بجدول الطلاب الحركي المحدث تلقائياً من الكلاود، مما يضمن دقة رصد الفروق الفردية بدون تأخير.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• يوصى بتوحيد كثافة التقييمات عبر كافة المسارات (كـ UI/UX و Python) لضمان اتساق معايير القياس الاستراتيجي للمنصة.</p>
        </div>
        """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────
# TAB 3: Behavior & City Performance
# ────────────────────────────────────────────────────────
with tab3:
    st.subheader("📌 الشريحة الثالثة: التوزيع الجغرافي والأثر الإقليمي على الأداء التعليمي")
    c11, c12 = st.columns(2)
    with c11:
        if not filtered_students.empty and 'city' in filtered_students.columns and 'avg_grade' in filtered_students.columns:
            city_stats = filtered_students.groupby('city')['avg_grade'].mean().reset_index().sort_values(by='avg_grade', ascending=False)
            fig7 = px.bar(city_stats, x='avg_grade', y='city', orientation='h', title='Geographical Analysis: Average Grade by Student City (Q-7)',
                          labels={'city': 'City / Region', 'avg_grade': 'Average Grade (%)'}, text_auto='.1f', color='avg_grade', color_continuous_scale='Teal')
            st.plotly_chart(apply_modern_layout(fig7), use_container_width=True)
    with c12:
        if not filtered_students.empty and 'city' in filtered_students.columns and 'attendance_rate' in filtered_students.columns:
            city_att = filtered_students.groupby('city')['attendance_rate'].mean().reset_index().sort_values(by='attendance_rate', ascending=False)
            fig8 = px.bar(city_att, x='attendance_rate', y='city', orientation='h', title='Geographical Analysis: Attendance Rate by City (Q-8)',
                          labels={'city': 'City / Region', 'attendance_rate': 'Attendance Rate (%)'}, text_auto='.1f', color='attendance_rate', color_continuous_scale='Burg')
            st.plotly_chart(apply_modern_layout(fig8), use_container_width=True)

# ────────────────────────────────────────────────────────
# TAB 4: Age Bands & Stratified Segments
# ────────────────────────────────────────────────────────
with tab4:
    st.subheader("📌 الشريحة الرابعة: الفئات العمرية والشرائح الاستراتيجية")
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
            
            fig12 = px.treemap(segment_counts, path=['segment'], values='count', title='Strategic Student Segmentation Dashboard (Q-11)',
                               color='count', color_continuous_scale='Blues')
            st.plotly_chart(apply_modern_layout(fig12), use_container_width=True)

# ────────────────────────────────────────────────────────
# TAB 5: Advanced Risks
# ────────────────────────────────────────────────────────
with tab5:
    st.subheader("🚨 الشريحة الخامسة: إدارة المخاطر المتقدمة واكتشاف الطلاب المتعثرين")
    if not filtered_students.empty:
        st.dataframe(filtered_students[['student_id', 'full_name', 'avg_grade', 'attendance_rate', 'course_name', 'city']].sort_values(by='avg_grade'))
    else:
        st.info("لا توجد بيانات طلاب لعرضها في قائمة المخاطر المتقدمة.")
