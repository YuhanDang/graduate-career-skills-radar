import json
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

# Replace the placeholder with the actual classroom team name.
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
STATE_NAMES = dict(zip(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split(),
    ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
     "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
     "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
     "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
     "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
     "New Hampshire", "New Jersey", "New Mexico", "New York",
     "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
     "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
     "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
     "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"],
))
TERM_NAMES = {
    "sql": "SQL", "python": "Python", "excel": "Excel", "r": "R",
    "java": "Java", "javascript": "JavaScript", "c++": "C++",
    "c#": "C#", "html": "HTML", "css": "CSS", "tableau": "Tableau",
    "power bi": "Power BI", "git": "Git", "aws": "AWS",
    "sas": "SAS", "gaap": "GAAP", "seo": "SEO",
}

st.set_page_config(page_title="Graduate Career Skills Radar", layout="centered")


def term_name(term):
    return TERM_NAMES.get(term, term.capitalize())


@st.cache_data
def load_data(path, modified_time):
    data = pd.read_csv(path)
    for column in ["workshop_skills", "qualification_like_terms"]:
        data[column] = data[column].apply(json.loads)
    for column in ["has_valid_skills", "has_skill_record",
                   "possible_duplicate", "volunteer_title_signal"]:
        data[column] = data[column].astype(str).str.casefold().eq("true")
    return data


def skill_summary(group):
    valid = group.loc[group["has_valid_skills"]]
    counts = Counter()
    for terms in valid["workshop_skills"]:
        counts.update(set(terms))
    ordered = sorted(counts, key=lambda term: (-counts[term], term))
    return pd.DataFrame([
        {"term": term, "skill": term_name(term), "mentions": counts[term],
         "valid_records": len(valid), "rate": counts[term] / len(valid)}
        for term in ordered
    ], columns=["term", "skill", "mentions", "valid_records", "rate"])


def sync_profile(visible_terms):
    profile = set(st.session_state.get("_skill_profile", []))
    chosen = set(st.session_state.get("current_skills", []))
    st.session_state["_skill_profile"] = sorted(
        (profile - set(visible_terms)) | chosen
    )


def show_skill_chart(frame):
    spec = {
        "height": {"step": 32},
        "encoding": {
            "y": {"field": "skill", "type": "nominal", "sort": None,
                  "axis": {"title": None, "labelLimit": 240}},
            "x": {"field": "rate", "type": "quantitative",
                  "scale": {"domain": [0, 1]},
                  "axis": {"title": "Advertisements mentioning the term (%)", "format": ".0%"}},
        },
        "layer": [
            {"mark": {"type": "bar", "cornerRadiusEnd": 4},
             "encoding": {
                 "color": {"field": "profile_status", "type": "nominal",
                           "scale": {"domain": ["Selected as current", "Not selected"],
                                     "range": ["#DCA900", "#DF65A1"]},
                           "legend": {"title": None, "orient": "top"}},
                 "tooltip": [
                     {"field": "skill", "title": "Skill term"},
                     {"field": "rate", "title": "Mention rate", "format": ".1%"},
                     {"field": "mentions", "title": "Advertisements mentioning term"},
                     {"field": "valid_records", "title": "Nonblank skill lists"},
                     {"field": "profile_status", "title": "Self-reported selection"},
                 ]}},
            {"mark": {"type": "text", "align": "left", "dx": 5},
             "encoding": {"x": {"field": "label_position", "type": "quantitative"},
                          "text": {"field": "rate", "type": "quantitative", "format": ".1%"}}},
        ],
    }
    st.vega_lite_chart(frame, spec, width="stretch")


def show_comparison_chart(frame):
    spec = {
        "height": {"step": 42},
        "encoding": {
            "y": {"field": "pathway", "type": "nominal", "sort": None,
                  "axis": {"title": None, "labelLimit": 240}},
            "x": {"field": "rate", "type": "quantitative",
                  "scale": {"domain": [0, 1]},
                  "axis": {"title": "Advertisements mentioning the term (%)", "format": ".0%"}},
        },
        "layer": [
            {"mark": {"type": "bar", "color": "#467AC7", "cornerRadiusEnd": 4},
             "encoding": {"tooltip": [
                 {"field": "pathway", "title": "Career pathway"},
                 {"field": "rate", "title": "Mention rate", "format": ".1%"},
                 {"field": "mentions", "title": "Advertisements mentioning term"},
                 {"field": "valid_records", "title": "Nonblank skill lists"},
                 {"field": "note", "title": "Interpretation"},
             ]}},
            {"mark": {"type": "text", "align": "left", "dx": 5},
             "encoding": {"x": {"field": "label_position", "type": "quantitative"},
                          "text": {"field": "label"}}},
        ],
    }
    st.vega_lite_chart(frame, spec, width="stretch")


