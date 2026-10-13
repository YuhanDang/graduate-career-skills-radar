import hashlib
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

st.set_page_config(page_title="Graduate Career Skills Radar", layout="wide")


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



def render_chart(frame, spec, chart_name):
    records = json.loads(frame.to_json(orient="records"))
    spec = {**spec, "data": {"values": records},
            "autosize": {"type": "fit-x", "contains": "padding"}}
    identity = json.dumps(spec, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
    with st.container(key=f"chart_{chart_name}_{digest}"):
        st.vega_lite_chart(spec=spec, width="stretch", key=f"{chart_name}_{digest}")


def show_skill_chart(frame):
    spec = {
        "height": {"step": 27},
        "encoding": {
            "y": {"field": "skill", "type": "nominal", "sort": None,
                  "axis": {"title": None, "labelLimit": 190}},
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
    render_chart(frame, spec, "top-skills")


def show_comparison_chart(frame, skill):
    spec = {
        "height": {"step": 36},
        "encoding": {
            "y": {"field": "pathway", "type": "nominal", "sort": None,
                  "axis": {"title": None, "labelLimit": 190}},
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
    spec["title"] = {"text": term_name(skill), "anchor": "start"}
    render_chart(frame, spec, "cross-pathway")



st.markdown("""
<style>
.stMainBlockContainer {max-width: 1440px; padding-top: 4rem; padding-bottom: 2rem;}
.stMainBlockContainer h1 {font-size: 1.85rem; line-height: 1.25; padding-top: 0; padding-bottom: .15rem;}
.stMainBlockContainer h3 {font-size: 1.15rem; line-height: 1.3; padding-top: .1rem; padding-bottom: .15rem;}
.stMainBlockContainer [data-testid="stVerticalBlock"] {gap: .5rem;}
.stMainBlockContainer [data-testid="stMetricValue"] {font-size: 1.9rem;}
.st-key-skills [data-testid="stVerticalBlock"] {gap: .25rem;}
.st-key-primary {margin-top: .15rem;}
.st-key-data_notes [data-testid="stCaptionContainer"] {font-size: .875rem; line-height: 1.5;}
@media (max-width: 1050px) {
  .st-key-primary [data-testid="stHorizontalBlock"] {flex-direction: column;}
  .st-key-primary [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {width: 100%; flex: 1 1 auto; min-width: 0;}
}
@media (max-width: 640px) {
  .stMainBlockContainer {padding-left: 1rem; padding-right: 1rem; padding-top: 3.75rem;}
  .stMainBlockContainer h1 {font-size: 1.45rem;}
  .st-key-filters [data-testid="stHorizontalBlock"],
  .st-key-metrics [data-testid="stHorizontalBlock"] {flex-direction: column;}
  .st-key-filters [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  .st-key-metrics [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {width: 100%; flex: 1 1 auto; min-width: 0;}
}
</style>
""", unsafe_allow_html=True)

st.title(f"Graduate Career Skills Radar — {TEAM_NAME}")
st.caption("For U.S. university students exploring career pathways and choosing their next skill-learning topic.")
st.caption("Historical data: first observed Jan 12–17, 2024 · Kaggle snapshot · Proposed refresh: weekly · Review weekly during career preparation.")

if not DATA_PATH.exists():
    st.error("The dashboard CSV is missing from the project's data folder.")
    st.stop()
data = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)

with st.container(key="filters"):
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
            help="Leave empty for all selected U.S. locations, including unspecified states.",
        )

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
with st.container(border=True, key="skills"):
    st.subheader("My Current Skills")
    st.caption("Select your current skills from these frequent terms. Self-reported; not a proficiency test.")
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
with st.container(key="metrics"):
    metrics = st.columns(3)
    metrics[0].metric("Selected Advertisements", f"{len(selected):,}", border=True)
    metrics[1].metric("Skill Information Coverage", f"{information_coverage:.1%}" if information_coverage is not None else "N/A", border=True)
    metrics[2].metric(
        "Top-Skill Coverage",
        f"{profile_coverage:.1%}" if profile_coverage is not None else "N/A",
        border=True, help="Selected displayed skill terms divided by the number of displayed terms. Not a qualification or hiring score.",
    )

context_note = f"{valid_count:,} nonblank skill lists · {selected_top_count}/{len(top)} displayed terms selected. Extracted mentions, not verified requirements."
if not profile and len(top):
    context_note += " No skills selected: 0% reflects input, not ability."
if SCOPES[scope_label] != "Explicit Early-Career Title Signal":
    context_note += " Broader-title eligibility is unverified."
st.caption(context_note)

if selected.empty:
    st.info("No advertisements match this selection. Change the pathway, state, or analysis scope.")
elif valid_count < 100:
    st.warning("Small selection: fewer than 100 nonblank skill lists. Treat percentages as exploratory.")

with st.container(key="primary"):
    skill_column, next_column = st.columns([2.1, 1], gap="large")
    with skill_column:
        st.subheader("Top Skill Mentions")
        st.caption("Up to eight terms. Hover to inspect counts and selection status.")
        if top.empty:
            st.info("No retained skill ranking is available.")
        else:
            top["profile_status"] = top["term"].apply(lambda term: "Selected as current" if term in profile else "Not selected")
            top["label_position"] = top["rate"].clip(upper=0.86)
            show_skill_chart(top)
    with next_column:
        st.subheader("Skills to Explore")
        st.caption("Topics to investigate next — based on unselected terms.")
        candidates = top.loc[~top["term"].isin(profile)].head(3)
        if top.empty:
            st.info("No learning candidates can be identified from this selection.")
        elif candidates.empty:
            st.success("You selected all displayed top terms. Review job examples or another pathway; this does not establish complete job readiness.")
        else:
            for number, row in enumerate(candidates.itertuples(index=False), 1):
                st.markdown(f"**{number}. {term_name(row.term)}**")
                st.caption(f"Mentioned in {row.rate:.1%} · {row.mentions} of {row.valid_records} nonblank lists")
            st.caption("Review examples, then discuss interests and prerequisites with a career adviser before choosing a course or project.")

st.divider()
st.subheader("Where Else Is This Skill Mentioned?")
st.caption("Explore whether a learning topic appears in other career directions.")
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
    location_label = ", ".join(STATE_NAMES.get(code, "Unspecified") for code in states) if states else "All selected U.S. locations"
    st.caption(f"Showing: {term_name(skill)} · {location_label} · {scope_label}")
    show_comparison_chart(pd.DataFrame(comparison_rows), skill)
    st.caption("All four pathways use the same target states and analysis scope. Each has its own nonblank-list denominator; N/A means no skill information, not zero demand.")

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
with st.container(key="data_notes"):
    st.markdown("**Data Notes and Limitations**")
    st.caption("**Source & period.** LinkedIn advertisements first observed Jan 12–17, 2024. Observation dates are not publication dates. This historical CSV does not refresh or establish current availability; original links may have expired. Proposed production refresh: weekly.")
    st.caption("**Interpretation.** Extracted mentions are not verified mandatory requirements. Title signals do not confirm graduate eligibility. Alias and qualification screening are provisional; originals and withheld terms remain available in examples. Volunteer signals do not establish pay.")
    st.caption("**Personal coverage.** Self-reported exact-term overlap with up to eight displayed terms, not proficiency, job readiness, or hiring probability. Selections persist only in the current session. Unselected terms are discussion candidates, not diagnosed deficiencies.")
    st.caption("**Sample quality.** Counts describe advertisements, not verified unique vacancies. Mention-rate denominators use nonblank original skill lists; withheld qualifications do not shrink them. Small groups and possible repeats can affect rates. Geographic/title rules are heuristic, and unspecified states remain in the all-location view. This is not a representative market sample.")
    st.caption("**Unavailable data.** Reliable salary, student proficiency, graduate employment outcomes, and hiring growth are unavailable. A missing denominator is shown as N/A rather than zero demand.")
    st.caption(f"This selection: {valid_count:,} nonblank skill lists; {int(selected['possible_duplicate'].sum()):,} advertisements flagged as possible repeats. The 100-record caution is not statistical validation.")
    st.caption("Source: [1.3M LinkedIn Jobs & Skills (2024), asaniczka on Kaggle](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024)")
