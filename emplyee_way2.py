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

# 1. إعداد الصفحة (يجب أن يكون أول أمر لـ Streamlit)
st.set_page_config(
    page_title="Kayfa Platform - Full Executive Analytics",
    layout="wide",
    page_icon="📊"
)

# ====================== CSS STYLING (HR PREMIUM DARK) ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap');
    
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
    if os.path.exists("Kayfa_logo.png"):
        st.image("Kayfa_logo.png", width=150)
    else:
        st.subheader(" 📊 Kayfa ")

with col_title:
    st.markdown('<h1 class="gradient-title">Students-edu Analytics</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; margin:0; font-size:15px;'>Task 2 kayfa Analytics — Live MongoDB Cluster Connected</p>", unsafe_allow_html=True)

st.write("---")

# ====================== DATA LOADING & PIPELINE FROM MONGO ======================
@st.cache_data
def load_all_pipeline_data_from_mongo():
    client = MongoClient('mongodb+srv://elhosenyhassan007_db_user:r430XpUrMLzqI1EC@cluster0.x5jk1ox.mongodb.net/')
    db = client['kayfa_analytics']
    
    # 1. سحب البيانات من المونجو
    groups = pd.DataFrame(list(db['groups'].find()))
    students = pd.DataFrame(list(db['students'].find()))
    concepts = pd.DataFrame(list(db['concepts_performance'].find()))
    engagement = pd.DataFrame(list(db['engagement_events'].find()))
    submissions = pd.DataFrame(list(db['assignment_submissions'].find()))
    attendance = pd.DataFrame(list(db['attendance'].find()))

    raw_grades = list(db['grades'].find())
    if raw_grades and 'grades' in raw_grades[0]:
        grades = pd.json_normalize(raw_grades, record_path=["grades"], meta=["student_id", "course_id", "group_id"])
    else:
        grades = pd.DataFrame(raw_grades)
    
    # 2. تنظيف معرفات مونجو الأساسية لتفادي التداخل في التحليل
    for df in [groups, students, concepts, engagement, submissions, grades, attendance]:
        if not df.empty and '_id' in df.columns:
            df.drop(columns=['_id'], inplace=True)

    # 3. توحيد مسميات الأعمدة إلى حروف صغيرة (Lowercase) لضمان الربط السليم مع ملف الدرجات والـ Submissions
    for df in [groups, students, concepts, engagement, submissions, grades, attendance]:
        if not df.empty:
            df.columns = df.columns.str.strip().str.lower()

    # 4. 🛠️ الحل الذكي: بما أن الـ students يحتوي على بيانات الكورس والمجموعة مسبقاً، ادمج الدرجات مباشرة!
    # نقوم بعمل نسخة من طلاب لتكون أساس التحليل النهائي
    final_df = students.copy()
    
    # دمج ملف الدرجات مع جدول الطلاب الأساسي بناءً على student_id
    if not grades.empty:
        final_df = pd.merge(final_df, grades, on='student_id', how='left', suffixes=('', '_grades'))
    
    # 5. تنظيف ومعالجة القيم المتطرفة (Data Cleaning & Outliers)
    if not final_df.empty and 'score' in final_df.columns:
        final_df.dropna(subset=['score'], inplace=True)
        if 'age' in final_df.columns:
            final_df['age'] = final_df['age'].abs()
            final_df = final_df[final_df['age'] <= 50]
        
        final_df.loc[final_df['score'] < 0, 'score'] = 0
        if 'max_score' in final_df.columns:
            over_score_mask = final_df['score'] > final_df['max_score']
            final_df.loc[over_score_mask, 'score'] = final_df.loc[over_score_mask, 'max_score']
    
    if 'date' in final_df.columns:
        final_df['date'] = pd.to_datetime(final_df['date'])

    # 6. تجهيز ملفات الحضور والتفاعلات والتسليمات
    if not attendance.empty and 'status' in attendance.columns:
        attendance['status_clean'] = attendance['status'].astype(str).str.strip().str.lower()
        attendance['is_present'] = attendance['status_clean'].apply(lambda x: 1 if 'attend' in x or 'present' in x else 0)
        
    if not submissions.empty and 'submitted_at' in submissions.columns:
        submissions['submitted_at'] = pd.to_datetime(submissions['submitted_at'])
        
    if not engagement.empty and 'event_datetime' in engagement.columns:
        engagement['event_datetime'] = pd.to_datetime(engagement['event_datetime'])

    return final_df, attendance, concepts, engagement, submissions, groups, students
final_analysis_df, attendance, concepts, engagement, submissions, groups, students = load_all_pipeline_data_from_mongo()
# ====================== SIDEBAR FILTER ======================
st.sidebar.header("🔍 لوحة التحكم والتصفية")
available_groups = sorted(final_analysis_df['group_id'].dropna().unique()) if not final_analysis_df.empty else ["G01"]
selected_group = st.sidebar.selectbox("اختر المجموعة المستهدفة (Group ID):", available_groups)

with st.sidebar:
    if os.path.exists("Kayfa_logo.png"):
        st.image("Kayfa_logo.png", width=160)

# تصفية البيانات المخصصة للمجموعة المختارة حياً في الذاكرة
filtered_final = final_analysis_df[final_analysis_df['group_id'] == selected_group]

# ====================== KPI METRICS ======================
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    total_active_students = filtered_final['student_id'].nunique() if not filtered_final.empty else 0
    st.metric(
        label="👥 الطلاب النشطون (Active Students)", 
        value=f"{total_active_students} طالب",
        delta="مستقر لايف"
    )

with kpi_col2:
    avg_cohort_score = filtered_final['score'].mean() if not filtered_final.empty else 0.0
    platform_benchmark = 70.0
    score_delta = avg_cohort_score - platform_benchmark
    st.metric(
        label="🎯 متوسط درجات المجموعة (Avg Grade)", 
        value=f"{avg_cohort_score:.1f}%",
        delta=f"{score_delta:+.1f}% vs المنصة"
    )

with kpi_col3:
    group_studs = filtered_final['student_id'].unique() if not filtered_final.empty else []
    filtered_attendance = attendance[attendance['student_id'].isin(group_studs)] if not attendance.empty else pd.DataFrame()
    
    if not filtered_attendance.empty and 'is_present' in filtered_attendance.columns:
        cohort_att_rate = filtered_attendance['is_present'].mean() * 100
    else:
        cohort_att_rate = 0.0
        
    st.metric(
        label="📅 معدل الحضور (Attendance Rate)", 
        value=f"{cohort_att_rate:.1f}%",
        delta="-2.1%" if cohort_att_rate < 75 else "+ OK"
    )

with kpi_col4:
    student_perf_check = filtered_final.groupby('student_id')['score'].mean() if not filtered_final.empty else pd.Series()
    at_risk_count = (student_perf_check < 60).sum() if not student_perf_check.empty else 0
    risk_ratio = (at_risk_count / total_active_students * 100) if total_active_students > 0 else 0
    
    st.metric(
        label="🚨 نسبة الخطورة (At-Risk Ratio)", 
        value=f"{risk_ratio:.1f}%",
        delta=f"{at_risk_count} طلاب يحتاجون تدخل",
        delta_color="inverse"
    )

st.write("---")

# ====================== 5 TABS WITH ALL 15 ORIGINAL CHARTS ======================
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
    st.subheader("📌 الشريحة الأولى: تحليلات الحضور، توزيع الدرجات، وعوامل السن الأكاديمية")
    c1, c2 = st.columns(2)
    with c1:
        if not attendance.empty and 'is_present' in attendance.columns:
            group_attendance = attendance.groupby('group_id')['is_present'].mean().reset_index()
            group_attendance['attendance_rate'] = group_attendance['is_present'] * 100
            plat_avg = group_attendance['attendance_rate'].mean()
            
            fig1 = px.bar(group_attendance, x='group_id', y='attendance_rate',
                          title='Attendance Rate per Group vs Platform Average (Q-1)',
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
            <p class="insight-text">• يظهر التباين واضحاً بين المجموعات؛ حيث تسجل بعضها تراجعاً حاداً تحت خط متوسط المنصة العام (Red Line).</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• مراجعة المجموعات منخفضة الحضور فظياً، وربطها بجداول المحاضرين لمعالجة ضعف التفاعل.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        if not filtered_final.empty and 'type' in filtered_final.columns:
            fig2 = px.box(
                filtered_final, 
                x='type', 
                y='score', 
                color='type',
                title='Score Distribution & Volatility by Assessment Type (Q-2 Pt.1)',
                labels={'type': 'Assessment Type', 'score': 'Score (%)'},
                points="all",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig2 = apply_modern_layout(fig2)
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-2 Pt.1)</div>
            <p class="insight-text">• توزيع درجات المهام المختلفة يكشف عن تشتت عالي (Spread) ووجود ذيول سفلية تشير لرسوب مفاجئ في بعض التقييمات المعقدة.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• إعادة مراجعة صياغة التقييمات ذات التشتت الضخم، وتقديم جلسات دعم مخصصة قبل الاختبارات الأساسية.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c3, c4 = st.columns(2)
    
    with c3:
        if not filtered_final.empty and 'course_name' in filtered_final.columns:
            fig3 = px.box(
                filtered_final,
                x='course_name',
                y='score',
                color='course_name',
                title='Course Grade Spread & Average Disparity (Q-2 Pt.2)',
                labels={'course_name': 'Course Name', 'score': 'Score (%)'},
                points="all",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig3 = apply_modern_layout(fig3)
            st.plotly_chart(fig3, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-2 Pt.2)</div>
            <p class="insight-text">• يختلف متوسط الدرجات بشكل ملحوظ بين الكورسات، مما يشير إلى وجود مقررات صعبة ذات معدل درجات منخفض وثبات ضعيف.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توحيد معايير التصحيح بين المقررات وتزويد كورسات العنق الزجاجي (Bottleneck) بمحتوى تعويضي إضافي.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c4:
        if not filtered_final.empty and not attendance.empty:
            student_grades = filtered_final.groupby('student_id')['score'].mean().reset_index(name='avg_score')
            student_att_rate = attendance.groupby('student_id')['is_present'].mean().reset_index(name='attendance_rate')
            student_att_rate['attendance_rate'] *= 100
            
            att_grade_corr_df = pd.merge(student_grades, student_att_rate, on='student_id', how='inner')
            
            if not att_grade_corr_df.empty and len(att_grade_corr_df) > 1:
                correlation_value = att_grade_corr_df['attendance_rate'].corr(att_grade_corr_df['avg_score'])
                st.metric(label="🔢 معامل الارتباط بين الحضور والدرجات (Pearson r)", value=f"{correlation_value:.2f}")
                
                fig_corr = px.scatter(
                    att_grade_corr_df,
                    x='attendance_rate',
                    y='avg_score',
                    title='Relationship: Student Attendance Rate vs. Average Grade (Q-3)',
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
                    <p class="insight-text">• معامل الارتباط الحالي يبلغ ({correlation_value:.2f})، مما يثبت إحصائياً الأثر الطردي القوي لنسب الحضور على رفع درجات الطلاب النهائية.</p>
                    <div class="rec-title">🚀 Recommendation</div>
                    <p class="insight-text">• تفعيل خطة حظر أو تنبيه آلي للطلاب بمجرد انخفاض نسبة حضورهم تجنباً للانهيار الأكاديمي.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("لا توجد بيانات متقاطعة كافية لحساب الارتباط لهذه المجموعة.")

# ────────────────────────────────────────────────────────
# TAB 2: Submissions & Device Trends (Q4, Q5, Q6)
# ────────────────────────────────────────────────────────
with tab2:
    st.subheader("📌 الشريحة الثانية: تتبع وتيرة التسليمات وتفاعل الأجهزة الذكية")
    c5, c6 = st.columns(2)
    
    with c5:
        if not submissions.empty and 'submitted_at' in submissions.columns:
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
            <p class="insight-text">• وتيرة التسليمات تكشف عن قمم (Peaks) محددة متبوعة بانهيار مفاجئ في الأسابيع التالية، مما يوضح غياب الاستمرارية.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• توزيع الديدلاينز (Deadlines) بشكل متوازن على مدار الشهر بدلاً من تكديسها في أسبوع واحد لحماية الطلاب من الضغط.</p>
        </div>
        """, unsafe_allow_html=True)

    with c6:
        if not engagement.empty and 'event_datetime' in engagement.columns:
            engagement['engagement_week'] = engagement['event_datetime'].dt.isocalendar().week
            weekly_eng = engagement.groupby('engagement_week').size().reset_index(name='total_events')
            
            fig5 = px.line(weekly_eng, x='engagement_week', y='total_events',
                           title='Total Engagement Events Across Weeks (Mid-Course Slump Testing) (Q-5)',
                           labels={'engagement_week': 'Calendar Week', 'total_events': 'Total Events'}, markers=True)
            fig5.update_traces(line_color='purple', line_width=3)
            fig5.update_layout(xaxis_type='category')
            st.plotly_chart(apply_modern_layout(fig5), use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-5)</div>
            <p class="insight-text">• رصد انخفاض ملحوظ في أحداث التفاعل بمنتصف الكورس (Mid-Course Slump)، وهو مؤشر نفسي خطير لملل الطلاب وفقدان الحماس الشائع.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• إطلاق مسابقات تحفيزية (Gamification) أو تحديات تفاعلية قصيرة في هذه الأسابيع الحرجة لإعادة تنشيط الحركة الرقمية.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c7, c8 = st.columns(2)
    
    with c7:
        if not engagement.empty and not filtered_final.empty and 'device' in engagement.columns:
            student_device = engagement.groupby('student_id')['device'].agg(lambda x: x.mode()[0] if not x.empty else None).reset_index()
            student_device.columns = ['student_id', 'primary_device']
            device_perf = pd.merge(filtered_final, student_device, on='student_id', how='inner')
            
            if not device_perf.empty:
                fig6 = px.box(device_perf, x='primary_device', y='score', color='primary_device',
                              title='Academic Performance Distribution Across Device Types (Q-6)',
                              labels={'primary_device': 'Primary Device', 'score': 'Final Score'}, points="outliers")
                st.plotly_chart(apply_modern_layout(fig6), use_container_width=True)
            else:
                st.warning("لا توجد بيانات أجهزة مطابقة للمجموعة الحالية.")
        else:
            st.warning("عمود الأجهزة غير متوفر حالياً.")
            
    with c8:
        st.success("📊 **ملخص فحص الأجهزة والتفاعل:** يربط التحليل السلوكي أعلاه بين البنية التحتية لتجربة الطالب الرقمية ومخرجاته الأكاديمية الفعلية.")
        
    c9 = st.columns(1)
    with c9[0]:
        if not filtered_final.empty and not engagement.empty:
            stud_perf = filtered_final.groupby('student_id')['score'].mean().reset_index(name='avg_score')
            stud_eng = engagement.groupby('student_id').size().reset_index(name='total_engagement_events')
            eng_perf_df = pd.merge(stud_perf, stud_eng, on='student_id', how='inner')
            
            if not eng_perf_df.empty and len(eng_perf_df) > 1:
                eng_correlation = eng_perf_df['total_engagement_events'].corr(eng_perf_df['avg_score'])
                st.metric(label="🔢 قوة الرابط بين حجم التفاعل والدرجات (Correlation r)", value=f"{eng_correlation:.2f}")
                
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
                    <p class="insight-text">• وجود ارتباط بقيمة ({eng_correlation:.2f}) يبرهن أن تصفح المنصة المستمر وحل الأسئلة السريعة هو المحرك الرئيسي للثبات الأكاديمي.</p>
                    <div class="rec-title">🚀 Recommendation</div>
                    <p class="insight-text">• تصميم نظام دفع وإشعارات دوري (Push Notifications) حثيث للطلاب الخاملين لرفع معدلات الدخول اليومية للمنصة.</p>
                </div>
                """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────
# TAB 3: Behavior & Lateness Impact (Q7, Q8, Q9)
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
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-7 Pt.1)</div>
            <p class="insight-text">• العلاقة خطية تصاعدية؛ زيادة الوقت المهدور في الحل ترتبط طردياً بزيادة المحاولات، مما يشير لمعاناة الطلاب من صعوبة بالغة في بعض الأسئلة المحددة.</p>
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
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-7 Pt.2)</div>
            <p class="insight-text">• الطلاب المتأخرون (True) يسجلون أوقات حل أقل بكثير مقارنة بالملتزمين بالمواعيد، مما يعني أن التأخير نابع من المماطلة والحل المتسرع وليس الصعوبة.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• فرض غرامات درجات تصاعدية طفيفة على التأخير، وحث الطلاب على بدء حل التكليفات مبكراً قبل يوم التسليم النهائي.</p>
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
        
        st.markdown("""
        <div class="insight-box">
            <div class="insight-title">💡 Insight (Q-8)</div>
            <p class="insight-text">• تحديد أدق للمفاهيم الحرجة والأصعب (الفئات باللون الأحمر الداكن بالأسفل) التي سجل فيها أغلب الطلاب درجات متدنية جداً.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تووجيه فريق المحاضرين بإعادة شرح وتغطية هذه المفاهيم المتعثرة فورا وبث مسودات مراجعة إضافية لها.</p>
        </div>
        """, unsafe_allow_html=True)

    with c14:
        if not submissions.empty and not filtered_final.empty and 'is_late' in submissions.columns:
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
            else:
                st.info("بيانات سلوك التسليم غير متوفرة للمجموعة الحالية.")

# ────────────────────────────────────────────────────────
# TAB 4: Age Bands & Stratified Segments (Q10, Q11, Q12)
# ────────────────────────────────────────────────────────
with tab4:
    st.subheader("📌 الشريحة الرابعة: الفئات العمرية والشرائح الاستراتيجية ومطابقة أعداد المجموعات")
    c15, c16 = st.columns(2)
    
    with c15:
        if not final_analysis_df.empty and not attendance.empty and not engagement.empty:
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
            <p class="insight-text">• تباين واضح في التفاعل والدرجات بين الفئات العمرية؛ حيث تسجل الفئات الأصغر سنّاً تفاعلاً أعلى ورقمنة أسرع لكنها أقل التزاماً في الحضور.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تخصيص طابع وأساليب المتابعة التعليمية حسب الفئة العمرية للطلاب لضمان أعلى نسب استبقاء والتحام أكاديمي.</p>
        </div>
        """, unsafe_allow_html=True)

    with c16:
        if not concepts.empty and 'score_pct' in concepts.columns:
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
            <p class="insight-text">• يوفر المخطط الدائري رؤية واضحة لنسب توزيع شرائح الطلاب، محذراً من حجم الكتلة الحرجة المعرضة للانسحاب (Disengaged At-Risk).</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• عزل شريحة 'Struggling Despite Effort' لدعمهم أكاديمياً فوراً لأنهم يتفاعلون بكثافة ولكن يعانون في الفهم الفعلي.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    c17, c18 = st.columns(2)
    
    with c17:
        if not groups.empty and not students.empty:
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
            <p class="insight-text">• كشف التقرير عن فجوات ومطابقة سلبية واضحة بين السجلات الدفترية والأرقام الحقيقية المقيدة بالسيستم في بعض المجموعات الذكية.</p>
            <div class="rec-title">🚀 Recommendation</div>
            <p class="insight-text">• تحديث خط السير وقاعدة البيانات المرجعية للـ Metadata الخاصة بالمجموعات بشكل فوري وسد الثغرات الإدارية التابعة لها.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c18:
        st.info("🔍 **تقرير المطابقة وجرد السجلات (Q-12):** يهدف هذا التبويب لضمان نزاهة البيانات ومطابقة الملفات المصدرية لعدم اتخاذ قرارات دمج عشوائية بناءً على مؤشرات خاطئة.")

# ────────────────────────────────────────────────────────
# TAB 5: Advanced Risks & Group Merging (Q13, Q14, Q15)
# ────────────────────────────────────────────────────────
with tab5:
    st.subheader("📌 الشريحة الخامسة: خوارزميات الدمج الذكي ونظام التدخل المبكر للمخاطر")
    c19, c20 = st.columns(2)
    
    with c19:
        if not concepts.empty and not students.empty:
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
                    <p class="insight-text">• قامت الخوارزمية بتحليل الأداء المفهومي للمجموعة الأصغر وزعتهم إقليدياً على المجموعات الكبرى حسب القرب الفكري والأكاديمي المتشابه.</p>
                    <div class="rec-title">🚀 Recommendation</div>
                    <p class="insight-text">• اعتماد الدمج المقترح وتسكين الطلاب بالمجموعات المستهدفة لضمان عدم وجود تباين في الشرح والتحصيل بين الأقران الجدد.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("لا توجد بيانات كافية لحساب المسافة الإقليدية.")
        else:
            st.info("بيانات المفاهيم الأكاديمية غير متوفرة لحساب الخوارزمية.")

    with c20:
        if not attendance.empty and not engagement.empty and not concepts.empty:
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
            
            if not top_10_risk.empty:
                fig15 = px.bar(top_10_risk, x='risk_score', y='full_name', orientation='h',
                               title='Top 10 At-Risk Students Requiring Immediate Intervention (Q-14)',
                               labels={'risk_score': 'Risk Severity Score (%)', 'full_name': 'Student Name'},
                               text='risk_score', color='risk_score', color_continuous_scale='Reds')
                fig15.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(apply_modern_layout(fig15), use_container_width=True)
            
            st.markdown("""
            <div class="insight-box">
                <div class="insight-title">💡 Insight (Q-14)</div>
                <p class="insight-text">• نجح نظام التقييم الهجين في فرز وتحديد القائمة الحرجة لـ "أعلى 10 طلاب مهددين بالرسوب أو الانسحاب الفوري" بناءً على خوارزمية الأوزان.</p>
                <div class="rec-title">🚀 Recommendation</div>
                <p class="insight-text">• سحب هذه القائمة فوراً وإسنادها لقسم الرعاية الأكاديمية بالمنصة لتقديم دعم مكثف مباشر لإنقاذهم قبل الاختبارات القادمة.</p>
            </div>
            """, unsafe_allow_html=True)

if final_analysis_df.empty:
    st.warning("⚠️ لم يتم العثور على بيانات! تأكد من صحة مسارات ملفات الـ Collections على MongoDB Cluster.")
