import streamlit as st
import pandas as pd
import plotly.express as px


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="EduPro Instructor Performance",
    page_icon="🎓",
    layout="wide"
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

@st.cache_data
def load_data():

    instructor_df = pd.read_csv(
        "EduPro_Instructor_Performance.csv"
    )

    df = pd.read_csv(
        "EduPro_Processed_Data.csv"
    )

    return instructor_df, df


instructor_df, df = load_data()


# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title(
    "🎓 EduPro Instructor Performance & Course Quality"
)

st.write(
    "Interactive analysis of instructor performance, "
    "teaching experience and course quality."
)

st.divider()


# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

st.sidebar.header("🔎 Filters")


# Instructor Expertise

expertise_list = sorted(
    instructor_df["Expertise"]
    .dropna()
    .unique()
)

selected_expertise = st.sidebar.multiselect(
    "Instructor Expertise",
    expertise_list,
    default=expertise_list
)


# Course Category

category_list = sorted(
    df["CourseCategory"]
    .dropna()
    .unique()
)

selected_category = st.sidebar.multiselect(
    "Course Category",
    category_list,
    default=category_list
)


# Course Level

level_list = sorted(
    df["CourseLevel"]
    .dropna()
    .unique()
)

selected_level = st.sidebar.multiselect(
    "Course Level",
    level_list,
    default=level_list
)


# Rating Range Slider

min_rating = float(
    instructor_df["TeacherRating"].min()
)

max_rating = float(
    instructor_df["TeacherRating"].max()
)

rating_range = st.sidebar.slider(
    "Teacher Rating Range",
    min_value=min_rating,
    max_value=max_rating,
    value=(min_rating, max_rating),
    step=0.1
)


# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------

filtered_instructors = instructor_df[
    instructor_df["Expertise"].isin(
        selected_expertise
    )
    &
    instructor_df["TeacherRating"].between(
        rating_range[0],
        rating_range[1]
    )
]


filtered_courses = df[
    df["Expertise"].isin(
        selected_expertise
    )
    &
    df["CourseCategory"].isin(
        selected_category
    )
    &
    df["CourseLevel"].isin(
        selected_level
    )
    &
    df["TeacherRating"].between(
        rating_range[0],
        rating_range[1]
    )
]


# ---------------------------------------------------------
# 1. INSTRUCTOR PERFORMANCE LEADERBOARD
# ---------------------------------------------------------

st.header("🏆 Instructor Performance Leaderboard")

leaderboard = (
    filtered_instructors
    .sort_values(
        "InstructorPerformanceScore",
        ascending=False
    )
)


leaderboard_display = leaderboard[
    [
        "TeacherName",
        "Expertise",
        "YearsOfExperience",
        "TeacherRating",
        "AverageCourseRating",
        "EnrollmentCount",
        "InstructorPerformanceScore"
    ]
].copy()


leaderboard_display.columns = [
    "Instructor",
    "Expertise",
    "Experience",
    "Teacher Rating",
    "Course Rating",
    "Enrollments",
    "Performance Score"
]


st.dataframe(
    leaderboard_display,
    use_container_width=True,
    hide_index=True
)


# Top 10 instructors

top10 = leaderboard.head(10)


if not top10.empty:

    fig = px.bar(
        top10,
        x="InstructorPerformanceScore",
        y="TeacherName",
        orientation="h",
        title="Top 10 Instructor Performance",
        labels={
            "InstructorPerformanceScore":
                "Performance Score",
            "TeacherName":
                "Instructor"
        }
    )

    fig.update_layout(
        yaxis=dict(
            categoryorder="total ascending"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


st.divider()


# ---------------------------------------------------------
# 2. EXPERIENCE VS RATING SCATTER PLOTS
# ---------------------------------------------------------

st.header("📈 Experience vs Rating")


col1, col2 = st.columns(2)


# Experience vs Teacher Rating

with col1:

    fig1 = px.scatter(
        filtered_instructors,
        x="YearsOfExperience",
        y="TeacherRating",
        hover_name="TeacherName",
        hover_data=[
            "Expertise"
        ],
        title="Experience vs Teacher Rating",
        labels={
            "YearsOfExperience":
                "Years of Experience",
            "TeacherRating":
                "Teacher Rating"
        }
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )


# Experience vs Course Rating

with col2:

    fig2 = px.scatter(
        filtered_courses,
        x="YearsOfExperience",
        y="CourseRating",
        hover_name="TeacherName",
        hover_data=[
            "CourseName",
            "CourseCategory",
            "CourseLevel"
        ],
        title="Experience vs Course Rating",
        labels={
            "YearsOfExperience":
                "Years of Experience",
            "CourseRating":
                "Course Rating"
        }
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


st.divider()


# ---------------------------------------------------------
# 3. COURSE QUALITY HEATMAP
# ---------------------------------------------------------

st.header("📚 Course Quality Heatmap")


heatmap_data = pd.pivot_table(
    filtered_courses,
    values="CourseRating",
    index="CourseCategory",
    columns="CourseLevel",
    aggfunc="mean"
)


if not heatmap_data.empty:

    fig3 = px.imshow(
        heatmap_data,
        text_auto=".2f",
        aspect="auto",
        title="Average Course Rating by Category and Level",
        labels={
            "x": "Course Level",
            "y": "Course Category",
            "color": "Course Rating"
        }
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

else:

    st.warning(
        "No course data available for the selected filters."
    )


st.divider()


# ---------------------------------------------------------
# 4. EXPERTISE-WISE PERFORMANCE COMPARISON
# ---------------------------------------------------------

st.header("🎯 Expertise-wise Performance Comparison")


expertise_analysis = (
    filtered_instructors
    .groupby("Expertise")
    .agg(
        AverageTeacherRating=(
            "TeacherRating",
            "mean"
        ),
        AverageCourseRating=(
            "AverageCourseRating",
            "mean"
        ),
        AveragePerformanceScore=(
            "InstructorPerformanceScore",
            "mean"
        )
    )
    .reset_index()
)


if not expertise_analysis.empty:

    fig4 = px.bar(
        expertise_analysis,
        x="Expertise",
        y="AveragePerformanceScore",
        title="Average Performance Score by Expertise",
        labels={
            "AveragePerformanceScore":
                "Average Performance Score",
            "Expertise":
                "Instructor Expertise"
        },
        text_auto=".2f"
    )

    fig4.update_layout(
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )


# Expertise table

st.subheader("Expertise Performance Details")

st.dataframe(
    expertise_analysis.sort_values(
        "AveragePerformanceScore",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "EduPro — Instructor Performance and Course Quality Evaluation"
)