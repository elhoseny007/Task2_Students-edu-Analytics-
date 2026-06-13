import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pymongo import MongoClient
import json
import os

# ====================== 1. PAGE CONFIG ======================
st.set_page_config(
    page_title="Kayfa Platform - Full Executive Analytics",
    layout="wide",
    page_icon="📊"
)

# ====================== 2. CSS STYLING ======================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .stApp, .stMarkdown, .stMetric, h1, h2, h3, h4, p, label { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid rgba(255, 255, 255, 0.05); }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p { color: #cbd5e1 !important; }
    .gradient-title {
        font-size: 44px; font-weight: 900;
        background: linear-gradient(90deg, #45e7ff, #7f8cff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent !important;
        margin: 10px 0; display: inline-block;
    }
    .insight-box { background-color: #1e293b; padding: 16px; border-radius: 10px; border-left: 5px solid #45e7ff; margin: 12px 0; }
    .insight-title { color: #45e7ff !important; font-weight: bold; font-size: 16px; margin-bottom: 6px; }
    .rec-title { color: #7f8cff !important; font-weight: bold; font-size: 15px; margin-top: 8px; }
    .insight-text { color: #e2e8f0 !important; font-size: 14px; margin: 2px 0; }
</style>
""", unsafe_allow_html=True)

# ====================== 3. MODERN LAYOUT FUNCTION ======================
def apply_modern_layout(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#ffffff"),
        title=dict(font=dict(size=16, weight="bold", color="#ffffff"), x=0, y=0.95),
        margin=dict(l=40, r=40, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#ffffff", size=12)),
        hoverlabel=dict(bgcolor="#1e293b", font_size=12, font_color="#ffffff")
    )
    return fig

# ====================== 4. DATA LOADING FROM MONGO (آمن ومحصن) ======================
@st.cache_data(ttl=300)
def load_all_pipeline_data():
    try:
        # ربط مع وضع مهلة اتصال لمنع التعليق اللانهائي للشاشة
        client = MongoClient(
            'mongodb+srv://elhosenyhassan007_db_user:r430XpUrMLzqI1EC@cluster0.x5jk1ox.mongodb.net/',
            serverSelectionTimeoutMS=5000
        )
        db = client['kayfa_analytics']
        client.server_info() # اختبار الاتصال فورا
    except Exception as e:
        st.error(f"❌ تعذر الاتصال بـ MongoDB. يرجى تفعيل 'Allow Access from Anywhere (0.0.0.0/0)' في شبكة أطلس. التفاصيل: {e}")
        st.stop()

    # سحب المجموعات وتنظيف المعرفات
    def get_clean_df(col_name):
        df = pd.DataFrame(list(db[col_name].find()))
        if not df.empty and '_id' in df.columns:
            df.drop(columns=['_id'], inplace=True)
        return df

    students = get_clean_df('students')
    groups = get_clean_df('groups')
    concepts = get_clean_df('concepts_performance')
    engagement = get_clean_df('engagement_events')
    submissions = get_clean_df('assignment_submissions')
    attendance_raw = get_clean_df('attendance')

    if students.empty:
        st.error("⚠️ لم يتم العثور على بيانات في كولكشن الطلاب بمونجو!")
        st.stop()

    # معالجة وتوحيد الأسماء
    students.columns = students.columns.str.strip().str.lower()
    groups.columns = groups.columns.str.strip().str.lower()
    concepts.columns = concepts.columns.str.strip().str.lower()
    engagement.columns = engagement.columns.str.strip().str.lower()
    submissions.columns = submissions.columns.str.strip().str.lower()

    if 'group' in students.columns and 'group_id' not in students.columns:
        students.rename(columns={'group': 'group_id'}, inplace=True)

    # فك درجات الـ JSON من المونجو
    grades_raw = list(db['grades'].find())
    if grades_raw:
        grades = pd.json_normalize(grades_raw, record_path='grades', meta=['student_id', 'course_id', 'group_id'])
        grades.columns = grades.columns.str.strip().str.lower()
    else:
        grades = pd.DataFrame(columns=['student_id', 'course_id', 'group_id', 'score', 'max_score', 'type', 'date'])

    # بناء الـ Pipeline الحركي في الذاكرة
    merged_df = pd.merge(students, groups, on='group_id', how='left', suffixes=('_student', '_group'))
    final_df = pd.merge(merged_df, grades, on='student_id', how='left', suffixes=('', '_grades'))
    
    # تنظيف درجات وأعمار حرج
    if 'score' in final_df.columns:
        final_df.dropna(subset=['score'], inplace=True)
        if 'max_score' not in final_df.columns: final_df['max_score'] = 100.0
        final_df['score'] = pd.to_numeric(final_df['score'], errors='coerce').fillna(0)
        final_df['max_score'] = pd.to_numeric(final_df['max_score'], errors='coerce').fillna(100)
        final_df['score'] = final_df['score'].clip(0, final_df['max_score'])
    else:
        final_df['score'] = 75.0
        final_df['max_score'] = 100.0

    if 'age' in final_df.columns:
        final_df['age'] = pd.to_numeric(final_df['age'], errors='coerce').abs()
        final_df = final_df[final_df['age'] <= 50]

    if 'date' in final_df.columns:
        final_df['date'] = pd.to_datetime(final_df['date'], errors='coerce')

    # تنظيف الحضور
    if not attendance_raw.empty:
        attendance_raw.columns = attendance_raw.columns.str.strip().str.lower()
        if 'status' in attendance_raw.columns:
            attendance_raw['is_present'] = attendance_raw['status'].astype(str).str.strip().str.lower().apply(
                lambda x: 1 if 'attend' in x or 'present' in x or '1' in x or 'yes' in x else 0
            )
    else:
        attendance_raw = pd.DataFrame(columns=['student_id', 'group_id', 'status', 'is_present'])

    # تنظيف التواريخ والتسليمات
    if not submissions.empty and 'submitted_at' in submissions.columns:
        submissions['submitted_at'] = pd.to_datetime(submissions['submitted_at'], errors='coerce')
        submissions['submission_week'] = submissions['submitted_at'].dt.isocalendar().week
    else:
        submissions['submission_week'] = 1

    if not engagement.empty and 'event_datetime' in engagement.columns:
        engagement['event_datetime'] = pd.to_datetime(engagement['event_datetime'], errors='coerce')
        engagement['engagement_week'] = engagement['event_datetime'].dt.isocalendar().week
    else:
        engagement['engagement_week'] = 1

    return final_df, attendance_raw, concepts, engagement, submissions, groups, students

final_analysis_df, attendance, concepts, engagement, submissions, groups, students = load_all_pipeline_data()

# ====================== 5. HEADER LAYOUT ======================
st.markdown('<h1 class="gradient-title">📊 Students-edu Analytics (Kayfa Platform)</h1>', unsafe_allow_html=True)
st.markdown("<p style='color:#bae6fd; margin:0; font-weight:bold;'>Full Executive Data Infrastructure - Direct MongoDB Stream</p>", unsafe_allow_html=True)
st.write("---")

# ====================== 6. SIDEBAR FILTER ======================
st.sidebar.header("🔍 لوحة التحكم والتصفية")
available_groups = sorted(final_analysis_df['group_id'].dropna().unique()) if not final_analysis_df.empty else ["G01"]
selected_group = st.sidebar.selectbox("اختر المجموعة المستهدفة (Group ID):", available_groups)

# تصفية حية بناء على خيار المستخدم
filtered_final = final_analysis_df[final_analysis_df['group_id'] == selected_group].copy()

# ====================== 7. HIGH LEVEL EXECUTIVE KPIs ======================
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    total_active_students = filtered_final['student_id'].nunique() if not filtered_final.empty else 0
    st.metric(label="👥 الطلاب النشطون (Active Students)", value=f"{total_active_students} طالب")

with kpi_col2:
    avg_cohort_score = filtered_final['score'].mean() if not filtered_final.empty else 0.0
    score_delta = avg_cohort_score - 70.0
    st.metric(label="🎯 متوسط درجات المجموعة", value=f"{avg_cohort_score:.1f}%", delta=f"{score_delta:+.1f}% vs المنصة")

with kpi_col3:
    cohort_att_rate = 0.0
    if not attendance.empty and not filtered_final.empty:
        group_studs = filtered_final['student_id'].unique()
        filtered_attendance = attendance[attendance['student_id'].isin(group_studs)]
        if not filtered_attendance.empty:
            cohort_att_rate = filtered_attendance['is_present'].mean() * 100
    st.metric(label="📅 معدل الحضور (Attendance Rate)", value=f"{cohort_att_rate:.1f}%")

with kpi_col4:
    at_risk_count = 0
    if not filtered_final.empty:
        student_perf_check = filtered_final.groupby('student_id')['score'].mean()
        at_risk_count = (student_perf_check < 60).sum()
    risk_ratio = (at_risk_count / total_active_students * 100) if total_active_students > 0 else 0
    st.metric(label="🚨 نسبة الخطورة (At-Risk)", value=f"{risk_ratio:.1f}%", delta=f"{at_risk_count} طلاب للخطر", delta_color="inverse")

st.write("---")

# ====================== 8. THE 5 EXPANSIVE TABS (15 CHARTS) ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Q1-Q3: Demographics & Core Performance",
    "🕒 Q4-Q6: Submissions & Device Trends",
    "🎯 Q7-Q9: Behavior & Lateness Impact",
    "📊 Q10-Q12: Age Bands & Stratified Segments",
    "🚨 Q13-Q15: Advanced Risks & Group Merging"
])

# ────────────────────────────────────────────────────────
# TAB 1: Core Performance (Q1, Q2, Q3)
# ────────────────────────────────────────────────────────
with tab1:
    st.subheader("📌 الشريحة الأولى: تحليلات الحضور، توزيع الدرجات، وعوامل السن الأكاديمية")
    c1, c2 = st.columns(2)
    with c1:
        if not attendance.empty and 'group_id' in attendance.columns:
            group_attendance = attendance.groupby('group_id')['is_present'].mean().reset_index()
            group_attendance['attendance_rate'] = group_attendance['is_present'] * 100
            plat_avg = group_attendance['attendance_rate'].mean()
            
            fig1 = px.bar(group_attendance, x='group_id', y='attendance_rate',
                          title='Attendance Rate per Group vs Platform Average (Q-1)',
                          labels={'attendance_rate': 'Attendance Rate (%)'}, text_auto='.1f',
                          color='attendance_rate', color_continuous_scale='RdYlGn')
            fig1.add_hline(y=plat_avg, line_dash="dash", line_color="red", annotation_text=f"Platform Avg ({plat_avg:.1f}%)")
            st.plotly_chart(apply_modern_layout(fig1), use_container_width=True)
        
        st.markdown("""<div class="insight-box"><div class="insight-title">💡 Insight (Q-1)</div><p class="insight-text">• يظهر تباين الحضور واضحاً بين المجموعات؛ مما يؤثر بشكل فوري على مخرجات الاستيعاب للمناهج.</p></div>""", unsafe_allow_html=True)

    with c2:
        if 'type' in filtered_final.columns and not filtered_final.empty:
            fig2 = px.box(filtered_final, x='type', y='score', color='type',
                          title='Score Volatility by Assessment Type (Q-2 Pt.1)', points="all")
            st.plotly_chart(apply_modern_layout(fig2), use_container_width=True)
        else:
            st.info("لم نجد عمود 'type' لتقييم الامتحانات في البيانات الحالية.")

    st.write("---")
    c3, c4 = st.columns(2)
    with c3:
        if 'course_name' in filtered_final.columns and not filtered_final.empty:
            fig3 = px.box(filtered_final, x='course_name', y='score', color='course_name',
                          title='Course Grade Spread & Disparity (Q-2 Pt.2)', points="all")
            st.plotly_chart(apply_modern_layout(fig3), use_container_width=True)

    with c4:
        if not attendance.empty and not filtered_final.empty:
            student_grades = filtered_final.groupby('student_id')['score'].mean().reset_index(name='avg_score')
            student_att_rate = attendance.groupby('student_id')['is_present'].mean().reset_index(name='attendance_rate')
            student_att_rate['attendance_rate'] *= 100
            att_grade_corr_df = pd.merge(student_grades, student_att_rate, on='student_id', how='inner')
            
            if len(att_grade_corr_df) > 1:
                correlation_value = att_grade_corr_df['attendance_rate'].corr(att_grade_corr_df['avg_score'])
                st.metric(label="🔢 معامل الارتباط بين الحضور والدرجات (Pearson r)", value=f"{correlation_value:.2f}")
                
                fig_corr = px.scatter(att_grade_corr_df, x='attendance_rate', y='avg_score',
                                      title='Relationship: Student Attendance Rate vs. Average Grade (Q-3)',
                                      color='avg_score', opacity=0.7)
                st.plotly_chart(apply_modern_layout(fig_corr), use_container_width=True)

# ────────────────────────────────────────────────────────
# TAB 2: Submissions & Device Trends (Q4, Q5, Q6)
# ────────────────────────────────────────────────────────
with tab2:
    st.subheader("📌 الشريحة الثانية: تتبع وتيرة التسليمات وتفاعل الأجهزة الذكية")
    c5, c6 = st.columns(2)
    with c5:
        if not submissions.empty and 'submission_week' in submissions.columns:
            sub_trends = submissions.groupby(['course_id', 'submission_week']).size().reset_index(name='total_submissions')
            fig4 = px.line(sub_trends, x='submission_week', y='total_submissions', color='course_id',
                           title='Assignment Submission Trends Across Calendar Weeks (Q-4)', markers=True)
            st.plotly_chart(apply_modern_layout(fig4), use_container_width=True)

    with c6:
        if not engagement.empty and 'engagement_week' in engagement.columns:
            weekly_eng = engagement.groupby('engagement_week').size().reset_index(name='total_events')
            fig5 = px.line(weekly_eng, x='engagement_week', y='total_events',
                           title='Total Engagement Events Across Weeks (Mid-Course Slump Testing) (Q-5)', markers=True)
            fig5.update_traces(line_color='purple')
            st.plotly_chart(apply_modern_layout(fig5), use_container_width=True)

    st.write("---")
    c7, c8 = st.columns(2)
    with c7:
        if not engagement.empty and 'device' in engagement.columns and not filtered_final.empty:
            student_device = engagement.groupby('student_id')['device'].agg(lambda x: x.mode()[0] if len(x)>0 else None).reset_index()
            student_device.columns = ['student_id', 'primary_device']
            device_perf = pd.merge(filtered_final, student_device, on='student_id', how='inner')
            if not device_perf.empty and 'primary_device' in device_perf.columns:
                fig6 = px.box(device_perf, x='primary_device', y='score', color='primary_device',
                              title='Academic Performance Distribution Across Device Types (Q-6)')
                st.plotly_chart(apply_modern_layout(fig6), use_container_width=True)
    with c8:
        if not filtered_final.empty and not engagement.empty:
            stud_perf = filtered_final.groupby('student_id')['score'].mean().reset_index(name='avg_score')
            stud_eng = engagement.groupby('student_id').size().reset_index(name='total_engagement_events')
            eng_perf_df = pd.merge(stud_perf, stud_eng, on='student_id', how='inner')
            if len(eng_perf_df) > 1:
                fig_eng_rel = px.scatter(eng_perf_df, x='total_engagement_events', y='avg_score',
                                         title='Does Platform Engagement Relate to Academic Performance?', color='avg_score')
                st.plotly_chart(apply_modern_layout(fig_eng_rel), use_container_width=True)

# ────────────────────────────────────────────────────────
# TAB 3: Behavior & Lateness Impact (Q7, Q8, Q9)
# ────────────────────────────────────────────────────────
with tab3:
    st.subheader("📌 الشريحة الثالثة: سلوكيات التأخير، الوقت المستغرق والمفاهيم الأكاديمية الأصعب")
    c11, c12 = st.columns(2)
    with c11:
        if not submissions.empty and all(col in submissions.columns for col in ['time_spent_minutes', 'attempts']):
            fig7 = px.scatter(submissions, x='time_spent_minutes', y='attempts',
                              title='Assignment Time Spent vs. Number of Attempts (Q-7 Pt.1)', opacity=0.6)
            st.plotly_chart(apply_modern_layout(fig7), use_container_width=True)

    with c12:
        if not submissions.empty and 'is_late' in submissions.columns:
            fig8 = px.box(submissions, x='is_late', y='time_spent_minutes', color='is_late',
                          title='Time Spent: On-Time vs. Late Submissions (Q-7 Pt.2)')
            st.plotly_chart(apply_modern_layout(fig8), use_container_width=True)

    st.write("---")
    c13, c14 = st.columns(2)
    with c13:
        if not concepts.empty and 'score_pct' in concepts.columns:
            concept_stats = concepts.groupby('concept_name')['score_pct'].mean().reset_index().sort_values(by='score_pct')
            fig9 = px.bar(concept_stats, x='score_pct', y='concept_name', orientation='h',
                          title='Average Student Performance per Academic Concept (Q-8)', color='score_pct', color_continuous_scale='Reds_r')
            st.plotly_chart(apply_modern_layout(fig9), use_container_width=True)

    with c14:
        if not submissions.empty and not filtered_final.empty:
            student_lateness = submissions.groupby('student_id')['is_late'].mean().reset_index()
            student_lateness.columns = ['student_id', 'late_rate']
            student_lateness['submission_behavior'] = student_lateness['late_rate'].apply(lambda x: 'Habitually Late (>30%)' if x > 0.3 else 'Mostly On-Time')
            late_perf_df = pd.merge(filtered_final, student_lateness, on='student_id', how='inner')
            if not late_perf_df.empty:
                fig10 = px.violin(late_perf_df, x='submission_behavior', y='score', color='submission_behavior', box=True,
                                  title='Overall Score Distribution: On-Time vs. Habitually Late (Q-9)')
                st.plotly_chart(apply_modern_layout(fig10), use_container_width=True)

# ────────────────────────────────────────────────────────
# TAB 4: Age Bands & Stratified Segments (Q10, Q11, Q12)
# ────────────────────────────────────────────────────────
with tab4:
    st.subheader("📌 الشريحة الرابعة: الفئات العمرية والشرائح الاستراتيجية ومطابقة أعداد المجموعات")
    c15, c16 = st.columns(2)
    with c15:
        if 'age' in students.columns and not filtered_final.empty:
            student_scores = final_analysis_df.groupby('student_id')['score'].mean().reset_index(name='avg_score')
            age_df = students[['student_id', 'age']].drop_duplicates().merge(student_scores, on='student_id', how='inner')
            age_df['age_band'] = pd.cut(age_df['age'], bins=[0, 22, 26, 100], labels=['Under 22', '22-26', 'Above 26'], right=False)
            age_band_stats = age_df.groupby('age_band', observed=False)['avg_score'].mean().reset_index()
            fig11 = px.bar(age_band_stats, x='age_band', y='avg_score', title='Impact of Age Bands on Outcomes (Q-10)', color='age_band')
            st.plotly_chart(apply_modern_layout(fig11), use_container_width=True)

    with c16:
        if not filtered_final.empty and not concepts.empty:
            student_scores = filtered_final.groupby('student_id')['score'].mean().reset_index(name='avg_score')
            concepts['is_failed'] = concepts['score_pct'] < 50
            student_fails = concepts.groupby('student_id')['is_failed'].sum().reset_index(name='failed_concepts_count')
            
            seg_df = students[['student_id']].drop_duplicates().merge(student_scores, on='student_id', how='inner')
            seg_df = pd.merge(seg_df, student_fails, on='student_id', how='left').fillna(0)
            
            def assign_segment(row):
                if row['avg_score'] >= 75 and row['failed_concepts_count'] == 0: return 'High-Achievers 🌟'
                elif row['avg_score'] < 60: return 'Disengaged At-Risk 🚨'
                else: return 'Average Learners 📈'
                
            seg_df['student_segment'] = seg_df.apply(assign_segment, axis=1)
            summary_stats = seg_df.groupby('student_segment', observed=False).size().reset_index(name='student_count')
            fig12 = px.pie(summary_stats, names='student_segment', values='student_count', title='Strategic Student Profiling (Q-11)', hole=0.4)
            st.plotly_chart(apply_modern_layout(fig12), use_container_width=True)

    st.write("---")
    c17, c18 = st.columns(2)
    with c17:
        if not students.empty and not groups.empty:
            actual_sizes = students.groupby('group_id').size().reset_index(name='actual_student_count')
            stated_col = 'stated_num_students' if 'stated_num_students' in groups.columns else ('num_students' if 'num_students' in groups.columns else groups.columns[0])
            group_meta = groups[['group_id', stated_col]].drop_duplicates()
            discrepancy_df = pd.merge(group_meta, actual_sizes, on='group_id', how='left').fillna(0)
            
            fig13 = px.bar(discrepancy_df, x='group_id', y='actual_student_count', title='Actual Student Counts per Group (Q-12)', text_auto=True)
            st.plotly_chart(apply_modern_layout(fig13), use_container_width=True)
    with c18:
        st.info("📊 تعتمد لوحة البيانات الحالية على جرد حركي مباشر ومقارنة البيانات بين الكولكشنز المختلفة في مونجو للتأكد من نزاهة وسرعة البنية التحتية التعليمية.")

# ────────────────────────────────────────────────────────
# TAB 5: Advanced Risks & Group Merging (Q13, Q14, Q15)
# ────────────────────────────────────────────────────────
with tab5:
    st.subheader("📌 الشريحة الخامسة: خوارزميات الدمج الذكي ونظام التدخل المبكر للمخاطر")
    c19, c20 = st.columns(2)
    with c19:
        if not concepts.empty and not students.empty:
            student_concept_matrix = concepts.pivot_table(index='student_id', columns='concept_name', values='score_pct', aggfunc='mean').fillna(0)
            student_groups_lookup = students[['student_id', 'group_id']].drop_duplicates().set_index('student_id')
            matrix_with_groups = student_concept_matrix.join(student_groups_lookup, how='inner')
            
            actual_sizes_raw = students.groupby('group_id').size().reset_index(name='size')
            if not actual_sizes_raw.empty and not matrix_with_groups.empty:
                smallest_group = actual_sizes_raw.sort_values(by='size').iloc[0]['group_id']
                small_grp_studs = matrix_with_groups[matrix_with_groups['group_id'] == smallest_group].drop(columns=['group_id'])
                other_studs = matrix_with_groups[matrix_with_groups['group_id'] != smallest_group]
                
                recommend_list = []
                for s_id, s_profile in small_grp_studs.iterrows():
                    min_dist = float('inf')
                    target_g = "G01"
                    for other_id, other_row in other_studs.iterrows():
                        dist = np.linalg.norm(s_profile.values - other_row.drop('group_id').values)
                        if dist < min_dist:
                            min_dist = dist
                            target_g = other_row['group_id']
                    recommend_list.append({'Recommended_Target_Group': target_g})
                
                recommendations_df = pd.DataFrame(recommend_list)
                if not recommendations_df.empty:
                    fig14 = px.histogram(recommendations_df, x='Recommended_Target_Group',
                                         title=f'Euclidean Recommendation: Where to Merge {smallest_group} (Q-13)', color_discrete_sequence=['#ff7f0e'])
                    st.plotly_chart(apply_modern_layout(fig14), use_container_width=True)

    with c20:
        if not attendance.empty and not concepts.empty:
            student_att_abs = attendance.groupby('student_id')['is_present'].mean().reset_index()
            student_att_abs['absence_rate'] = 1 - student_att_abs['is_present']
            
            concepts['is_failed'] = concepts['score_pct'] < 50
            student_fails_cnt = concepts.groupby('student_id')['is_failed'].sum().reset_index(name='failed_concepts')
            
            risk_base = students[['student_id', 'full_name']].drop_duplicates()
            risk_base = pd.merge(risk_base, student_att_abs, on='student_id', how='left')
            risk_base = pd.merge(risk_base, student_fails_cnt, on='student_id', how='left').fillna(0)
            
            risk_base['risk_score'] = (risk_base['absence_rate'] * 0.5 + (risk_base['failed_concepts'] / max(risk_base['failed_concepts'].max(), 1)) * 0.5) * 100
            top_10_risk = risk_base.sort_values(by='risk_score', ascending=False).head(10)
            
            if not top_10_risk.empty:
                fig15 = px.bar(top_10_risk, x='risk_score', y='full_name', orientation='h',
                               title='Top 10 At-Risk Students Requiring Immediate Intervention (Q-14)', color='risk_score', color_continuous_scale='Reds')
                st.plotly_chart(apply_modern_layout(fig15), use_container_width=True)

st.success("✅ تم تحديث النظام بالكامل وربطه بـ MongoDB Atlas بنجاح استراتيجي صلب!")
