import os

import altair as alt
import duckdb
import streamlit as st

st.set_page_config(page_title="Data Job Skills Tracker", layout="wide")


@st.cache_resource
def get_connection():
    # locally the token comes from the environment, on Streamlit Cloud from secrets
    if "MOTHERDUCK_TOKEN" not in os.environ:
        os.environ["MOTHERDUCK_TOKEN"] = st.secrets["MOTHERDUCK_TOKEN"]
    return duckdb.connect("md:job_market")


@st.cache_data(ttl=3600)  # data only changes once a day
def query(sql, params=None):
    return get_connection().cursor().execute(sql, params or []).df()


# ---------- header ----------
st.title("What skills do data jobs ask for?")
st.caption(
    "Job postings collected daily from public job board APIs, "
    "filtered to data roles, and scanned for skills."
)

summary = query("""
    SELECT
        count(*) FILTER (WHERE is_data_job) AS data_jobs,
        (SELECT count(DISTINCT cast(ingested_at AS date)) FROM raw_jobs) AS days_collected,
        (SELECT max(ingested_at) FROM raw_jobs) AS last_updated
    FROM stg_jobs
""").iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("Data jobs tracked", f"{int(summary.data_jobs):,}")
c2.metric("Days of data", int(summary.days_collected))
c3.metric("Last updated (UTC)", summary.last_updated.strftime("%Y-%m-%d %H:%M"))

st.divider()

# ---------- top skills ----------
st.subheader("Top skills")
level = st.radio(
    "Seniority (guessed from the job title)",
    ["all", "intern", "junior", "senior", "unspecified"],
    horizontal=True,
)

top = query("""
    WITH jobs AS (
        SELECT source, job_id
        FROM stg_jobs
        WHERE is_data_job AND (? = 'all' OR seniority = ?)
    )
    SELECT
        f.skill,
        f.category,
        count(*) AS jobs,
        round(100.0 * count(*) / (SELECT nullif(count(*), 0) FROM jobs), 1) AS pct
    FROM fct_job_skills f
    JOIN jobs USING (source, job_id)
    GROUP BY f.skill, f.category
    ORDER BY jobs DESC
    LIMIT 15
""", [level, level])

job_count = query("""
    SELECT count(*) AS n FROM stg_jobs
    WHERE is_data_job AND (? = 'all' OR seniority = ?)
""", [level, level]).iloc[0].n

if top.empty:
    st.info("No jobs at this level yet.")
else:
    bars = (
        alt.Chart(top)
        .mark_bar()
        .encode(
            x=alt.X("pct:Q", title="% of data jobs mentioning the skill"),
            y=alt.Y("skill:N", sort="-x", title=None),
            color=alt.Color("category:N", title="Category"),
            tooltip=["skill", "category", "jobs", "pct"],
        )
        .properties(height=420)
    )
    st.altair_chart(bars, use_container_width=True)
    st.caption(f"Based on {int(job_count):,} jobs.")
    if job_count < 30:
        st.warning("Small sample at this level, so treat the ranking as rough.")

st.divider()

# ---------- weekly trend ----------
st.subheader("Weekly trend")
all_skills = query("SELECT DISTINCT skill FROM mart_skill_trends ORDER BY skill").skill.tolist()
defaults = [s for s in ["python", "sql", "dbt", "airflow", "spark"] if s in all_skills]
chosen = st.multiselect("Skills", all_skills, default=defaults)

trend = query("""
    SELECT week_start, skill, pct_of_jobs, job_count, total_jobs
    FROM mart_skill_trends
    ORDER BY week_start
""")
trend = trend[trend.skill.isin(chosen)]
trend["week"] = trend.week_start.astype("datetime64[ns]").dt.strftime("%d %b")

if trend.empty:
    st.info("Pick at least one skill.")
else:
    lines = (
        alt.Chart(trend)
        .mark_line(point=True)
        .encode(
            x=alt.X("week:O", title="Week starting", sort=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("pct_of_jobs:Q", title="% of that week's data jobs"),
            color=alt.Color("skill:N", title="Skill"),
            tooltip=["week_start", "skill", "pct_of_jobs", "job_count", "total_jobs"],
        )
        .properties(height=380)
    )
    st.altair_chart(lines, use_container_width=True)
    st.caption(
        "Older weeks are undercounted because ingestion only reads the newest pages "
        "of each API, and the current week is still in progress."
    )

# ---------- method ----------
with st.expander("How this works and what to keep in mind"):
    st.markdown("""
- **Sources:** Arbeitnow and Remotive public APIs, pulled once a day by GitHub Actions.
  Most postings are in Europe or remote.
- **Pipeline:** Python loads raw JSON into MotherDuck, dbt cleans it, picks the latest
  version of each job and runs data quality tests before the tables here are rebuilt.
- **Data roles** are detected from keywords in the job title, so a few edge cases are
  missed or misclassified.
- **Skills** are regex matches against the title, description and tags.
  A posting that mentions a skill counts once, even if it repeats it.
- **Seniority** is guessed from the title. Most postings don't say, hence "unspecified".
""")