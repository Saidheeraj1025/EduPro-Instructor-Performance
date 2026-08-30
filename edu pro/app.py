import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="EduPro Instructor Performance",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# TITLE
# ============================================================

st.title("🎓 EduPro Instructor Performance & Course Quality")

st.markdown(
    """
    **Data-driven evaluation of instructor effectiveness,
    teaching experience, course quality and learner demand.**
    """
)


# ============================================================
# FILE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INSTRUCTOR_FILE = BASE_DIR / "EduPro_Instructor_Performance.csv"
EXPERTISE_FILE = BASE_DIR / "EduPro_Expertise_Analysis.csv"
PROCESSED_FILE = BASE_DIR / "EduPro_Processed_Data.csv"


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_csv(file_path):

    return pd.read_csv(file_path)


# ============================================================
# CHECK FILES
# ============================================================

missing_files = []

if not INSTRUCTOR_FILE.exists():
    missing_files.append("EduPro_Instructor_Performance.csv")

if not EXPERTISE_FILE.exists():
    missing_files.append("EduPro_Expertise_Analysis.csv")

if not PROCESSED_FILE.exists():
    missing_files.append("EduPro_Processed_Data.csv")


if missing_files:

    st.error("❌ Required files are missing.")

    st.write("Please make sure these files are in the same folder as `app.py`:")

    for file in missing_files:
        st.write(f"• {file}")

    st.stop()


# ============================================================
# READ DATA
# ============================================================

try:

    instructor = load_csv(INSTRUCTOR_FILE)
    expertise = load_csv(EXPERTISE_FILE)
    processed = load_csv(PROCESSED_FILE)

except Exception as error:

    st.error("❌ Error while loading the CSV files.")

    st.exception(error)

    st.stop()


# ============================================================
# REMOVE UNNAMED COLUMNS
# ============================================================

def clean_columns(data):

    data = data.copy()

    data.columns = (
        data.columns
        .astype(str)
        .str.strip()
    )

    unwanted = [
        column
        for column in data.columns
        if column.lower().startswith("unnamed")
    ]

    data.drop(
        columns=unwanted,
        errors="ignore",
        inplace=True
    )

    return data


instructor = clean_columns(instructor)
expertise = clean_columns(expertise)
processed = clean_columns(processed)


# ============================================================
# CONVERT NUMERIC COLUMNS
# ============================================================

def convert_numeric(data):

    data = data.copy()

    numeric_columns = [
        "Age",
        "YearsOfExperience",
        "TeacherRating",
        "CourseRating",
        "EnrollmentCount",
        "AverageCourseRating",
        "RatingConsistency",
        "ExperienceImpactScore",
        "EnrollmentInfluenceRatio"
    ]

    for column in numeric_columns:

        if column in data.columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

    return data


instructor = convert_numeric(instructor)
expertise = convert_numeric(expertise)
processed = convert_numeric(processed)


# ============================================================
# CREATE ENROLLMENT COUNT
# ============================================================

if "EnrollmentCount" not in instructor.columns:

    if "TeacherID" in processed.columns:

        enrollment = (
            processed
            .groupby("TeacherID")
            .size()
            .reset_index(name="EnrollmentCount")
        )

        instructor = instructor.merge(
            enrollment,
            on="TeacherID",
            how="left"
        )

    else:

        instructor["EnrollmentCount"] = 0


# ============================================================
# CREATE AVERAGE COURSE RATING
# ============================================================

if "AverageCourseRating" not in instructor.columns:

    if (
        "TeacherID" in processed.columns
        and "CourseRating" in processed.columns
    ):

        course_rating = (
            processed
            .groupby("TeacherID")["CourseRating"]
            .mean()
            .reset_index()
        )

        course_rating.rename(
            columns={
                "CourseRating": "AverageCourseRating"
            },
            inplace=True
        )

        instructor = instructor.merge(
            course_rating,
            on="TeacherID",
            how="left"
        )

    else:

        instructor["AverageCourseRating"] = np.nan


