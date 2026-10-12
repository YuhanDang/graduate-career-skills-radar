import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Replace this placeholder with the actual classroom team name.
TEAM_NAME = "Your Team Name"
DATA_PATH = Path(__file__).resolve().parent / "data" / "career_postings_expanded.csv"
PATHWAYS = [
    "Data and Business Analytics",
    "Finance and Accounting",
    "Marketing",
    "Software Development",
]
SCOPES = {
    "All Selected Advertisements": None,
    "Explicit Early-Career Title Signals": "Explicit Early-Career Title Signal",
    "Broader Title Matches — Eligibility Unverified": "Broader Title Match - Eligibility Unverified",
}

st.set_page_config(page_title="Graduate Career Skills Radar", layout="wide")


@st.cache_data
def load_data(path, modified_time):
    data = pd.read_csv(path)
    for column in ["workshop_skills", "qualification_like_terms"]:
        data[column] = data[column].apply(json.loads)
    for column in [
        "has_valid_skills", "has_skill_record",
        "possible_duplicate", "volunteer_title_signal",
    ]:
        data[column] = data[column].astype(str).str.casefold().eq("true")
    return data


def skill_rates(group):
    valid = group.loc[group["has_valid_skills"]]
    counts = Counter()
    for skills in valid["workshop_skills"]:
        counts.update(set(skills))
    return pd.Series(
        {skill: count / len(valid) * 100 for skill, count in counts.items()},
        dtype="float64",
    ).sort_values(ascending=False)


def bar_chart(labels, values, annotations):
    fig, ax = plt.subplots(figsize=(10, max(3, len(labels) * 0.48)))
    ax.barh(range(len(labels)), values, color="#3569c6")
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Advertisements with skill information (%)")
    ax.set_axisbelow(True)
    ax.grid(axis="x", alpha=0.15)
    for i, (value, annotation) in enumerate(zip(values, annotations)):
        ax.text(
            min(value + 1, 99), i, annotation,
            va="center", ha="right" if value > 85 else "left",
        )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


st.title(f"Graduate Career Skills Radar — {TEAM_NAME}")
st.caption(
    "For U.S. university Career Services directors planning skill workshops "
    "across four career pathways."
)
st.caption(
    "Data: first observed Jan 12–17, 2024, Kaggle snapshot. "
    "Proposed production refresh: weekly; planning review: monthly."
)

if not DATA_PATH.exists():
    st.error("The dashboard CSV is missing from the project's data folder.")
    st.stop()

data = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)

with st.sidebar:
    st.header("Planning Filters")
    state_options = sorted(data["target_state"].unique())
    states = st.multiselect(
        "Target State", state_options,
        help="State abbreviations include DC. Unspecified means no state was assigned.",
    )
    st.caption("Leave empty to include all selected U.S. locations, including Unspecified.")
    pathway = st.selectbox("Career Pathway", PATHWAYS)
    scope_label = st.selectbox("Analysis Scope", list(SCOPES))

comparison_data = data.copy()
if states:
    comparison_data = comparison_data.loc[comparison_data["target_state"].isin(states)]
if SCOPES[scope_label] is not None:
    comparison_data = comparison_data.loc[
        comparison_data["analysis_scope"].eq(SCOPES[scope_label])
    ]
selected = comparison_data.loc[comparison_data["career_pathway"].eq(pathway)]
rates = skill_rates(selected)

with st.sidebar:
    if rates.empty:
        skill = None
        st.info("No retained skill terms are available for this selection.")
    else:
        options = rates.index.tolist()
        skill = st.selectbox(
            "Skill of Interest", options,
            index=options.index("sql") if "sql" in options else 0,
        )

valid_count = int(selected["has_valid_skills"].sum())
coverage = valid_count / len(selected) * 100 if len(selected) else None
mention_rate = float(rates.get(skill, 0)) if skill is not None and valid_count else None

columns = st.columns(3)
columns[0].metric("Selected Advertisements", f"{len(selected):,}")
columns[1].metric("Skill Information Coverage", f"{coverage:.1f}%" if coverage is not None else "N/A")
columns[2].metric("Selected Skill Mention Rate", f"{mention_rate:.1f}%" if mention_rate is not None else "N/A")
st.caption(
    f"{pathway} · {scope_label} · "
    f"{valid_count:,} nonblank original skill lists. "
    "Rates describe extracted mentions, not verified mandatory requirements."
)
if SCOPES[scope_label] != "Explicit Early-Career Title Signal":
    st.caption("Broader titles are included; graduate eligibility is unverified.")