st.title("Graduate Career Skills Radar")
st.caption(f"Team: {TEAM_NAME}")
st.caption("For U.S. university students exploring career pathways and choosing their next skill-learning topic.")
st.caption(
    "Data: first observed Jan 12–17, 2024, Kaggle snapshot. "
    "Proposed production refresh: weekly; review weekly during active career preparation."
)

if not DATA_PATH.exists():
    st.error("The dashboard CSV is missing from the project's data folder.")
    st.stop()
data = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)

filter_columns = st.columns([1.2, 1.3, 1])
with filter_columns[0]:
    pathway = st.selectbox("Career Pathway", PATHWAYS, key="pathway")
with filter_columns[1]:
    scope_label = st.selectbox("Analysis Scope", list(SCOPES), key="scope")
with filter_columns[2]:
    states = st.multiselect(
        "Target State", sorted(data["target_state"].unique()), key="states",
        format_func=lambda code: STATE_NAMES.get(code, "Unspecified"),
        placeholder="All selected U.S. locations",
    )
st.caption("No state selection includes all selected U.S. locations, including unspecified states. Title signals do not confirm graduate eligibility.")

comparison_data = data.copy()
if states:
    comparison_data = comparison_data.loc[comparison_data["target_state"].isin(states)]
if SCOPES[scope_label] is not None:
    comparison_data = comparison_data.loc[comparison_data["analysis_scope"].eq(SCOPES[scope_label])]
selected = comparison_data.loc[comparison_data["career_pathway"].eq(pathway)]
summary = skill_summary(selected)
top = summary.head(8).copy()
valid_count = int(selected["has_valid_skills"].sum())

profile = set(st.session_state.get("_skill_profile", []))
with st.container(border=True):
    st.subheader("My Current Skills")
    st.caption("Select terms that describe your current skills. These are self-reported choices, not a proficiency assessment.")
    if top.empty:
        st.info("No skill terms are available for this selection. Your session selections are retained.")
    else:
        visible = top["term"].tolist()
        st.session_state["current_skills"] = [term for term in visible if term in profile]
        st.pills(
            "Select or remove a displayed skill", visible, selection_mode="multi",
            format_func=term_name, key="current_skills", wrap=True, label_visibility="collapsed",
            on_change=sync_profile, args=(visible,),
        )
    hidden_profile = sorted(profile - set(top["term"]))
    if hidden_profile:
        st.caption("Also selected in this session: " + ", ".join(term_name(term) for term in hidden_profile))

selected_top_count = sum(term in profile for term in top["term"])
information_coverage = valid_count / len(selected) if len(selected) else None
profile_coverage = selected_top_count / len(top) if len(top) else None
metrics = st.columns(3)
metrics[0].metric("Selected Advertisements", f"{len(selected):,}", border=True)
metrics[1].metric("Skill Information Coverage", f"{information_coverage:.1%}" if information_coverage is not None else "N/A", border=True)
metrics[2].metric(
    "Top-Skill Coverage",
    f"{profile_coverage:.1%}" if profile_coverage is not None else "N/A",
    border=True, help="Selected displayed skill terms divided by the number of displayed terms. Not a qualification or hiring score.",
)
st.caption(
    f"{valid_count:,} nonblank original skill lists. "
    + (f"{selected_top_count} of {len(top)} displayed terms selected. " if len(top) else "")
    + "Mention rates describe extracted terms, not verified mandatory requirements."
)
if not profile and len(top):
    st.caption("No skills selected yet: 0% records your current input, not a verified lack of ability.")
if SCOPES[scope_label] != "Explicit Early-Career Title Signal":
    st.caption("Broader titles are included; experience and applicant eligibility are unverified.")
if selected.empty:
    st.info("No advertisements match this selection. Change the pathway, state, or analysis scope.")
elif valid_count < 100:
    st.warning("Small selected group: interpret these percentages cautiously. The 100-record flag is a display caution, not a statistical guarantee.")

st.subheader("Top Skill Mentions")
st.caption(f"{pathway} · Up to eight terms. Hover over a bar to inspect counts and your selection status.")
if top.empty:
    st.info("No retained skill ranking is available.")
else:
    top["profile_status"] = top["term"].apply(lambda term: "Selected as current" if term in profile else "Not selected")
    top["label_position"] = top["rate"].clip(upper=0.86)
    show_skill_chart(top)

st.subheader("Compare a Skill Across Career Pathways")
if summary.empty:
    skill = None
    st.info("Choose a selection with retained skill terms to compare a skill.")