# ============================================================
# CREATE RATING TIER
# ============================================================

def rating_tier(rating):

    if pd.isna(rating):
        return "Not Rated"

    if rating >= 4:
        return "High"

    if rating >= 3:
        return "Medium"

    return "Low"


if "TeacherRating" in instructor.columns:

    instructor["RatingTier"] = (
        instructor["TeacherRating"]
        .apply(rating_tier)
    )


# ============================================================
# CREATE EXPERIENCE GROUP
# ============================================================

def experience_group(years):

    if pd.isna(years):
        return "Unknown"

    if years <= 2:
        return "0–2 Years"

    if years <= 5:
        return "3–5 Years"

    if years <= 10:
        return "6–10 Years"

    return "10+ Years"


if "YearsOfExperience" in instructor.columns:

    instructor["ExperienceGroup"] = (
        instructor["YearsOfExperience"]
        .apply(experience_group)
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🔎 Dashboard Filters")

st.sidebar.markdown(
    "Use the filters below to explore EduPro performance."
)


# ============================================================
# EXPERTISE FILTER
# ============================================================

if "Expertise" in instructor.columns:

    expertise_values = sorted(
        instructor["Expertise"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_expertise = st.sidebar.multiselect(
        "Instructor Expertise",
        expertise_values,
        default=expertise_values
    )

else:

    selected_expertise = []


# ============================================================
# COURSE CATEGORY FILTER
# ============================================================

if "CourseCategory" in processed.columns:

    category_values = sorted(
        processed["CourseCategory"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_category = st.sidebar.multiselect(
        "Course Category",
        category_values,
        default=category_values
    )

else:

    selected_category = []


# ============================================================
# COURSE LEVEL FILTER
# ============================================================

if "CourseLevel" in processed.columns:

    level_values = sorted(
        processed["CourseLevel"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_level = st.sidebar.multiselect(
        "Course Level",
        level_values,
        default=level_values
    )

else:

    selected_level = []


# ============================================================
# TEACHER RATING FILTER
# ============================================================

if "TeacherRating" in instructor.columns:

    rating_filter = st.sidebar.slider(
        "Teacher Rating",
        min_value=0.0,
        max_value=5.0,
        value=(0.0, 5.0),
        step=0.1
    )

else:

    rating_filter = (0.0, 5.0)


# ============================================================
# FILTER INSTRUCTOR DATA
# ============================================================

filtered_instructor = instructor.copy()

if (
    selected_expertise
    and "Expertise" in filtered_instructor.columns
):

    filtered_instructor = filtered_instructor[
        filtered_instructor["Expertise"]
        .astype(str)
        .isin(selected_expertise)
    ]


if "TeacherRating" in filtered_instructor.columns:

    filtered_instructor = filtered_instructor[
        filtered_instructor["TeacherRating"].between(
            rating_filter[0],
            rating_filter[1]
        )
    ]


# ============================================================
# FILTER PROCESSED DATA
# ============================================================

filtered_processed = processed.copy()


if (
    selected_category
    and "CourseCategory" in filtered_processed.columns
):

    filtered_processed = filtered_processed[
        filtered_processed["CourseCategory"]
        .astype(str)
        .isin(selected_category)
    ]


if (
    selected_level
    and "CourseLevel" in filtered_processed.columns
):

    filtered_processed = filtered_processed[
        filtered_processed["CourseLevel"]
        .astype(str)
        .isin(selected_level)
    ]


# ============================================================
# KPI CALCULATIONS
# ============================================================

if (
    "TeacherRating" in filtered_instructor.columns
    and not filtered_instructor.empty
):

    average_teacher_rating = (
        filtered_instructor["TeacherRating"]
        .mean()
    )

else:

    average_teacher_rating = 0


if (
    "CourseRating" in filtered_processed.columns
    and not filtered_processed.empty
):

    average_course_rating = (
        filtered_processed["CourseRating"]
        .mean()
    )

else:

    average_course_rating = 0


number_of_instructors = len(filtered_instructor)


if "EnrollmentCount" in filtered_instructor.columns:

    total_enrollments = (
        filtered_instructor["EnrollmentCount"]
        .fillna(0)
        .sum()
    )

else:

    total_enrollments = len(filtered_processed)


# ============================================================
# RATING CONSISTENCY INDEX
# ============================================================

if (
    "TeacherRating" in filtered_instructor.columns
    and len(filtered_instructor) > 1
):

    rating_mean = filtered_instructor[
        "TeacherRating"
    ].mean()

    rating_std = filtered_instructor[
        "TeacherRating"
    ].std()

    if rating_mean != 0:

        consistency_index = (
            1 - (rating_std / rating_mean)
        ) * 100

        consistency_index = max(
            0,
            min(100, consistency_index)
        )

    else:

        consistency_index = 0

else:

    consistency_index = 0


# ============================================================
# KPI DISPLAY
# ============================================================

st.subheader("📌 Key Performance Indicators")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)


with kpi1:

    st.metric(
        "Average Teacher Rating",
        f"{average_teacher_rating:.2f}"
    )


with kpi2:

    st.metric(
        "Average Course Rating",
        f"{average_course_rating:.2f}"
    )


with kpi3:

    st.metric(
        "Total Instructors",
        f"{number_of_instructors:,}"
    )


with kpi4:

    st.metric(
        "Total Enrollments",
        f"{total_enrollments:,.0f}"
    )


with kpi5:

    st.metric(
        "Rating Consistency",
        f"{consistency_index:.1f}%"
    )


st.divider()


# ============================================================
# DASHBOARD TABS
# ============================================================

overview_tab, instructor_tab, experience_tab, course_tab, expertise_tab = st.tabs(
    [
        "📊 Overview",
        "👨‍🏫 Instructor Performance",
        "📈 Experience Analysis",
        "📚 Course Quality",
        "🎯 Expertise Analysis"
    ]
)


# ============================================================
# TAB 1 — OVERVIEW
# ============================================================

with overview_tab:

    st.header("📊 Overall Platform Performance")


    chart1, chart2 = st.columns(2)


    # --------------------------------------------------------
    # TEACHER RATING DISTRIBUTION
    # --------------------------------------------------------

    with chart1:

        if "TeacherRating" in filtered_instructor.columns:

            fig = px.histogram(
                filtered_instructor,
                x="TeacherRating",
                nbins=15,
                title="Instructor Rating Distribution"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # --------------------------------------------------------
    # COURSE RATING DISTRIBUTION
    # --------------------------------------------------------

    with chart2:

        if "CourseRating" in filtered_processed.columns:

            fig = px.histogram(
                filtered_processed,
                x="CourseRating",
                nbins=15,
                title="Course Rating Distribution"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # --------------------------------------------------------
    # PERFORMANCE TIER
    # --------------------------------------------------------

    if "RatingTier" in filtered_instructor.columns:

        tier_data = (
            filtered_instructor["RatingTier"]
            .value_counts()
            .reset_index()
        )

        tier_data.columns = [
            "RatingTier",
            "Count"
        ]

        fig = px.pie(
            tier_data,
            names="RatingTier",
            values="Count",
            title="Instructor Performance Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# TAB 2 — INSTRUCTOR PERFORMANCE
# ============================================================

with instructor_tab:

    st.header("👨‍🏫 Instructor Performance Leaderboard")


    if filtered_instructor.empty:

        st.warning(
            "No instructors match the selected filters."
        )

    else:

        leaderboard_columns = []

        possible_columns = [
            "TeacherID",
            "TeacherName",
            "Age",
            "Gender",
            "Expertise",
            "YearsOfExperience",
            "TeacherRating",
            "AverageCourseRating",
            "EnrollmentCount",
            "RatingTier"
        ]

        for column in possible_columns:

            if column in filtered_instructor.columns:

                leaderboard_columns.append(column)


        leaderboard = (
            filtered_instructor[
                leaderboard_columns
            ]
            .sort_values(
                by="TeacherRating",
                ascending=False
            )
        )


        st.dataframe(
            leaderboard,
            use_container_width=True,
            hide_index=True
        )


    # --------------------------------------------------------
    # TOP INSTRUCTORS
    # --------------------------------------------------------

    st.subheader("🏆 Top 10 Instructors")


    if (
        not filtered_instructor.empty
        and "TeacherName" in filtered_instructor.columns
        and "TeacherRating" in filtered_instructor.columns
    ):

        top10 = (
            filtered_instructor
            .sort_values(
                "TeacherRating",
                ascending=False
            )
            .head(10)
        )


        fig = px.bar(
            top10.sort_values("TeacherRating"),
            x="TeacherRating",
            y="TeacherName",
            orientation="h",
            title="Top 10 Instructors by Teacher Rating",
            text="TeacherRating"
        )


        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # TEACHER RATING VS ENROLLMENT
    # --------------------------------------------------------

    if (
        "TeacherRating" in filtered_instructor.columns
        and "EnrollmentCount" in filtered_instructor.columns
    ):

        st.subheader(
            "📈 Teacher Rating vs Enrollment"
        )


        fig = px.scatter(
            filtered_instructor,
            x="TeacherRating",
            y="EnrollmentCount",
            hover_name=(
                "TeacherName"
                if "TeacherName" in filtered_instructor.columns
                else None
            ),
            color=(
                "RatingTier"
                if "RatingTier" in filtered_instructor.columns
                else None
            ),
            title="Instructor Rating vs Enrollment"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# TAB 3 — EXPERIENCE ANALYSIS
# ============================================================

with experience_tab:

    st.header("📈 Teaching Experience Analysis")


    # --------------------------------------------------------
    # EXPERIENCE VS TEACHER RATING
    # --------------------------------------------------------

    if (
        "YearsOfExperience" in filtered_instructor.columns
        and "TeacherRating" in filtered_instructor.columns
    ):

        experience_data = filtered_instructor[
            [
                "YearsOfExperience",
                "TeacherRating"
            ]
        ].dropna()


        if len(experience_data) > 1:

            experience_correlation = (
                experience_data
                .corr()
                .iloc[0, 1]
            )

        else:

            experience_correlation = 0


        st.metric(
            "Experience vs Teacher Rating Correlation",
            f"{experience_correlation:.3f}"
        )


        fig = px.scatter(
            filtered_instructor,
            x="YearsOfExperience",
            y="TeacherRating",
            hover_name=(
                "TeacherName"
                if "TeacherName" in filtered_instructor.columns
                else None
            ),
            color=(
                "Expertise"
                if "Expertise" in filtered_instructor.columns
                else None
            ),
            title="Teaching Experience vs Teacher Rating"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        # ----------------------------------------------------
        # EXPERIENCE GROUP
        # ----------------------------------------------------

        st.subheader(
            "📊 Average Rating by Experience Group"
        )


        if "ExperienceGroup" in filtered_instructor.columns:

            experience_summary = (
                filtered_instructor
                .groupby("ExperienceGroup")
                ["TeacherRating"]
                .mean()
                .reset_index()
            )


            fig = px.bar(
                experience_summary,
                x="ExperienceGroup",
                y="TeacherRating",
                title="Average Teacher Rating by Experience Group",
                text="TeacherRating"
            )


            fig.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside"
            )


            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # --------------------------------------------------------
    # EXPERIENCE VS COURSE RATING
    # --------------------------------------------------------

    if (
        "YearsOfExperience" in filtered_processed.columns
        and "CourseRating" in filtered_processed.columns
    ):

        st.subheader(
            "📚 Experience vs Course Rating"
        )


        course_experience = filtered_processed[
            [
                "YearsOfExperience",
                "CourseRating"
            ]
        ].dropna()


        if len(course_experience) > 1:

            course_experience_corr = (
                course_experience
                .corr()
                .iloc[0, 1]
            )

        else:

            course_experience_corr = 0


        st.metric(
            "Experience vs Course Rating Correlation",
            f"{course_experience_corr:.3f}"
        )


        fig = px.scatter(
            filtered_processed,
            x="YearsOfExperience",
            y="CourseRating",
            hover_name=(
                "TeacherName"
                if "TeacherName" in filtered_processed.columns
                else None
            ),
            color=(
                "CourseCategory"
                if "CourseCategory" in filtered_processed.columns
                else None
            ),
            title="Teaching Experience vs Course Rating"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# TAB 4 — COURSE QUALITY
# ============================================================

with course_tab:

    st.header("📚 Course Quality Evaluation")


    category_col, level_col = st.columns(2)


    # --------------------------------------------------------
    # CATEGORY RATING
    # --------------------------------------------------------

    with category_col:

        if (
            "CourseCategory" in filtered_processed.columns
            and "CourseRating" in filtered_processed.columns
        ):

            category_rating = (
                filtered_processed
                .groupby("CourseCategory")
                ["CourseRating"]
                .mean()
                .reset_index()
                .sort_values(
                    "CourseRating",
                    ascending=False
                )
            )


            fig = px.bar(
                category_rating,
                x="CourseCategory",
                y="CourseRating",
                title="Average Course Rating by Category",
                text="CourseRating"
            )


            fig.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside"
            )


            fig.update_layout(
                xaxis_tickangle=-45
            )


            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # --------------------------------------------------------
    # LEVEL RATING
    # --------------------------------------------------------

    with level_col:

        if (
            "CourseLevel" in filtered_processed.columns
            and "CourseRating" in filtered_processed.columns
        ):

            level_rating = (
                filtered_processed
                .groupby("CourseLevel")
                ["CourseRating"]
                .mean()
                .reset_index()
                .sort_values(
                    "CourseRating",
                    ascending=False
                )
            )


            fig = px.bar(
                level_rating,
                x="CourseLevel",
                y="CourseRating",
                title="Average Course Rating by Level",
                text="CourseRating"
            )


            fig.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside"
            )


            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # --------------------------------------------------------
    # CATEGORY × LEVEL HEATMAP
    # --------------------------------------------------------

    if (
        "CourseCategory" in filtered_processed.columns
        and "CourseLevel" in filtered_processed.columns
        and "CourseRating" in filtered_processed.columns
    ):

        st.subheader(
            "🔥 Course Quality Heatmap"
        )


        heatmap_data = pd.pivot_table(
            filtered_processed,
            values="CourseRating",
            index="CourseCategory",
            columns="CourseLevel",
            aggfunc="mean"
        )


        if not heatmap_data.empty:

            fig = px.imshow(
                heatmap_data,
                text_auto=".2f",
                aspect="auto",
                title="Average Course Rating by Category and Level"
            )


            st.plotly_chart(
                fig,
                use_container_width=True
            )


# ============================================================
# TAB 5 — EXPERTISE ANALYSIS
# ============================================================

with expertise_tab:

    st.header("🎯 Expertise-wise Performance")


    # --------------------------------------------------------
    # TEACHER RATING BY EXPERTISE
    # --------------------------------------------------------

    if (
        "Expertise" in filtered_instructor.columns
        and "TeacherRating" in filtered_instructor.columns
    ):

        expertise_summary = (
            filtered_instructor
            .groupby("Expertise")
            .agg(
                AverageTeacherRating=(
                    "TeacherRating",
                    "mean"
                ),
                InstructorCount=(
                    "TeacherRating",
                    "count"
                )
            )
            .reset_index()
            .sort_values(
                "AverageTeacherRating",
                ascending=False
            )
        )


        fig = px.bar(
            expertise_summary,
            x="Expertise",
            y="AverageTeacherRating",
            title="Average Teacher Rating by Expertise",
            text="AverageTeacherRating"
        )


        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )


        fig.update_layout(
            xaxis_tickangle=-45
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        st.dataframe(
            expertise_summary,
            use_container_width=True,
            hide_index=True
        )


    # --------------------------------------------------------
    # EXPERTISE VS COURSE RATING
    # --------------------------------------------------------

    if (
        "Expertise" in filtered_processed.columns
        and "CourseRating" in filtered_processed.columns
    ):

        expertise_course = (
            filtered_processed
            .groupby("Expertise")
            .agg(
                AverageCourseRating=(
                    "CourseRating",
                    "mean"
                ),
                CourseCount=(
                    "CourseRating",
                    "count"
                )
            )
            .reset_index()
            .sort_values(
                "AverageCourseRating",
                ascending=False
            )
        )


        fig = px.bar(
            expertise_course,
            x="Expertise",
            y="AverageCourseRating",
            title="Average Course Rating by Expertise",
            text="AverageCourseRating"
        )


        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )


        fig.update_layout(
            xaxis_tickangle=-45
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        st.dataframe(
            expertise_course,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# KEY INSIGHTS
# ============================================================

st.divider()

st.header("💡 Key Insights")


insights = []


# Teacher rating insight

if average_teacher_rating >= 4:

    insights.append(
        "Instructor performance is strong, with an average teacher rating of "
        f"{average_teacher_rating:.2f}."
    )

elif average_teacher_rating >= 3:

    insights.append(
        "Instructor performance is moderate, indicating opportunities for improvement."
    )

else:

    insights.append(
        "Instructor ratings indicate that targeted teaching-quality improvements may be required."
    )


# Course rating insight

if average_course_rating >= 4:

    insights.append(
        "Overall course quality is strong based on the average course rating."
    )

elif average_course_rating >= 3:

    insights.append(
        "Course quality is moderate and can be improved in lower-performing categories."
    )

else:

    insights.append(
        "Course quality requires attention, particularly among lower-rated courses."
    )


# Experience insight

if (
    "YearsOfExperience" in filtered_instructor.columns
    and "TeacherRating" in filtered_instructor.columns
):

    exp_data = filtered_instructor[
        [
            "YearsOfExperience",
            "TeacherRating"
        ]
    ].dropna()


    if len(exp_data) > 1:

        corr = exp_data.corr().iloc[0, 1]


        if corr >= 0.5:

            insights.append(
                "Teaching experience has a strong positive relationship with instructor ratings."
            )

        elif corr >= 0.2:

            insights.append(
                "Teaching experience has a moderate positive relationship with instructor ratings."
            )

        elif corr >= -0.2:

            insights.append(
                "Teaching experience has a weak relationship with instructor ratings."
            )

        else:

            insights.append(
                "Teaching experience shows a negative relationship with instructor ratings."
            )


# Display insights

for insight in insights:

    st.info("• " + insight)


# ============================================================
# DATASET INFORMATION
# ============================================================

st.divider()

st.header("📋 Dataset Information")


info1, info2, info3 = st.columns(3)


with info1:

    st.subheader("Instructor Data")

    st.write(
        f"Rows: **{len(instructor):,}**"
    )

    st.write(
        f"Columns: **{len(instructor.columns):,}**"
    )


with info2:

    st.subheader("Processed Data")

    st.write(
        f"Rows: **{len(processed):,}**"
    )

    st.write(
        f"Columns: **{len(processed.columns):,}**"
    )


with info3:

    st.subheader("Expertise Data")

    st.write(
        f"Rows: **{len(expertise):,}**"
    )

    st.write(
        f"Columns: **{len(expertise.columns):,}**"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EduPro Instructor Performance & Course Quality Evaluation | "
    "Data Analytics Project"
)