if len(selected) == 0:
    st.info("No advertisements match this selection. Choose another state, pathway, or scope.")
elif valid_count < 100:
    st.warning("Small selected group: interpret skill percentages cautiously. The 100-record cutoff is a display caution, not a statistical guarantee.")

st.subheader(f"Top Skill Mentions — {pathway}")
if rates.empty:
    st.info("No skill ranking is available for this selection.")
else:
    top = rates.head(8)
    fig = bar_chart(top.index.tolist(), top.tolist(), [f"{value:.1f}%" for value in top])
    st.pyplot(fig)
    plt.close(fig)

st.subheader(f"{skill.upper() if skill else 'Selected Skill'} Mentions Across Career Pathways")
st.caption("This chart compares all four pathways using the same state selection and analysis scope. Each pathway has its own denominator.")
if skill is not None:
    values, annotations = [], []
    for name in PATHWAYS:
        group = comparison_data.loc[comparison_data["career_pathway"].eq(name)]
        n = int(group["has_valid_skills"].sum())
        rate = float(skill_rates(group).get(skill, 0)) if n else 0
        values.append(rate)
        caution = "; small group" if 0 < n < 100 else ""
        annotations.append(f"{rate:.1f}% (n={n}{caution})" if n else "N/A (n=0)")
    fig = bar_chart(PATHWAYS, values, annotations)
    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("Select a pathway with retained skills to choose a skill for comparison.")

with st.expander("Example Advertisements"):
    only_mentions = st.checkbox("Show only advertisements mentioning the selected skill", value=True)
    examples = selected.copy()
    if only_mentions:
        examples = examples.loc[
            examples["workshop_skills"].apply(lambda terms: skill in terms if skill else False)
        ]
    st.caption(f"{len(examples):,} matching examples. This table filter does not change headline metric denominators. Historical links may no longer be available.")
    if examples.empty:
        st.info("No advertisement examples match the current table selection.")
    else:
        shown = examples.sort_values(["company", "job_title", "job_link"]).head(50).copy()
        shown["workshop_skills"] = shown["workshop_skills"].apply(lambda terms: "; ".join(terms))
        shown["qualification_like_terms"] = shown["qualification_like_terms"].apply(lambda terms: "; ".join(terms))
        st.caption("Showing up to 50 examples, sorted by company and title. These are not a representative sample.")
        st.dataframe(
            shown[["job_title", "company", "job_location", "analysis_scope", "workshop_skills", "qualification_like_terms", "volunteer_title_signal", "possible_duplicate", "job_link"]],
            hide_index=True,
            column_config={
                "job_title": "Job Title", "company": "Company",
                "job_location": "Location", "analysis_scope": "Analysis Scope",
                "workshop_skills": "Retained Skill Terms",
                "qualification_like_terms": "Withheld Qualification Terms",
                "volunteer_title_signal": "Volunteer Title Signal",
                "possible_duplicate": "Possible Duplicate",
                "job_link": st.column_config.LinkColumn("Original LinkedIn Posting", display_text="Open posting"),
            },
        )

with st.expander("Data Notes and Limitations"):
    st.markdown(
        """
- One row is an advertisement, not a verified unique vacancy or hire.
- Title and location rules are heuristic. Early-career titles do not confirm applicant eligibility.
- Skill terms are extracted labels. Qualification screening and alias normalization are provisional.
- Missing original skill lists are excluded from mention-rate denominators but included in advertisement counts.
- Possible repeated advertisements remain in the data; repeated ads can affect rates.
- Unspecified state records are included in the default all-location view. Cross-state areas are not forced into one state.
- The snapshot cannot establish hiring growth, student skill gaps, graduate employment outcomes, or current job availability.
- Reliable salary information is not available in this dashboard input.
        """
    )
    st.caption(f"Possible-duplicate flags in this selection: {int(selected['possible_duplicate'].sum()):,} advertisements.")
    st.markdown("Dataset: [1.3M LinkedIn Jobs & Skills (2024), Kaggle](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024)")
