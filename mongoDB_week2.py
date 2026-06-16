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

# 1. إعداد الصفحة (يجب أن يكون أول أمر لـ Streamlit)
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
    
    /* اختياري: لو حابب برضه تخلي العنوان الصغير اللي فوقه أبيض واضح */
    [data-testid="stMetricLabel"] p {
        color: #cbd5e1 !important;
    }
</style>
""", unsafe_allow_html=True)

# ====================== YOUR UPDATED MODERN LAYOUT FUNCTION ======================
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
    st.markdown("<p style='color:#bae6fd; margin:0;'>Task 2 kayfa Analytics - Internship Program</p>", unsafe_allow_html=True)

st.write("---")

# ====================== DATA LOADING & PIPELINE ======================
@st.cache_resource(show_spinner="🔗 جاري الاتصال بـ MongoDB ...")
def get_mongo_collection():
    # إنشاء الاتصال بالـ URI الخاص بك
    client = MongoClient("mongodb+srv://elhosenyhassan007_db_user:r430XpUrMLzqI1EC@cluster0.x5jk1ox.mongodb.net/")
    db = client["kayfa_analytics"]
    collection = db["grades"]
    return collection, client
@st.cache_data
def load_all_pipeline_data():
    courses = pd.read_csv(r'd:\Desktop\Data Analysis\Internship\courses.csv')
    groups = pd.read_csv(r'd:\Desktop\Data Analysis\Internship\groups.csv')
    students = pd.read_csv(r"d:\Desktop\Data Analysis\Internship\students.csv")
    concepts = pd.read_csv(r'd:\Desktop\Data Analysis\Internship\concepts_performance.csv')
    engagement = pd.read_csv(r'd:\Desktop\Data Analysis\Internship\engagement_events.csv')
    submissions = pd.read_csv(r'd:\Desktop\Data Analysis\Internship\assignment_submissions.csv')
    collection, client = get_mongo_collection()

    raw_grades = list(collection.find({}, {"_id": 0}))

    if raw_grades and "grades" in raw_grades[0]:
        grades = pd.json_normalize(raw_grades[0], record_path=["grades"], meta=["student_id", "course_id", "group_id"])
    else:
        try:
            grades = pd.json_normalize(raw_grades, record_path=["grades"], meta=["student_id", "course_id", "group_id"])
        except Exception:
            grades = pd.DataFrame(raw_grades)

    # Attendance Excel
    excel_file = pd.ExcelFile(r'd:\Desktop\Data Analysis\Internship\attendance.xlsx')
    sheets_dfs = [pd.read_excel(excel_file, sheet_name=sheet) for sheet in excel_file.sheet_names]
    attendance = pd.concat(sheets_dfs, ignore_index=True)

    # دمج وتنظيف البيانات حياً لبناء الـ final_analysis_df
    merged_df = pd.merge(students, groups, on='group_id', how='left', suffixes=('_student', '_group'))
    merged_df = pd.merge(merged_df, courses, on='course_id', how='left')
    final_df = pd.merge(merged_df, grades, on='student_id', how='left', suffixes=('', '_grades'))
    
    final_df.dropna(subset=['score'], inplace=True)
    final_df['age'] = final_df['age'].abs()
    final_df = final_df[final_df['age'] <= 50]
    final_df.loc[final_df['score'] < 0, 'score'] = 0
    over_score_mask = final_df['score'] > final_df['max_score']
    final_df.loc[over_score_mask, 'score'] = final_df.loc[over_score_mask, 'max_score']
    final_df['date'] = pd.to_datetime(final_df['date'])

    attendance['status_clean'] = attendance['status'].astype(str).str.strip().str.lower()
    attendance['is_present'] = attendance['status_clean'].apply(lambda x: 1 if 'attend' in x or 'present' in x else 0)
    submissions['submitted_at'] = pd.to_datetime(submissions['submitted_at'])
    if 'event_datetime' in engagement.columns:
        engagement['event_datetime'] = pd.to_datetime(engagement['event_datetime'])

    return final_df, attendance, concepts, engagement, submissions, groups, students

final_analysis_df, attendance, concepts, engagement, submissions, groups, students = load_all_pipeline_data()

# ====================== SIDEBAR FILTER ======================
st.sidebar.header("🔍 Control Panel & Filtering")
available_groups = sorted(final_analysis_df['group_id'].unique())
selected_group = st.sidebar.selectbox("Select Target Group (Group ID):", available_groups)

with st.sidebar:
    st.image(r"Kayfa_logo.png", width=160)

# Filter data dynamically in memory for the selected group
filtered_final = final_analysis_df[final_analysis_df['group_id'] == selected_group]

# KPI Columns
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    total_active_students = filtered_final['student_id'].nunique()
    st.metric(
        label="👥 Active Students", 
        value=f"{total_active_students}",
        delta="Stable"
    )

with kpi_col2:
    avg_cohort_score = filtered_final['score'].mean() if not filtered_final.empty else 0.0
    platform_benchmark = 70.0
    score_delta = avg_cohort_score - platform_benchmark
    st.metric(
        label="🎯 Avg Grade", 
        value=f"{avg_cohort_score:.1f}%",
        delta=f"{score_delta:+.1f}% vs Platform"
    )

with kpi_col3:
    group_studs = filtered_final['student_id'].unique()
    filtered_attendance = attendance[attendance['student_id'].isin(group_studs)]
    
    if not filtered_attendance.empty:
        cohort_att_rate = filtered_attendance['is_present'].mean() * 100
    else:
        cohort_att_rate = 0.0
        
    st.metric(
        label="📅 Attendance Rate", 
        value=f"{cohort_att_rate:.1f}%",
        delta="-2.1%" if cohort_att_rate < 75 else "+ OK"
    )

with kpi_col4:
    student_perf_check = filtered_final.groupby('student_id')['score'].mean()
    at_risk_count = (student_perf_check < 60).sum() if not student_perf_check.empty else 0
    risk_ratio = (at_risk_count / total_active_students * 100) if total_active_students > 0 else 0
    
    st.metric(
        label="🚨 At-Risk Ratio", 
        value=f"{risk_ratio:.1f}%",
        delta=f"{at_risk_count} Students need support",
        delta_color="inverse"
    )

st.write("---")

# ====================== 5 TABS WITH 15 CHARTS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Q1-Q3: Demographics & Core Performance",
    "🕒 Q4-Q6: Submissions & Device Trends",
    "🎯 Q7-Q9: Behavior & Lateness Impact",
    "📊 Q10-Q12: Age Bands & Stratified Segments",
    "🚨 Q13-Q15: Advanced Risks & Group Merging"
])

# ────────────────────────────────────────────────────────
# TAB 1: Demographics & Core Performance (Q1, Q2, Q3)
# ────────────────────────────────────────────────────────
with tab1:
    st.subheader("📌 Section 1: Attendance Analytics, Grade Distribution, and Academic Age Factors")
    c1, c2 = st.columns(2)
    with c1:
        group_attendance = attendance.groupby('group_id')['is_present'].mean().reset_index()
        group_attendance['attendance_rate'] = group_attendance['is_present'] * 100
        plat_avg = group_attendance['attendance_rate'].mean()
        
        fig1 = px.bar(group_attendance, x='group_id', y='attendance_rate',
                      title='Attendance Rate per Group with Platform Average (Q-1)',
                      labels={'attendance_rate': 'Attendance Rate (%)'}, text_auto='.1f',
                      color='attendance_rate', color_continuous_scale='RdYlGn')
        fig1.add_hline(y=plat_avg, line_dash="dash", line_color="red", annotation_text=f"Platform Avg ({plat_avg:.1f}%)")
        fig1 = apply_modern_layout(fig1)
        fig1.update_xaxes(title_text="Group ID")
        fig1.update_yaxes(title_text="Attendance Rate (%)")
        st.plotly_chart(fig1, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
        <div class="insight-title">💡 Insight (Q-1)</div>
        <p class="insight-text">• A clear variance is visible across groups, with some dropping significantly below the overall platform average benchmark (Red Line).</p>
        <div class="rec-title">🚀 Recommendation</div>
        <p class="insight-text">• Conduct an immediate verbal review of low-attendance groups, and cross-reference them with instructor schedules to address low engagement.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        fig2 = px.box(
            filtered_final, 
            x='type', 
            y='score', 
            color='type',
            title='Score Distribution by Assessment',
            labels={'type': 'Assessment Type', 'score': 'Score (%)'},
            points="all",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig2 = apply_modern_layout(fig2)
        st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
        <div class="insight-title">💡 Insight (Q-2 Pt.1)</div>
        <p class="insight-text">• The score distribution across various assessments reveals high volatility (spread) with notable lower tails, indicating sudden drops/failures in certain complex tasks.</p>
        <div class="rec-title">🚀 Recommendation</div>
        <p class="insight-text">• Review the design and framing of assessments with high variance, and provide targeted support sessions prior to major examinations.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c3, c4 = st.columns(2)
    
with c3:

    fig3 = px.box(
        final_analysis_df, 
        x='course_name',
        y='score',
        color='course_name',
        title='Course Grade Spread & Average Disparity (Q-2 Pt.2)',
        labels={'course_name': 'Course Name', 'score': 'Score (%)'},
        points="all",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig3.update_layout(
        margin=dict(t=150),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="", font=dict(color="#ffffff", size=12)),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#ffffff"),
        title=dict(font=dict(size=16, family="Arial, sans-serif", weight="bold", color="#ffffff"), x=0, y=0.95),
        hoverlabel=dict(bgcolor="#1e293b", font_size=12, font_family="Inter, sans-serif", bordercolor="rgba(255,255,255,0.1)", font_color="#ffffff")
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("""
    <div class="insight-box">
        <div class="insight-title">💡 Insight (Q-2 Pt.2)</div>
        <p class="insight-text">• Average grades vary significantly across different courses, indicating the presence of challenging modules with lower average scores and high volatility.</p>
        <div class="rec-title">🚀 Recommendation</div>
        <p class="insight-text">• Standardize grading criteria across all modules and provide additional remedial/compensatory content for bottleneck courses.</p>
    </div>
    """, unsafe_allow_html=True)
        
    with c4:
        student_grades = filtered_final.groupby('student_id')['score'].mean().reset_index(name='avg_score')
        student_att_rate = attendance.groupby('student_id')['is_present'].mean().reset_index(name='attendance_rate')
        student_att_rate['attendance_rate'] *= 100
        
        att_grade_corr_df = pd.merge(student_grades, student_att_rate, on='student_id', how='inner')
        
        if not att_grade_corr_df.empty and len(att_grade_corr_df) > 1:
            correlation_value = att_grade_corr_df['attendance_rate'].corr(att_grade_corr_df['avg_score'])
            st.metric(label="Attendance & Grades Correlation (Pearson r)", value=f"{correlation_value:.2f}")
            
            fig_corr = px.scatter(
                att_grade_corr_df,
                x='attendance_rate',
                y='avg_score',
                title='Attendance Rate with Average Grade',
                labels={'attendance_rate': 'Attendance Rate (%)', 'avg_score': 'Average Grade (%)'},
                trendline='ols',
                trendline_color_override='red',
                opacity=0.7
            )
            fig_corr = apply_modern_layout(fig_corr)
            st.plotly_chart(fig_corr, use_container_width=True)
            
            st.markdown(f"""
                    <div class="insight-box">
                    <div class="insight-title">💡 Insight (Q-3)</div>
                    <p class="insight-text">• The current correlation coefficient is ({correlation_value:.2f}), statistically proving the strong positive impact of attendance rates on improving final student grades.</p>
                    <div class="rec-title">🚀 Recommendation</div>
                    <p class="insight-text">• Activate an automated warning or restriction protocol for students as soon as their attendance drops to prevent academic failure.</p>
                </div>
                """, unsafe_allow_html=True)
# ────────────────────────────────────────────────────────
# TAB 2: Submissions & Device Trends (Q4, Q5, Q6)
# ────────────────────────────────────────────────────────
with tab2:
    st.subheader("📌 Section 2: Submission Patterns & Smart Device Engagement Tracking")
    c5, c6 = st.columns(2)
    
    with c5:
        submissions['submission_week'] = submissions['submitted_at'].dt.isocalendar().week
        sub_trends = submissions.groupby(['course_id', 'submission_week']).size().reset_index(name='total_submissions')
        
        fig4 = px.line(sub_trends, x='submission_week', y='total_submissions', color='course_id',
                       title='Assignment Submission Trends Across Calendar Weeks (Q-4)',
                       labels={'submission_week': 'Calendar Week', 'total_submissions': 'Submissions Count'}, markers=True)
        fig4.update_layout(xaxis_type='category')
        st.plotly_chart(apply_modern_layout(fig4), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-4)</div>
            <p class="insight-text">• Submission frequency reveals specific spikes (peaks) followed by sharp drops in the subsequent weeks, highlighting a lack of consistent engagement.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Distribute submission deadlines evenly across the month rather than clustering them into a single week to prevent student burnout.</p>
        </div>
        """, unsafe_allow_html=True)

    with c6:
        # --- 1. Clean & Prepare Engagement Metrics Per Student ---
        # Calculate login frequency per student
        student_logins = engagement[engagement['event_type'] == 'login'].groupby('student_id').size().reset_index(name='login_count')

        # Filter video watch time from negative values or outliers (less than 2 hours)
        valid_videos = engagement[
            (engagement['event_type'] == 'video_watch') & 
            (engagement['duration_seconds'] > 0) & 
            (engagement['duration_seconds'] < 7200)
        ]

        # Calculate total watch time per student and convert to minutes
        student_video_time = valid_videos.groupby('student_id')['duration_seconds'].sum().reset_index(name='total_watch_time_mins')
        student_video_time['total_watch_time_mins'] = student_video_time['total_watch_time_mins'] / 60

        # Merge engagement metrics together for all students
        student_engagement = pd.merge(student_logins, student_video_time, on='student_id', how='outer').fillna(0)

        student_grades = final_analysis_df.groupby('student_id')['score'].mean().reset_index(name='average_grade')

        correlation_df = pd.merge(student_engagement, student_grades, on='student_id', how='inner')

        corr_logins = correlation_df['login_count'].corr(correlation_df['average_grade'])
        corr_video = correlation_df['total_watch_time_mins'].corr(correlation_df['average_grade'])


        # --- 4. Build and Display Visualizations ---
        st.subheader("Engagement vs Academic Performance Analysis")
        
        # Display correlation strength as metrics inside the container
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric(label="Logins vs Grades Correlation", value=f"{corr_logins:.2f}")
        with metric_col2:
            st.metric(label="Watch Time vs Grades Correlation", value=f"{corr_video:.2f}")

        # إنشاء تبويبات لعرض الرسمتين في نفس المكان
        plot_tab1, plot_tab2 = st.tabs(["🔑 Logins Analysis", "📺 Watch Time Analysis"])
        
        with plot_tab1:
            # الرسمة البيانية الخاصة بالـ Logins (الجديدة)
            fig_logins = px.scatter(
                correlation_df, 
                x='login_count', 
                y='average_grade',
                title='Link Strength: Total Platform Logins vs Academic Performance',
                labels={'login_count': 'Total Logins Count', 'average_grade': 'Average Grade'},
                trendline="ols", 
                trendline_color_override="red"
            )
            fig_logins.update_traces(marker=dict(size=6, color='darkblue', opacity=0.6))
            
            # حل مشكلة تداخل العناوين
            fig_logins.update_layout(margin=dict(t=100))
            st.plotly_chart(apply_modern_layout(fig_logins) if 'apply_modern_layout' in globals() else fig_logins, use_container_width=True)

        with plot_tab2:
            # الرسمة البيانية الخاصة بالـ Watch Time (القديمة)
            fig5 = px.scatter(
                correlation_df, 
                x='total_watch_time_mins', 
                y='average_grade',
                title='Link Strength: Total Video-Watch Time vs Academic Performance (Q-Engagement)',
                labels={'total_watch_time_mins': 'Total Watch Time (Minutes)', 'average_grade': 'Average Grade'},
                trendline="ols", 
                trendline_color_override="red"
            )
            fig5.update_traces(marker=dict(size=6, color='purple', opacity=0.6))
            
            # حل مشكلة تداخل العناوين
            fig5.update_layout(margin=dict(t=100))
            st.plotly_chart(apply_modern_layout(fig5) if 'apply_modern_layout' in globals() else fig5, use_container_width=True)
        
        # صندوق الأفكار والتوصيات يظل ثابتاً بالأسفل لأنه يشمل تحليل التفاعل بشكل عام
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-5)</div>
            <p class="insight-text">• A notable decrease in engagement events is detected mid-course (Mid-Course Slump), which serves as a critical behavioral indicator of student boredom and loss of momentum.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Launch motivational campaigns (Gamification) or short interactive challenges during these critical weeks to re-energize digital activity.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c7, c8 = st.columns(2)
    
    with c7:
        student_device = engagement.groupby('student_id')['device'].agg(lambda x: x.mode()[0]).reset_index()
        student_device.columns = ['student_id', 'primary_device']
        device_perf = pd.merge(filtered_final, student_device, on='student_id', how='inner')
        
        if not device_perf.empty:
            fig6 = px.box(device_perf, x='primary_device', y='score', color='primary_device',
                          title='Academic Performance Distribution Across Device Types (Q-6)',
                          labels={'primary_device': 'Primary Device', 'score': 'Final Score'}, points="outliers")
            st.plotly_chart(apply_modern_layout(fig6), use_container_width=True)
            
            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-6)</div>
                <p class="insight-text">• A variance in performance spread and lower scores is visible among users of specific device categories, hinting at potential technical optimization issues within the platform application.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• Optimize the user interface and overall experience (UI/UX), ensuring full compatibility of the platform and embedded code editors with mobile screens.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No matching device data found for the current group.")
            
    with c8:
        st.success("📊 **Device & Engagement Summary:** The behavioral analysis above bridges the gap between the infrastructure of a student's digital experience and their actual academic outcomes.")
        
    c9 = st.columns(1)
    with c9[0]:
        stud_perf = filtered_final.groupby('student_id')['score'].mean().reset_index(name='avg_score')
        stud_eng = engagement.groupby('student_id').size().reset_index(name='total_engagement_events')
        eng_perf_df = pd.merge(stud_perf, stud_eng, on='student_id', how='inner')
        
        if not eng_perf_df.empty and len(eng_perf_df) > 1:
            eng_correlation = eng_perf_df['total_engagement_events'].corr(eng_perf_df['avg_score'])
            st.metric(label="🔢 Engagement Volume vs. Grades (Correlation r)", value=f"{eng_correlation:.2f}")
            
            fig_eng_rel = px.scatter(
                eng_perf_df,
                x='total_engagement_events',
                y='avg_score',
                title='Does Platform Engagement Relate to Academic Performance? (Correlation Scatter)',
                labels={'total_engagement_events': 'Total Engagement Events (Logins/Activity)', 'avg_score': 'Average Grade (%)'},
                trendline='ols',
                trendline_color_override='#7f8cff',
                opacity=0.7
            )
            fig_eng_rel = apply_modern_layout(fig_eng_rel)
            st.plotly_chart(fig_eng_rel, use_container_width=True)
            
            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Engagement Relationship)</div>
                <p class="insight-text">• A correlation value of ({eng_correlation:.2f}) proves that consistent platform browsing and tackling quick quizzes act as the primary drivers of academic stability.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• Implement a periodic push notification system tailored for inactive students to boost daily platform login rates.</p>
            </div>
            """, unsafe_allow_html=True)
# ────────────────────────────────────────────────────────
# TAB 3: Behavior & Lateness Impact (Q7, Q8, Q9)
# ────────────────────────────────────────────────────────
with tab3:
    st.subheader("📌 Section 3: Lateness Behavior, Time Investment, and Challenging Academic Concepts")
    c11, c12 = st.columns(2)
    
    with c11:
        fig7 = px.scatter(submissions, x='time_spent_minutes', y='attempts',
                          title='Assignment Time Spent vs. Number of Attempts (Q-7 Pt.1)',
                          labels={'time_spent_minutes': 'Time Spent (Minutes)', 'attempts': 'Attempts'},
                          trendline='ols', trendline_color_override='darkblue', opacity=0.5)
        st.plotly_chart(apply_modern_layout(fig7), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-7 Pt.1)</div>
            <p class="insight-text">• A positive linear relationship is visible; an increase in time spent on assignments directly correlates with a higher number of attempts, indicating that students are facing significant difficulties with specific problem sets.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Identify the specific assignments causing high attempt volumes and break them down into smaller, incremental components to reduce student friction.</p>
        </div>
        """, unsafe_allow_html=True)

    with c12:
        fig8 = px.box(submissions, x='is_late', y='time_spent_minutes', color='is_late',
                      title='Time Spent: On-Time vs. Late Submissions (Q-7 Pt.2)',
                      labels={'is_late': 'Is Late?', 'time_spent_minutes': 'Time Spent (Minutes)'},
                      color_discrete_map={True: '#ef4444', False: '#22c55e'})
        st.plotly_chart(apply_modern_layout(fig8), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-7 Pt.2)</div>
            <p class="insight-text">• Late submitters (True) record significantly less time spent working on tasks compared to on-time students. This implies that lateness stems from procrastination and rushed execution rather than task complexity.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Implement minor incremental grading penalties for late submissions, and encourage students to initiate assignments well ahead of the final deadline.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c13, c14 = st.columns(2)
    
    with c13:
        concept_stats = concepts.groupby('concept_name')['score_pct'].mean().reset_index().sort_values(by='score_pct', ascending=True)
        fig9 = px.bar(concept_stats, x='score_pct', y='concept_name', orientation='h',
                      title='Average Student Performance per Academic Concept (Q-8)',
                      labels={'concept_name': 'Concept', 'score_pct': 'Avg Score (%)'},
                      text_auto='.1f', color='score_pct', color_continuous_scale='Reds_r')
        st.plotly_chart(apply_modern_layout(fig9), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-8)</div>
            <p class="insight-text">• Precise identification of critical and complex concepts (indicated by the dark red bars at the bottom) where the majority of students achieved suboptimal scores.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Instruct the academic team to immediately review and re-teach these bottleneck concepts, and deploy additional review materials.</p>
        </div>
        """, unsafe_allow_html=True)

    with c14:
        student_lateness = submissions.groupby('student_id')['is_late'].mean().reset_index()
        student_lateness.columns = ['student_id', 'late_rate']
        student_lateness['submission_behavior'] = student_lateness['late_rate'].apply(lambda x: 'Habitually Late (>30%)' if x > 0.3 else 'Mostly On-Time')
        late_perf_df = pd.merge(filtered_final, student_lateness, on='student_id', how='inner')
        
        if not late_perf_df.empty:
            fig10 = px.violin(late_perf_df, x='submission_behavior', y='score', color='submission_behavior',
                              box=True, points="all", title='Overall Score Distribution: On-Time vs. Habitually Late (Q-9)',
                              labels={'submission_behavior': 'Behavior', 'score': 'Final Score'},
                              color_discrete_map={'Mostly On-Time': 'green', 'Habitually Late (>30%)': 'crimson'})
            st.plotly_chart(apply_modern_layout(fig10), use_container_width=True)
            
            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-9)</div>
                <p class="insight-text">• The violin plot illustrates a severe drop and a heavy concentration of lower scores within the habitually late student segment compared to their punctual peers.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• Provide early academic advising and time-management coaching to students flagged with habitual lateness behaviors.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Submission behavior data is unavailable for the current group.")
# ────────────────────────────────────────────────────────
# TAB 4: Age Bands & Stratified Segments (Q10, Q11, Q12)
# ────────────────────────────────────────────────────────
with tab4:
    st.subheader("📌 Section 4: Demographic Bands, Strategic Profiling, and Data Integrity Reconciliation")
    c15, c16 = st.columns(2)
    
    with c15:
        student_scores = final_analysis_df.groupby('student_id')['score'].mean().reset_index(name='avg_score')
        student_att = attendance.groupby('student_id')['is_present'].mean().reset_index(name='attendance_rate')
        student_att['attendance_rate'] *= 100
        student_eng = engagement.groupby('student_id').size().reset_index(name='total_engagement')
        
        age_df = students[['student_id', 'age']].drop_duplicates()
        age_df = pd.merge(age_df, student_scores, on='student_id', how='left')
        age_df = pd.merge(age_df, student_att, on='student_id', how='left')
        age_df = pd.merge(age_df, student_eng, on='student_id', how='left')
        
        age_df['age_band'] = pd.cut(age_df['age'], bins=[0, 22, 26, 100], labels=['Under 22', '22-26', 'Above 26'], right=False)
        age_band_stats = age_df.groupby('age_band', observed=False)[['avg_score', 'attendance_rate', 'total_engagement']].mean().reset_index()
        
        fig11 = make_subplots(rows=1, cols=3, subplot_titles=('Avg Score', 'Attendance %', 'Total Engagement'))
        fig11.add_trace(go.Bar(x=age_band_stats['age_band'], y=age_band_stats['avg_score'], name='Score', marker_color='teal'), row=1, col=1)
        fig11.add_trace(go.Bar(x=age_band_stats['age_band'], y=age_band_stats['attendance_rate'], name='Attendance', marker_color='coral'), row=1, col=2)
        fig11.add_trace(go.Bar(x=age_band_stats['age_band'], y=age_band_stats['total_engagement'], name='Engagement', marker_color='indigo'), row=1, col=3)
        fig11.update_layout(title_text='Impact of Age Bands on Outcomes & Engagement (Q-10)', showlegend=False, height=400)
        st.plotly_chart(apply_modern_layout(fig11), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-10)</div>
            <p class="insight-text">• Clear variance is visible in engagement and performance across demographics; younger cohorts exhibit higher digital activity and rapid platform adoption but demonstrate lower attendance consistency.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Tailor communication and student-retention strategies based on age demographics to ensure optimal academic attachment and persistent engagement.</p>
        </div>
        """, unsafe_allow_html=True)

    with c16:
        concepts['is_failed'] = concepts['score_pct'] < 50
        student_fails = concepts.groupby('student_id')['is_failed'].sum().reset_index(name='failed_concepts_count')
        
        seg_df = students[['student_id', 'group_id']].drop_duplicates()
        seg_df = pd.merge(seg_df, student_scores, on='student_id', how='left')
        seg_df = pd.merge(seg_df, student_att, on='student_id', how='left')
        seg_df = pd.merge(seg_df, student_eng, on='student_id', how='left')
        seg_df = pd.merge(seg_df, student_fails, on='student_id', how='left')
        seg_df.fillna(0, inplace=True)
        
        def assign_segment(row):
            if row['avg_score'] >= 75 and row['attendance_rate'] >= 75 and row['failed_concepts_count'] == 0: return 'High-Achievers 🌟'
            elif row['avg_score'] < 60 and row['attendance_rate'] < 50 and row['total_engagement'] > seg_df['total_engagement'].median(): return 'Struggling Despite Effort 🔄'
            elif row['avg_score'] < 60 and row['attendance_rate'] < 50: return 'Disengaged At-Risk 🚨'
            elif row['attendance_rate'] >= 75 and row['avg_score'] < 60: return 'Under-Performers ⚠️'
            else: return 'Average / Steady Learners 📈'
            
        seg_df['student_segment'] = seg_df.apply(assign_segment, axis=1)
        summary_stats = seg_df.groupby('student_segment', observed=False).size().reset_index(name='student_count')
        
        fig12 = px.pie(summary_stats, names='student_segment', values='student_count',
                       title='Strategic Student Profiling Segmentation Distribution (Q-11)',
                       hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig12.update_traces(textinfo='percent+value')
        st.plotly_chart(apply_modern_layout(fig12), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-11)</div>
            <p class="insight-text">• The chart provides clear visibility into student cohort proportions, raising an early warning regarding the size of the critical 'Disengaged At-Risk' segment vulnerable to dropouts.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Isolate the 'Struggling Despite Effort' segment for immediate targeted academic intervention, as they interact heavily with the platform but face actual comprehension gaps.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c17, c18 = st.columns(2)
    
    with c17:
        actual_sizes = students[['student_id', 'group_id']].drop_duplicates().groupby('group_id').size().reset_index(name='actual_student_count')
        stated_col = 'stated_num_students' if 'stated_num_students' in groups.columns else ('num_students' if 'num_students' in groups.columns else groups.columns[1])
        group_meta = groups[['group_id', stated_col]].drop_duplicates()
        discrepancy_df = pd.merge(group_meta, actual_sizes, on='group_id', how='left').fillna(0)
        
        df_melted = discrepancy_df.melt(id_vars=['group_id'], value_vars=[stated_col, 'actual_student_count'], var_name='Count_Type', value_name='Student_Count')
        df_melted['Count_Type'] = df_melted['Count_Type'].replace({stated_col: 'Stated (Metadata)', 'actual_student_count': 'Actual (Students File)'})
        
        fig13 = px.bar(df_melted, x='group_id', y='Student_Count', color='Count_Type', barmode='group',
                       title='Discrepancy Analysis: Stated vs. Actual Student Counts (Q-12)',
                       labels={'group_id': 'Group ID', 'Student_Count': 'Number of Students'}, text_auto=True,
                       color_discrete_map={'Stated (Metadata)': '#aec7e8', 'Actual (Students File)': '#1f77b4'})
        st.plotly_chart(apply_modern_layout(fig13), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-12)</div>
            <p class="insight-text">• The audit reveals notable data gaps and negative discrepancies between ledger records (metadata) and actual enrolled student IDs captured within the core system for specific cohorts.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Immediately update and synchronize the underlying metadata pipeline to eliminate administrative tracking bottlenecks and ensure reliable reporting.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c18:
        st.info("🔍 **Reconciliation & Record Auditing Report (Q-12):** This view ensures data pipeline integrity and cross-references source metadata to prevent misinformed structural consolidation decisions based on corrupted enrollment metrics.")
# ────────────────────────────────────────────────────────
# TAB 5: Advanced Risks & Group Merging (Q13, Q14, Q15)
# ────────────────────────────────────────────────────────
with tab5:
    st.subheader("📌 Section 5: Intelligent Cohort Consolidation Algorithms & Early Risk Intervention System")
    c19, c20 = st.columns(2)
    
    with c19:
        actual_sizes_raw = students[['student_id', 'group_id']].drop_duplicates().groupby('group_id').size().reset_index(name='size')
        smallest_group = actual_sizes_raw.sort_values(by='size').iloc[0]['group_id']
        
        student_concept_matrix = concepts.pivot_table(index='student_id', columns='concept_name', values='score_pct', aggfunc='mean').fillna(0)
        student_groups_lookup = students[['student_id', 'group_id']].drop_duplicates().set_index('student_id')
        matrix_with_groups = student_concept_matrix.join(student_groups_lookup, how='inner')
        
        small_grp_studs = matrix_with_groups[matrix_with_groups['group_id'] == smallest_group].drop(columns=['group_id'])
        other_studs = matrix_with_groups[matrix_with_groups['group_id'] != smallest_group]
        
        recommend_list = []
        for s_id, s_profile in small_grp_studs.iterrows():
            min_dist = float('inf')
            target_g = None
            for other_id, other_row in other_studs.iterrows():
                dist = np.linalg.norm(s_profile.values - other_row.drop('group_id').values)
                if dist < min_dist:
                    min_dist = dist
                    target_g = other_row['group_id']
            recommend_list.append({'Recommended_Target_Group': target_g})
            
        recommendations_df = pd.DataFrame(recommend_list)
        
        if not recommendations_df.empty:
            fig14 = px.histogram(recommendations_df, x='Recommended_Target_Group',
                                 title=f'Euclidean Recommendation: Where to Merge Students from {smallest_group} (Q-13)',
                                 labels={'Recommended_Target_Group': 'Suggested Target Group'}, color_discrete_sequence=['#ff7f0e'])
            st.plotly_chart(apply_modern_layout(fig14), use_container_width=True)
            
            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-13)</div>
                <p class="insight-text">• The algorithm analyzed the conceptual learning profiles of the smallest group and distributed them Euclideanly across larger cohorts based on intellectual proximity and academic similarity.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• Adopt the proposed consolidation structure and re-allocate students to the recommended target groups to minimize teaching pace variance and ensure alignment among new peers.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Insufficient data available to compute Euclidean distance vectors.")

    with c20:
        student_att_abs = attendance.groupby('student_id')['is_present'].mean().reset_index()
        student_att_abs['absence_rate'] = 1 - student_att_abs['is_present']
        student_eng_cnt = engagement.groupby('student_id').size().reset_index(name='total_eng')
        
        mx_eng = student_eng_cnt['total_eng'].max() if not student_eng_cnt.empty else 1
        mn_eng = student_eng_cnt['total_eng'].min() if not student_eng_cnt.empty else 0
        student_eng_cnt['low_eng_score'] = 1 - ((student_eng_cnt['total_eng'] - mn_eng) / (mx_eng - mn_eng + 1e-5))
        
        student_fails_cnt = concepts.groupby('student_id')['is_failed'].sum().reset_index(name='failed_concepts')
        mx_fails = student_fails_cnt['failed_concepts'].max() if not student_fails_cnt.empty else 1
        student_fails_cnt['failed_concepts_score'] = student_fails_cnt['failed_concepts'] / mx_fails
        
        risk_base = students[['student_id', 'full_name', 'group_id']].drop_duplicates()
        risk_base = pd.merge(risk_base, student_att_abs[['student_id', 'absence_rate']], on='student_id', how='left')
        risk_base = pd.merge(risk_base, student_eng_cnt[['student_id', 'low_eng_score', 'total_eng']], on='student_id', how='left')
        risk_base = pd.merge(risk_base, student_fails_cnt[['student_id', 'failed_concepts_score', 'failed_concepts']], on='student_id', how='left').fillna(0)
        
        risk_base['risk_score'] = ((risk_base['absence_rate'] * 0.35) + (risk_base['failed_concepts_score'] * 0.35) + (risk_base['low_eng_score'] * 0.30)) * 100
        top_10_risk = risk_base.sort_values(by='risk_score', ascending=False).head(10)
        
        fig15 = px.bar(top_10_risk, x='risk_score', y='full_name', orientation='h',
                       title='Top 10 At-Risk Students Requiring Immediate Intervention (Q-14)',
                       labels={'risk_score': 'Risk Severity Score (%)', 'full_name': 'Student Name'},
                       text='risk_score', color='risk_score', color_continuous_scale='Reds')
        fig15.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(apply_modern_layout(fig15), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-14)</div>
            <p class="insight-text">• The hybrid evaluation system successfully screened and identified the critical list of the "Top 10 Students At-Risk of Failing or Immediate Drop-out" using the weighted risk scoring matrix.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• Extract this roster immediately and route it to the platform's Academic Support Division to deploy intensive, direct guidance to rescue them ahead of upcoming exams.</p>
        </div>
        """, unsafe_allow_html=True)

    group_trends_df = final_analysis_df.copy()
    group_trends_df['date'] = pd.to_datetime(group_trends_df['date'])
    
    # Function to generate assessment_type column based on title keywords
    def categorize_assessment(title):
        title_str = str(title).lower()
        if 'quiz' in title_str: return 'Quizzes'
        elif 'assign' in title_str: return 'Assignments'
        elif 'practical' in title_str: return 'Practical Exams'
        elif 'mid' in title_str: return 'Mid Exam'
        elif 'final' in title_str: return 'Final Exam'
        else: return 'Bonus'

    # Apply function to prevent KeyError
    group_trends_df['assessment_type'] = group_trends_df['assessment_title'].apply(categorize_assessment)
    group_trends_df = group_trends_df.sort_values(by='date')

    # Calculate mean score per group based on assessment title, type, and date
    group_monthly_perf = group_trends_df.groupby(['group_id', 'assessment_title', 'assessment_type', 'date'])['score'].mean().reset_index()
    group_monthly_perf = group_monthly_perf.sort_values(by=['group_id', 'date'])

    # 🌟 NEW CODE: Calculate and Display the exact Mean Breakdown Matrix per Group 🌟
    st.markdown("### 📋 Cohort Performance Summary Matrix")
    
    # Create a structured pivot summary to get the mean of each assessment type per group
    summary_matrix = group_trends_df.pivot_table(
        index='group_id',
        columns='assessment_type',
        values='score',
        aggfunc='mean'
    ).round(1)
    
    # Ensure correct category order matching your charts
    assessment_types = ['Quizzes', 'Assignments', 'Practical Exams', 'Mid Exam', 'Final Exam', 'Bonus']
    available_cols = [col for col in assessment_types if col in summary_matrix.columns]
    summary_matrix = summary_matrix[available_cols]
    
    # Render the clean summary table inside Streamlit
    st.dataframe(summary_matrix, use_container_width=True)
    st.write("---")

    # 1️⃣ Setup subplot layout with padding spacing to prevent overlapping
    fig_segmented = make_subplots(
        rows=2, cols=3,
        subplot_titles=[f"<b>{at}</b>" for at in available_cols],
        shared_yaxes=False,  # Disabling forced sharing gives flexibility to inspect local Min/Max clearly
        horizontal_spacing=0.08, 
        vertical_spacing=0.28    
    )

    # Standardize group colors across subplots
    unique_groups = group_monthly_perf['group_id'].unique()
    colors = px.colors.qualitative.Safe # Using high-contrast, professional palette
    group_color_map = {group: colors[i % len(colors)] for i, group in enumerate(unique_groups)}

    # Distribute tracking metrics onto Subplots
    for idx, assess_type in enumerate(available_cols):
        row = (idx // 3) + 1
        col = (idx % 3) + 1
        
        type_data = group_monthly_perf[group_monthly_perf['assessment_type'] == assess_type]
        
        # 2️⃣ Dynamically calculate Min/Max lines for reference mapping
        if not type_data.empty:
            min_score = type_data['score'].min()
            max_score = type_data['score'].max()
            
            # Floor boundary guide line
            fig_segmented.add_shape(
                type="line", x0=-0.5, x1=len(type_data['assessment_title'].unique())-0.5, 
                y0=min_score, y1=min_score,
                line=dict(color="rgba(239, 85, 59, 0.4)", width=1.5, dash="dash"),
                row=row, col=col
            )
            # Ceiling peak guide line
            fig_segmented.add_shape(
                type="line", x0=-0.5, x1=len(type_data['assessment_title'].unique())-0.5, 
                y0=max_score, y1=max_score,
                line=dict(color="rgba(44, 160, 44, 0.4)", width=1.5, dash="dot"),
                row=row, col=col
            )

        for group in unique_groups:
            group_data = type_data[type_data['group_id'] == group]
            
            if not group_data.empty:
                fig_segmented.add_trace(
                    go.Scatter(
                        x=group_data['assessment_title'],
                        y=group_data['score'].round(1),
                        mode='lines+markers',
                        name=group,
                        line=dict(color=group_color_map[group], width=2.5), 
                        marker=dict(size=7, symbol='circle'),
                        # Unified hover card formatting
                        hovertemplate=f"<b>{group}</b>: %{{y}}%<extra></extra>",
                        showlegend=True if idx == 0 else False 
                    ),
                    row=row, col=col
                )
    
    #graph
    group_type_summary = group_trends_df.groupby(['group_id', 'assessment_type'])['score'].mean().reset_index()
    
    # Enforce logical horizontal sorting on the category axis
    assessment_types_order = ['Quizzes', 'Assignments', 'Practical Exams', 'Mid Exam', 'Final Exam', 'Bonus']
    group_type_summary['assessment_type'] = pd.Categorical(
        group_type_summary['assessment_type'], 
        categories=[at for at in assessment_types_order if at in group_type_summary['assessment_type'].unique()], 
        ordered=True
    )
    group_type_summary = group_type_summary.sort_values('assessment_type')

    # Construct the scatter plot tracking exactly one mean marker point per group
    fig_summary_scatter = px.scatter(
        group_type_summary,
        x='assessment_type',
        y='score',
        color='group_id',
        title='🎯 Global Cohort Overview: Mean Performance Across Assessment Categories',
        labels={'assessment_type': 'Assessment Category', 'score': 'Overall Mean Score (%)', 'group_id': 'Cohort'},
        color_discrete_sequence=px.colors.qualitative.Safe
    )

    # Style markers for clean structural visualization (No background min/max lines included)
    fig_summary_scatter.update_traces(
        marker=dict(size=14, opacity=0.85, line=dict(width=1, color='DarkSlateGrey')),
        hovertemplate="<b>Cohort:</b> %{customdata[0]}<br><b>Category:</b> %{x}<br><b>Mean Score:</b> %{y:.1f}%<extra></extra>",
        customdata=np.stack((group_type_summary['group_id'],), axis=-1)
    )

    # Clean layout tuning with corrected weight parameter for text boldness
    fig_summary_scatter.update_layout(
        height=520,
        hovermode="closest",
        xaxis=dict(gridcolor="rgba(240, 240, 240, 0.8)", tickfont=dict(size=11, weight='bold')),
        yaxis=dict(range=[0, 105], gridcolor="rgba(220, 220, 220, 0.5)", ticksuffix="%"),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )

    # Render clean chart inside your Streamlit Tab
    st.plotly_chart(apply_modern_layout(fig_summary_scatter) if 'apply_modern_layout' in globals() else fig_summary_scatter, use_container_width=True)
    st.write("---")
