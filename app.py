import base64
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st

# Replace the placeholder with the actual classroom team name.
TEAM_NAME = "Group 3"
TEAM_MEMBERS = "Yuhan Dang, Yanxi Wang, Wenbo Hu, Borui Su"
ASSET_PATH = Path(__file__).resolve().parent / "assets"
DATA_PATH = Path(__file__).resolve().parent / "data" / "career_postings_expanded.csv"
PATHWAYS = [
    "Data and Business Analytics",
    "Finance and Accounting",
    "Marketing",
    "Software Development",
]
SCOPES = {
    "All Selected Job Postings": None,
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

st.set_page_config(page_title="Graduate Career Skills Radar", page_icon="🧭", layout="wide")


def normalize_skill_label(value):
    value = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    # Strip extraction bullets and wrapping quotes, preserving .NET, C++ and C#.
    value = value.strip(" \t\r\n*•·\"'“”‘’`")
    return re.sub(r"\s+", " ", value)


CATALOG_PATH = DATA_PATH.parent / "skill_catalog.json"
CATALOG = json.loads(CATALOG_PATH.read_text())["skills"]
SKILL_LABELS = {entry["id"]: entry["label"] for entry in CATALOG}
SKILL_ALIASES = {
    normalize_skill_label(alias): entry["id"]
    for entry in CATALOG
    for alias in [entry["id"], entry["label"], *entry["aliases"]]
}


def term_name(term):
    return SKILL_LABELS.get(term, TERM_NAMES.get(term, term.capitalize()))


def search_skills(query, available):
    query = normalize_skill_label(query)
    if not query:
        return []
    matches = []
    for entry in CATALOG:
        if entry["id"] not in available:
            continue
        names = [normalize_skill_label(name) for name in [entry["label"], *entry["aliases"]]]
        if any(query in name for name in names):
            priority = 0 if query in names else (1 if any(name.startswith(query) for name in names) else 2)
            matches.append((priority, entry["label"].casefold(), entry["id"]))
    return [term for _, _, term in sorted(matches)]


def select_search_match():
    chosen = st.session_state.get("skill_match")
    if chosen:
        st.session_state["focus_skill"] = chosen


@st.cache_data
def load_data(path, modified_time):
    data = pd.read_csv(path)
    for column in ["workshop_skills", "qualification_like_terms"]:
        data[column] = data[column].apply(json.loads)
    for column in ["has_valid_skills", "has_skill_record",
                   "possible_duplicate", "volunteer_title_signal"]:
        data[column] = data[column].astype(str).str.casefold().eq("true")
    data["source_skill_terms"] = data["workshop_skills"].apply(list)
    data["unmapped_skill_terms"] = data["source_skill_terms"].apply(
        lambda terms: [term for term in terms if normalize_skill_label(term) not in SKILL_ALIASES]
    )
    data["workshop_skills"] = data["source_skill_terms"].apply(
        lambda terms: sorted({SKILL_ALIASES[normalize_skill_label(term)] for term in terms
                              if normalize_skill_label(term) in SKILL_ALIASES})
    )
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
    spec = {**spec, "config": {
                "font": "Open Sans",
                "axis": {"labelFont": "Open Sans", "titleFont": "Open Sans",
                         "labelColor": "#304A65", "titleColor": "#17324D",
                         "gridColor": "#E0E8EF", "labelFontSize": 11, "titleFontSize": 12},
                "legend": {"labelFont": "Open Sans", "labelColor": "#304A65", "labelFontSize": 11},
                "title": {"font": "Oswald", "color": "#00539F", "fontSize": 19},
                "view": {"stroke": None},
            }, "data": {"values": records},
            "autosize": {"type": "fit-x", "contains": "padding"}}
    identity = json.dumps(spec, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
    with st.container(key=f"chart_{chart_name}_{digest}"):
        st.vega_lite_chart(spec=spec, width="stretch", key=f"{chart_name}_{digest}", theme=None)


def show_skill_chart(frame):
    spec = {
        "height": {"step": 24},
        "encoding": {
            "y": {"field": "skill", "type": "nominal", "sort": None,
                  "axis": {"title": None, "labelLimit": 190}},
            "x": {"field": "rate", "type": "quantitative",
                  "scale": {"domain": [0, 1]},
                  "axis": {"title": "Job Postings mentioning the term (%)", "format": ".0%"}},
        },
        "layer": [
            {"mark": {"type": "bar", "cornerRadiusEnd": 4},
             "encoding": {
                 "color": {"field": "profile_status", "type": "nominal",
                           "scale": {"domain": ["Selected as current", "Not selected"],
                                     "range": ["#FFD200", "#00539F"]},
                           "legend": {"title": None, "orient": "top"}},
                 "tooltip": [
                     {"field": "skill", "title": "Skill term"},
                     {"field": "rate", "title": "Mention rate", "format": ".1%"},
                     {"field": "mentions", "title": "Job Postings mentioning term"},
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
                  "axis": {"title": "Job Postings mentioning the term (%)", "format": ".0%"}},
        },
        "layer": [
            {"mark": {"type": "bar", "color": "#00539F", "cornerRadiusEnd": 4},
             "encoding": {"tooltip": [
                 {"field": "pathway", "title": "Career pathway"},
                 {"field": "rate", "title": "Mention rate", "format": ".1%"},
                 {"field": "mentions", "title": "Job Postings mentioning term"},
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




@st.cache_data
def asset_data_url(path, modified_time):
    file = Path(path)
    mime = {".ttf": "font/ttf", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg"}.get(file.suffix, "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(file.read_bytes()).decode()


def asset_url(name):
    file = ASSET_PATH / name
    return asset_data_url(str(file), file.stat().st_mtime_ns) if file.exists() else ""


def show_project_meta():
    st.html(
        '<div class="project-meta">'
        f'<div class="project-team"><strong>{escape(TEAM_NAME)}:</strong> {escape(TEAM_MEMBERS)}</div>'
        '<div>For U.S. university students exploring career pathways and choosing their next skill-learning topic.</div>'
        '<div>Data: first observed Jan 12–17, 2024, Kaggle snapshot. Proposed production refresh: weekly. '
        'Skill selections are self-reported; job eligibility is unverified.</div></div>'
    )


def open_dashboard():
    st.query_params["view"] = "dashboard"


def open_introduction():
    st.query_params["view"] = "welcome"


font_rules = ""
for name, filename in [("Open Sans", "fonts/OpenSans.ttf"), ("Oswald", "fonts/Oswald.ttf")]:
    font_source = asset_url(filename)
    if font_source:
        font_rules += f"@font-face {{font-family:'{name}';src:url('{font_source}') format('truetype');font-weight:100 900;font-style:normal;font-display:swap;}}"

st.html("<style>" + font_rules + """
:root {--career-blue:#00539f;--career-gold:#ffd200;--career-ink:#17324d;--career-muted:#526578;--career-line:#dbe4ed;}
.stApp {font-family:'Open Sans',Arial,sans-serif;color:var(--career-ink);}
.stApp input,.stApp button,.stApp select,.stApp textarea,.stApp [data-baseweb="select"] {font-family:'Open Sans',Arial,sans-serif;}
.stMainBlockContainer {max-width:1440px;padding-top:3.75rem;padding-bottom:2rem;}
.stMainBlockContainer h1,.stMainBlockContainer h2,.stMainBlockContainer h3 {font-family:'Oswald','Arial Narrow',Arial,sans-serif;color:var(--career-blue);font-weight:600;}
.stMainBlockContainer h1 {font-size:2rem;line-height:1.35;padding:0;margin:0;}
.stMainBlockContainer h3 {font-size:1.25rem;line-height:1.45;padding:0;margin:0;}
.stMainBlockContainer [data-testid="stVerticalBlock"] {gap:.75rem;}
.stMainBlockContainer [data-testid="stCaptionContainer"] {line-height:1.6;color:var(--career-muted);}
.stMainBlockContainer [data-testid="stMarkdownContainer"] p {line-height:1.6;}
.stMainBlockContainer [data-testid="stMetricValue"] {font-family:'Oswald',Arial,sans-serif;font-size:2rem;color:var(--career-blue);}
.st-key-metrics [data-testid="stMetric"] {border-radius:12px;border-top:3px solid var(--career-gold);background:#f8fafc;}
.st-key-skills {border-radius:14px;border-left:4px solid var(--career-blue);background:#f7f9fc;}
.st-key-skills [data-testid="stVerticalBlock"] {gap:.65rem;}
.st-key-current_skills button {border-radius:999px;padding:.35rem .8rem;}
.st-key-current_skills button[aria-pressed="true"],.st-key-current_skills button[aria-checked="true"] {background-color:#fff4b3!important;color:#17324d!important;border-color:#9c7d00!important;}
.stMainBlockContainer [data-baseweb="select"] > div {border-radius:12px;}
.st-key-primary {margin-top:.25rem;}
.st-key-primary h3,.st-key-comparison h3 {border:0;}
.section-heading {border-left:4px solid var(--career-gold);padding-left:.7rem;margin:0;}
.section-heading h2 {font-size:1.3rem;line-height:1.4;padding:0;margin:0;}
.st-key-data_notes {border-top:3px solid var(--career-blue);padding-top:1rem;}
.st-key-data_notes [data-testid="stCaptionContainer"] {font-size:.875rem;line-height:1.6;color:var(--career-muted);}
.brand-bar {display:flex;align-items:center;justify-content:space-between;gap:1rem;background:var(--career-blue);color:#fff;border-bottom:4px solid var(--career-gold);padding:.65rem 1rem;}
.brand-identity {display:flex;align-items:center;gap:.6rem;font-family:'Oswald',Arial,sans-serif;font-size:1.1rem;letter-spacing:.05em;}
.brand-identity img {width:30px;height:30px;}
.brand-context {font-family:'Open Sans',Arial,sans-serif;font-size:.75rem;line-height:1.5;}
.project-meta {display:grid;gap:.3rem;font-size:.78rem;line-height:1.65;color:var(--career-muted);text-align:left;}
.project-team {text-align:left;}
.st-key-welcome_canvas {border-radius:18px;padding:1.5rem;background:linear-gradient(130deg,#eff6fc 0%,#fff 65%,#fff8d9 100%);}
.hero-photo {display:block;width:100%;height:auto;object-fit:contain;border-radius:16px;}
.landing-eyebrow {font-size:.72rem;line-height:1.6;letter-spacing:.1em;font-weight:700;color:var(--career-blue);text-transform:uppercase;margin:0 0 .75rem;}
.landing-title {font-family:'Oswald',Arial,sans-serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:600;line-height:1.3;color:var(--career-blue);margin:0 0 1rem;}
.stMainBlockContainer .landing-title {margin-bottom:.75rem;}
.landing-description {font-size:.98rem;line-height:1.7;max-width:780px;color:var(--career-ink);margin:0;}
.st-key-enter_dashboard button {background:var(--career-gold);color:var(--career-ink);border:0;border-radius:999px;font-weight:700;min-height:48px;padding:.65rem 1.4rem;box-shadow:0 3px 10px #17324d12;}
.st-key-enter_dashboard button:hover {background:#ffe36a;color:var(--career-ink);box-shadow:0 4px 14px #17324d20;}
.st-key-intro_return button {border:0;background:transparent;border-radius:999px;color:var(--career-blue);padding:.45rem .8rem;}
.st-key-intro_return button:hover {background:#edf4fb;}
.st-key-landing_steps {padding:.75rem 0;}
.st-key-landing_steps h3 {font-size:1.1rem;line-height:1.5;}
.landing-step h3 {margin:0 0 .5rem!important;}
.landing-step p {font-size:.8rem;line-height:1.7;color:var(--career-muted);margin:0;}
.project-footer {font-size:.75rem;line-height:1.6;color:var(--career-muted);border-top:1px solid var(--career-line);padding-top:.75rem;margin-top:.4rem;}
@media(max-width:1050px) {
 .st-key-primary [data-testid="stHorizontalBlock"] {flex-direction:column;}
 .st-key-primary [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {width:100%;flex:1 1 auto;min-width:0;}
}
@media(max-width:760px) {
 .st-key-landing_intro [data-testid="stHorizontalBlock"],.st-key-landing_steps [data-testid="stHorizontalBlock"] {gap:1.25rem!important;}
 .st-key-landing_intro [data-testid="stHorizontalBlock"],.st-key-landing_steps [data-testid="stHorizontalBlock"] {flex-direction:column;}
 .st-key-landing_intro [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],.st-key-landing_steps [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {width:100%;flex:1 1 auto;min-width:0;}
}
@media(max-width:640px) {
 .stMainBlockContainer {padding-left:1rem;padding-right:1rem;padding-top:3.75rem;}
 .stMainBlockContainer h1 {font-size:1.6rem;}.brand-bar {align-items:flex-start;flex-direction:column;gap:.3rem;}
 .st-key-welcome_canvas {padding:1rem;}.landing-title {font-size:2rem;}
 .st-key-filters [data-testid="stHorizontalBlock"],.st-key-metrics [data-testid="stHorizontalBlock"] {flex-direction:column;}
 .st-key-filters [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],.st-key-metrics [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {width:100%;flex:1 1 auto;min-width:0;}
}
</style>
""")

icon_url = asset_url("career-compass.svg")
st.html(
    '<div class="brand-bar"><div class="brand-identity">'
    + (f'<img src="{icon_url}" alt="Career compass">' if icon_url else '')
    + '<span>CAREER SKILLS RADAR</span></div>'
    + '<span class="brand-context">University of Delaware student project · Group 3</span></div>'
)

if st.query_params.get("view", "welcome") != "dashboard":
    with st.container(key="welcome_canvas"):
        with st.container(key="landing_intro"):
            illustration, introduction = st.columns([1.25, 1], gap="large", vertical_alignment="center")
            with illustration:
                hero = asset_url("career-exploration.png")
                if hero:
                    st.html(f'<img class="hero-photo" src="{hero}" alt="Illustration of a student connecting current skills with data, finance, marketing and software career directions">')
            with introduction:
                st.html('<div class="landing-eyebrow">Career exploration, informed by job postings</div><h1 class="landing-title">Find the skills for your next step.</h1><p class="landing-description">Explore your career pathways, compare skill mentions in historical job postings, and select topics to discuss with a career adviser or learn next.</p>')
                st.button("Explore the Dashboard →", type="primary", width="content", key="enter_dashboard", on_click=open_dashboard)
        with st.container(key="landing_steps"):
            steps = st.columns(3, gap="large")
            for column, title, description in zip(steps,
                ["01 / Choose your direction", "02 / Select your skills", "03 / Investigate your next topic"],
                ["Pick a career pathway, target states, and title-based scope.",
                 "Mark frequent terms that describe your current skills.",
                 "Compare mentions and inspect real job posting examples."]):
                with column:
                    st.html(f'<div class="landing-step"><h3>{escape(title)}</h3><p>{escape(description)}</p></div>')
        show_project_meta()
        st.caption("AI-generated illustration of career exploration and skill learning; not a real student scene or a representation of the dataset.")
    st.html('<div class="project-footer">Independent class project. Not an official University of Delaware service.</div>')
    st.stop()

heading_column, home_column = st.columns([5, 1])
with heading_column:
    st.title("Graduate Career Skills Radar")
with home_column:
    st.button("← Introduction", key="intro_return", on_click=open_introduction, width="content")
show_project_meta()

if not DATA_PATH.exists():
    st.error("The dashboard CSV is missing from the project's data folder.")
    st.stop()
data = load_data(str(DATA_PATH), (DATA_PATH.stat().st_mtime_ns, CATALOG_PATH.stat().st_mtime_ns))

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
    metrics[0].metric("Selected Job Postings", f"{len(selected):,}", border=True)
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
    st.info("No job postings match this selection. Change the pathway, state, or analysis scope.")
elif valid_count < 100:
    st.warning("Small selection: fewer than 100 nonblank skill lists. Treat percentages as exploratory.")

with st.container(key="primary"):
    skill_column, next_column = st.columns([2.1, 1], gap="large")
    with skill_column:
        st.html('<div class="section-heading"><h2>Top Skill Mentions</h2></div>')
        st.caption("Up to eight terms. Hover to inspect counts and selection status.")
        if top.empty:
            st.info("No retained skill ranking is available.")
        else:
            top["profile_status"] = top["term"].apply(lambda term: "Selected as current" if term in profile else "Not selected")
            top["label_position"] = top["rate"].clip(upper=0.86)
            show_skill_chart(top)
    with next_column:
        st.html('<div class="section-heading"><h2>Skills to Explore</h2></div>')
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
with st.container(key="comparison"):
    st.html('<div class="section-heading"><h2>Where Else Is This Skill Mentioned?</h2></div>')
    st.caption("Explore whether a learning topic appears in other career directions.")
    available_skills = set(term for terms in data["workshop_skills"] for term in terms)
    if not available_skills:
        skill = None
        st.info("No catalogued skill terms are available in the dataset.")
    else:
        if st.session_state.get("focus_skill") not in available_skills:
            st.session_state["focus_skill"] = "sql" if "sql" in available_skills else sorted(available_skills)[0]
        st.caption("Type a skill name or a few letters, press Enter, then select a matching skill.")
        query = st.text_input("Search the Skill Library", key="skill_search",
                              placeholder="Try pyt, SQL, C or project management",
                              help="Type part of a skill name and press Enter. Select a suggestion to update the comparison.")
        matches = search_skills(query, available_skills)
        if query.strip():
            if matches:
                shown_matches = matches[:12]
                if st.session_state.get("skill_match") not in shown_matches:
                    st.session_state["skill_match"] = None
                st.pills("Matching skills", shown_matches, format_func=term_name,
                         selection_mode="single", key="skill_match", wrap=True,
                         on_change=select_search_match)
                if len(matches) > 12:
                    st.caption(f"Showing 12 of {len(matches)} matches. Type a more specific name to narrow the results.")
            else:
                st.info("No matching skill in the current library. Try another name; the library can be expanded after review.")
        else:
            st.caption("Search by name, then select a suggestion. The library covers skills observed across the full dataset.")
        skill = st.session_state["focus_skill"]
        st.markdown(f"**Selected skill: {term_name(skill)}**")
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

with st.expander("Example Job Postings"):
    only_mentions = st.checkbox("Show only job postings mentioning the skill of interest", value=True, key="example_mentions")
    examples = selected.copy()
    if only_mentions:
        examples = examples.loc[examples["workshop_skills"].apply(lambda terms: skill in terms if skill else False)]
    st.caption(f"{len(examples):,} matching examples. This table filter does not change metric denominators. Historical links may no longer be available.")
    if examples.empty:
        st.info("No examples match the current table selection.")
    else:
        shown = examples.sort_values(["company", "job_title", "job_link"]).head(50).copy()
        for column in ["workshop_skills", "qualification_like_terms", "source_skill_terms", "unmapped_skill_terms"]:
            shown[column] = shown[column].apply(lambda terms: "; ".join(terms))
        st.caption("Up to 50 examples, sorted by company and title. These examples are not a representative sample.")
        st.dataframe(
            shown[["job_link", "job_title", "company", "job_location", "analysis_scope", "workshop_skills", "source_skill_terms", "unmapped_skill_terms", "qualification_like_terms", "volunteer_title_signal", "possible_duplicate"]],
            hide_index=True,
            column_config={
                "job_title": "Job Title", "company": "Company", "job_location": "Location",
                "analysis_scope": "Analysis Scope", "workshop_skills": "Retained Skill Terms",
                "source_skill_terms": "Original Retained Extracted Terms", "unmapped_skill_terms": "Terms Outside Skill Library",
                "qualification_like_terms": "Withheld Qualification Terms",
                "volunteer_title_signal": "Volunteer Title Signal", "possible_duplicate": "Possible Duplicate",
                "job_link": st.column_config.LinkColumn("Original Posting", display_text="Open posting", pinned=True, width="small"),
            },
        )

st.divider()
with st.container(key="data_notes"):
    st.markdown("**Data Notes and Limitations**")
    st.caption("**Source & period.** LinkedIn job postings first observed Jan 12–17, 2024. Observation dates are not publication dates. This historical CSV does not refresh or establish current availability; original links may have expired. Proposed production refresh: weekly.")
    st.caption("**Interpretation.** Extracted mentions are not verified mandatory requirements. Title signals do not confirm graduate eligibility. A maintained skill library accepts only exact names and listed aliases after stripping bullets and wrapping quotes. Unmatched terms are withheld from rankings and search, and remain available alongside original terms in examples. The library is incomplete and requires review. Volunteer signals do not establish pay.")
    st.caption("**Personal coverage.** Self-reported exact-term overlap with up to eight displayed terms, not proficiency, job readiness, or hiring probability. Selections persist only in the current session. Unselected terms are discussion candidates, not diagnosed deficiencies.")
    st.caption("**Sample quality.** Counts describe job postings, not verified unique vacancies. Mention-rate denominators use nonblank original skill lists; withheld qualifications do not shrink them. Small groups and possible repeats can affect rates. Geographic/title rules are heuristic, and unspecified states remain in the all-location view. This is not a representative market sample.")
    st.caption("**Unavailable data.** Reliable salary, student proficiency, graduate employment outcomes, and hiring growth are unavailable. A missing denominator is shown as N/A rather than zero demand.")
    st.caption(f"This selection: {valid_count:,} nonblank skill lists; {int(selected['possible_duplicate'].sum()):,} job postings flagged as possible repeats. The 100-record caution is not statistical validation.")
    st.caption("Source: [1.3M LinkedIn Jobs & Skills (2024), asaniczka on Kaggle](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024)")

st.html('<div class="project-footer">Independent class project. Not an official University of Delaware service. Open Sans and Oswald are distributed with their SIL Open Font License notices.</div>')