else:
    options = summary["term"].tolist()
    if st.session_state.get("focus_skill") not in options:
        st.session_state["focus_skill"] = "sql" if "sql" in options else options[0]
    skill = st.selectbox("Skill of Interest", options, format_func=term_name, key="focus_skill")
    comparison_rows = []
    for name in PATHWAYS:
        group = comparison_data.loc[comparison_data["career_pathway"].eq(name)]
        n = int(group["has_valid_skills"].sum())
        count = sum(skill in set(terms) for terms in group.loc[group["has_valid_skills"], "workshop_skills"])
        rate = count / n if n else None
        note = "No skill information" if not n else ("Small group" if n < 100 else "")
        comparison_rows.append({
            "pathway": name, "rate": rate, "mentions": count,
            "valid_records": n, "label_position": min(rate or 0, 0.72),
            "label": f"{rate:.1%} · n={n}" if n else "N/A · n=0",
            "note": note,
        })
    # A missing rate remains null. Only its text label is placed at zero.
    show_comparison_chart(pd.DataFrame(comparison_rows))
    st.caption("All four pathways use the same target states and analysis scope. Each has its own nonblank-list denominator; N/A means no skill information, not zero demand.")

st.subheader("Skills to Explore")
candidates = top.loc[~top["term"].isin(profile)].head(3)
if top.empty:
    st.info("No learning candidates can be identified from this selection.")
elif candidates.empty:
    st.success("You selected all displayed top terms. Review job examples or another pathway; this does not establish complete job readiness.")
else:
    for number, row in enumerate(candidates.itertuples(index=False), 1):
        st.markdown(f"**{number}. {term_name(row.term)}** — mentioned in {row.rate:.1%} of advertisements with skill information.")
    st.caption("Unselected terms from the displayed ranking, ordered by mention rate. Review examples and discuss interests and prerequisites with a career adviser before choosing a course or project.")

with st.expander("Example Advertisements"):
    only_mentions = st.checkbox("Show only advertisements mentioning the skill of interest", value=True, key="example_mentions")
    examples = selected.copy()
    if only_mentions:
        examples = examples.loc[examples["workshop_skills"].apply(lambda terms: skill in terms if skill else False)]
    st.caption(f"{len(examples):,} matching examples. This table filter does not change metric denominators. Historical links may no longer be available.")
    if examples.empty:
        st.info("No examples match the current table selection.")
    else:
        shown = examples.sort_values(["company", "job_title", "job_link"]).head(50).copy()
        for column in ["workshop_skills", "qualification_like_terms"]:
            shown[column] = shown[column].apply(lambda terms: "; ".join(terms))
        st.caption("Up to 50 examples, sorted by company and title. These examples are not a representative sample.")
        st.dataframe(
            shown[["job_link", "job_title", "company", "job_location", "analysis_scope", "workshop_skills", "qualification_like_terms", "volunteer_title_signal", "possible_duplicate"]],
            hide_index=True,
            column_config={
                "job_title": "Job Title", "company": "Company", "job_location": "Location",
                "analysis_scope": "Analysis Scope", "workshop_skills": "Retained Skill Terms",
                "qualification_like_terms": "Withheld Qualification Terms",
                "volunteer_title_signal": "Volunteer Title Signal", "possible_duplicate": "Possible Duplicate",
                "job_link": st.column_config.LinkColumn("Original Posting", display_text="Open posting", pinned=True, width="small"),
            },
        )

st.divider()
st.subheader("Data Notes and Limitations")
st.markdown("""
- **Historical snapshot:** first observed Jan 12–17, 2024. These are collection dates, not publication dates. The app does not refresh external data or establish current job availability.
- **Unit of analysis:** one row is an advertisement, not a verified unique vacancy or hire. Possible repeated advertisements remain flagged.
- **Eligibility:** title signals and location rules are heuristic. Neither early-career titles nor broader titles confirm experience, degree, or work-authorization eligibility. Volunteer-title flags do not verify compensation.
- **Skill terms:** supplied labels are extracted. A limited alias map and provisional qualification screen remove some inconsistent wording and qualification-like terms; retained labels are not all manually validated requirements.
- **Denominators:** mention rates use nonblank original skill lists, including lists whose qualification-like terms were withheld. Missing lists are excluded from rates and included in advertisement counts.
- **Self-reported coverage:** exact-term overlap with up to eight displayed skills. It is not a proficiency test, hiring probability, or a verified personal skill gap. Selections are retained across filters in the current session; the app does not create a student account or durable profile.
- **Geography:** the all-location view includes unspecified states. Cross-state areas are not forced into one state. Selection rules do not produce a representative U.S. market sample.
- **Small groups:** always check valid-record counts. The display caution is not statistical validation.
- **Unavailable information:** reliable salaries, graduate employment outcomes, student proficiency, and hiring growth cannot be calculated from this input.
""")
st.caption(f"Possible-duplicate flags in this selection: {int(selected['possible_duplicate'].sum()):,} advertisements.")
st.markdown("Source: [1.3M LinkedIn Jobs & Skills (2024), asaniczka on Kaggle](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024)")
