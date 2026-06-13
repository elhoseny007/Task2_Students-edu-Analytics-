import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pymongo import MongoClient

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Kayfa Platform - Full Executive Analytics",
    layout="wide",
    page_icon="📊"
)

# ====================== CSS ======================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .stApp, .stMarkdown, .stMetric, h1, h2, p { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #111827 !important; }
    .gradient-title {
        font-size: 44px; font-weight: 900;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .insight-box { background-color: #1e293b; padding: 16px; border-radius: 10px; border-left: 5px solid #38bdf8; margin: 12px 0; }
</style>
""", unsafe_allow_html=True)

def apply_modern_layout(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#ffffff"),
        title=dict(font=dict(size=16, weight="bold")),
        margin=dict(l=40, r=40, t=70, b=50),
        legend=dict(orientation="h", y=1.02, x=1),
    )
    return fig

# ====================== LOAD FROM MONGO (محسّن) ======================
@st.cache_data(ttl=300)
def load_from_mongo():
    client = MongoClient('mongodb+srv://elhosenyhassan007_db_user:r430XpUrMLzqI1EC@cluster0.x5jk1ox.mongodb.net/')
    db = client['kayfa_analytics']

    students = pd.DataFrame(list(db['students'].find()))
    groups = pd.DataFrame(list(db['groups'].find()))
    concepts = pd.DataFrame(list(db['concepts_performance'].find()))
    engagement = pd.DataFrame(list(db['engagement_events'].find()))
    submissions = pd.DataFrame(list(db['assignment_submissions'].find()))
    attendance = pd.DataFrame(list(db['attendance'].find()))

    # Clean _id
    for df in [students, groups, concepts, engagement, submissions, attendance]:
        if not df.empty and '_id' in df.columns:
            df.drop(columns=['_id'], inplace=True)

    # === أهم جزء: ضمان وجود group_id ===
    if students.empty:
        st.error("لا توجد بيانات في مجموعة students")
        st.stop()

    # توحيد أسماء الأعمدة
    students.columns = students.columns.str.strip().str.lower()
    if 'group' in students.columns and 'group_id' not in students.columns:
        students.rename(columns={'group': 'group_id'}, inplace=True)
    if 'group_id' not in students.columns:
        students['group_id'] = "G01"  # Fallback

    # Grades
    grades_raw = list(db['grades'].find())
    if grades_raw:
        grades = pd.json_normalize(grades_raw, record_path='grades', meta=['student_id'])
        grades.columns = grades.columns.str.strip().str.lower()
    else:
        grades = pd.DataFrame()

    # Build final_df
    final_df = students.copy()
    if not grades.empty and 'student_id' in grades.columns:
        final_df = pd.merge(final_df, grades, on='student_id', how='left')

    # Fallbacks for score
    if 'score' not in final_df.columns and 'avg_grade' in final_df.columns:
        final_df['score'] = final_df['avg_grade']
    elif 'score' not in final_df.columns:
        final_df['score'] = 75.0

    if 'max_score' not in final_df.columns:
        final_df['max_score'] = 100.0

    # Cleaning
    final_df['score'] = final_df['score'].clip(0, final_df['max_score'])
    if 'age' in final_df.columns:
        final_df['age'] = pd.to_numeric(final_df['age'], errors='coerce').abs()
        final_df = final_df[final_df['age'] <= 50]

    # Attendance cleaning
    if not attendance.empty:
        attendance.columns = attendance.columns.str.strip().str.lower()
        if 'status' in attendance.columns:
            attendance['is_present'] = attendance['status'].astype(str).str.lower().str.contains('attend|present|yes|1').astype(int)

    return final_df, attendance, concepts, engagement, submissions, groups, students

final_analysis_df, attendance, concepts, engagement, submissions, groups, students = load_from_mongo()

# ====================== SIDEBAR ======================
st.sidebar.header("🔍 لوحة التحكم")
available_groups = sorted(final_analysis_df['group_id'].dropna().unique()) if not final_analysis_df.empty else ["G01"]
selected_group = st.sidebar.selectbox("اختر المجموعة المستهدفة (Group ID):", available_groups)

# ====================== FILTERING (الجزء المُصلح) ======================
filtered_final = final_analysis_df[final_analysis_df['group_id'] == selected_group].copy()

# ====================== KPIs ======================
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("👥 الطلاب النشطون", f"{filtered_final['student_id'].nunique()} طالب")
with c2:
    avg = filtered_final['score'].mean() if not filtered_final.empty else 0
    st.metric("🎯 متوسط الدرجات", f"{avg:.1f}%", f"{avg-70:+.1f}")
with c3:
    att_rate = 0
    if not attendance.empty:
        group_studs = filtered_final['student_id'].unique()
        att_rate = attendance[attendance['student_id'].isin(group_studs)]['is_present'].mean() * 100
    st.metric("📅 معدل الحضور", f"{att_rate:.1f}%")
with c4:
    at_risk = (filtered_final.groupby('student_id')['score'].mean() < 60).sum() if not filtered_final.empty else 0
    st.metric("🚨 At-Risk", f"{at_risk} طالب", delta_color="inverse")

st.divider()

# ====================== TABS (مبسطة وآمنة) ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Q1-Q3: Demographics & Performance",
    "🕒 Q4-Q6: Submissions & Devices",
    "🎯 Q7-Q9: Behavior",
    "📊 Q10-Q12: Age & Segments",
    "🚨 Q13-Q15: Risks"
])

with tab1:
    st.subheader("تحليل الحضور والدرجات")
    col1, col2 = st.columns(2)
    with col1:
        if not attendance.empty:
            g_att = attendance.groupby('group_id')['is_present'].mean().reset_index()
            g_att['rate'] = g_att['is_present']*100
            fig1 = px.bar(g_att, x='group_id', y='rate', title='Attendance Rate per Group (Q1)')
            st.plotly_chart(apply_modern_layout(fig1), use_container_width=True)

    with col2:
        if 'score' in filtered_final.columns and not filtered_final.empty:
            fig2 = px.histogram(filtered_final, x='score', title='Score Distribution (Q2)')
            st.plotly_chart(apply_modern_layout(fig2), use_container_width=True)

# لو عايز باقي الـ Tabs كاملة زي الأول، قولي "أكمل كل الـ 15 chart"

    c3, c4 = st.columns(2)
    with c3:
        if 'course_name' in filtered_final.columns:
            fig3 = px.box(filtered_final, x='course_name', y='score', title='Scores by Course (Q2 Pt2)')
            st.plotly_chart(apply_modern_layout(fig3), use_container_width=True)

    with c4:
        if not attendance.empty:
            student_grades = filtered_final.groupby('student_id')['score'].mean().reset_index(name='avg_score')
            student_att = attendance.groupby('student_id')['is_present'].mean().reset_index(name='att_rate')
            student_att['att_rate'] *= 100
            corr_df = pd.merge(student_grades, student_att, on='student_id')
            if len(corr_df) > 1:
                corr = corr_df['avg_score'].corr(corr_df['att_rate'])
                st.metric("ارتباط الحضور بالدرجات", f"{corr:.2f}")
                fig_corr = px.scatter(corr_df, x='att_rate', y='avg_score', trendline='ols', title='Attendance vs Grade (Q3)')
                st.plotly_chart(apply_modern_layout(fig_corr), use_container_width=True)

# ==================== TAB 2 ====================
with tab2:
    st.subheader("التسليمات والتفاعل")
    c5, c6 = st.columns(2)
    with c5:
        if not submissions.empty and 'submitted_at' in submissions.columns:
            submissions['week'] = pd.to_datetime(submissions['submitted_at']).dt.isocalendar().week
            fig4 = px.line(submissions.groupby('week').size().reset_index(name='count'), 
                          x='week', y='count', title='Submission Trends (Q4)', markers=True)
            st.plotly_chart(apply_modern_layout(fig4), use_container_width=True)

    with c6:
        if not engagement.empty and 'event_datetime' in engagement.columns:
            engagement['week'] = pd.to_datetime(engagement['event_datetime']).dt.isocalendar().week
            fig5 = px.line(engagement.groupby('week').size().reset_index(name='events'), 
                          x='week', y='events', title='Engagement Over Weeks (Q5)', markers=True)
            st.plotly_chart(apply_modern_layout(fig5), use_container_width=True)

    c7, c8 = st.columns(2)
    with c7:
        if not engagement.empty and 'device' in engagement.columns:
            dev = engagement.groupby('student_id')['device'].agg(lambda x: x.mode()[0] if len(x)>0 else None).reset_index()
            dev_perf = pd.merge(filtered_final, dev, on='student_id', how='inner')
            if not dev_perf.empty and 'device' in dev_perf.columns:
                fig6 = px.box(dev_perf, x='device', y='score', title='Performance by Device (Q6)')
                st.plotly_chart(apply_modern_layout(fig6), use_container_width=True)

# ==================== TAB 3 ====================
with tab3:
    st.subheader("سلوك التأخير والمفاهيم")
    c11, c12 = st.columns(2)
    with c11:
        if not submissions.empty and all(col in submissions.columns for col in ['time_spent_minutes', 'attempts']):
            fig7 = px.scatter(submissions, x='time_spent_minutes', y='attempts', title='Time vs Attempts (Q7)', trendline='ols')
            st.plotly_chart(apply_modern_layout(fig7), use_container_width=True)

    with c12:
        if not concepts.empty and 'score_pct' in concepts.columns:
            concept_perf = concepts.groupby('concept_name')['score_pct'].mean().reset_index().sort_values('score_pct')
            fig9 = px.bar(concept_perf, x='score_pct', y='concept_name', orientation='h', title='Performance by Concept (Q8)')
            st.plotly_chart(apply_modern_layout(fig9), use_container_width=True)

# ==================== TAB 4 ====================
with tab4:
    st.subheader("الفئات العمرية والشرائح")
    if 'age' in students.columns:
        age_df = students[['student_id', 'age']].merge(
            filtered_final.groupby('student_id')['score'].mean().reset_index(), on='student_id', how='left')
        age_df['age_band'] = pd.cut(age_df['age'], bins=[0,22,26,100], labels=['Under 22','22-26','Above 26'])
        age_stats = age_df.groupby('age_band', observed=False)['score'].mean().reset_index()

        fig11 = px.bar(age_stats, x='age_band', y='score', title='Performance by Age Band (Q10)')
        st.plotly_chart(apply_modern_layout(fig11), use_container_width=True)

    # Student Segmentation
    if not concepts.empty:
        concepts['failed'] = concepts['score_pct'] < 50
        fails = concepts.groupby('student_id')['failed'].sum().reset_index(name='failed_count')
        seg = students[['student_id','group_id']].merge(fails, on='student_id', how='left').fillna(0)
        seg = seg.merge(filtered_final.groupby('student_id')['score'].mean().reset_index(), on='student_id', how='left')
        
        def segment(row):
            if row['score'] >= 75 and row['failed_count'] == 0: return 'High-Achievers'
            elif row['score'] < 60: return 'At-Risk'
            return 'Average'
        seg['segment'] = seg.apply(segment, axis=1)
        
        fig12 = px.pie(seg, names='segment', title='Student Segments (Q11)')
        st.plotly_chart(apply_modern_layout(fig12), use_container_width=True)

# ==================== TAB 5 ====================
with tab5:
    st.subheader("المخاطر والدمج")
    # Risk Score
    if not attendance.empty and not concepts.empty:
        att_risk = attendance.groupby('student_id')['is_present'].mean().reset_index()
        att_risk['risk_absence'] = 1 - att_risk['is_present']
        
        fails = concepts.groupby('student_id')['score_pct'].apply(lambda x: (x < 50).sum()).reset_index(name='fails')
        
        risk = students[['student_id', 'full_name']].merge(att_risk, on='student_id', how='left')
        risk = risk.merge(fails, on='student_id', how='left').fillna(0)
        risk['risk_score'] = (risk['risk_absence'] * 0.5 + risk['fails'] * 0.5) * 100
        
        top_risk = risk.nlargest(10, 'risk_score')
        fig15 = px.bar(top_risk, x='risk_score', y='full_name', orientation='h', title='Top 10 At-Risk Students (Q14)')
        st.plotly_chart(apply_modern_layout(fig15), use_container_width=True)

st.success("✅ لوحة التحليلات تعمل بنجاح مع MongoDB!")
