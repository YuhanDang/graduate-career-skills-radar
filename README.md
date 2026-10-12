# Graduate Career Skills Radar

A career-readiness workshop planning dashboard for a U.S. university.

**Team name:** [Add team name]  
**Live app:** [Add deployed app URL]  
**Repository:** [Add public GitHub repository URL]

**Implementation status:** Data preparation, EDA, and the first Streamlit implementation are complete. Deployment is pending; the team-name placeholder must be replaced before submission.

## Step 1 — Dataset and Decision-Maker

### Dataset and provenance

I independently selected [1.3M LinkedIn Jobs & Skills (2024) by asaniczka on Kaggle](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024) for my individual project. The source contains real-world LinkedIn job advertisements and extracted skill terms, rather than synthetic employment outcomes.

I use the postings and skills CSVs, joined by `job_link`. One row in the final dataset represents one job advertisement, not necessarily a distinct vacancy or hire. The source postings have first-seen dates from **January 12–17, 2024**. These are observation dates, not verified publication dates; the dataset does not establish how long each job was open.

The original postings file contains 1,348,454 rows. To keep the app small, I selected advertisements using reproducible location and title rules in the EDA notebook, then exported **one dashboard input CSV containing 4,766 rows and 19 columns, approximately 5.484 MB**. This is rule-based selection, not a random or representative sample of the U.S. labor market.

### Audience and scope

The primary user is the **Director of Career Services at a U.S. university serving students in business, computing, and related programs**. The director plans career-readiness workshops and coordinates with advisers and employer partners.

The dashboard covers four career pathways: Data and Business Analytics, Finance and Accounting, Marketing, and Software Development.

U.S. locations are inferred from `job_location` using explicit country names, state abbreviations, and a documented metropolitan-area list. Ambiguous locations are excluded. `search_country` is search metadata and is not used as proof that a job is located in the United States.

Of the selected advertisements, **354 have explicit early-career title signals** and **4,412 match selected broader titles with eligibility unverified**. Broader titles are exact normalized-title matches from the unclear-stage group. They provide workshop-planning context but are not classified as confirmed entry-level opportunities. Neither group has been verified against full descriptions for experience, degree, or work-authorization eligibility.

## Step 2 — Why a Dashboard?

### Who reviews it, and how often?

The director would review the production dashboard **monthly**, before planning the next cycle of workshops. The same questions recur: which skills deserve attention, which pathways share them, and whether the evidence comes from explicit early-career titles or broader roles.

### What decision does it support?

**If the Director of Career Services sees a frequently mentioned, teachable skill in a relevant pathway, they will review existing workshop coverage and decide whether to add, revise, or combine a workshop, considering student interest, staffing, and budget.**

For example, frequent SQL mentions in selected analytics advertisements would prompt a review of SQL workshop coverage and consultation with advisers. The dashboard does not by itself establish a student skill gap or prove that a workshop will improve employment outcomes.

### What happens without it?

In the assumed customer workflow, staff manually review advertisements, collect adviser observations, and maintain separate spreadsheets of possible workshop topics. Repeating this process consumes staff time and makes comparisons between pathways inconsistent. It can also lead staff to prioritize memorable examples rather than systematically counted evidence.

This workflow is a business hypothesis, not a measured finding from a university interview. No numerical time savings or financial return is claimed.

### Why not an email, report, or alert?

A report or poster can describe this historical snapshot once. The production dashboard earns its place through **regularly updated evidence and repeated comparisons during planning**: the director can change the pathway, analysis scope, and skill of interest without requesting a new report for each combination.

An email can distribute a summary, but cannot provide those comparisons directly. An alert can identify a change, but cannot provide enough context to decide which workshop to schedule. The frozen Kaggle app demonstrates the intended workflow; it does not currently monitor a changing market.

### Commercial application

The potential customer is a university Career Services office, with the director as the primary user and students as beneficiaries. A possible institutional subscription would provide refreshed advertisement data and consistent workshop-planning comparisons. The recurring programming decision provides a plausible customer need; purchasing demand, pricing, and willingness to pay still require interviews and a pilot. A production service would require a sustainable, appropriately licensed data source.

## Step 3 — EDA and Dashboard Design

### EDA findings

The Pandas and Matplotlib notebook examines dataset shape, data types, missing values, categorical distributions, title signals, skill frequencies, and relationships between career pathway, analysis scope, and skill mentions.

The source posting links and skill links are unique. The skill-record match rate is **96.14%**, but a matched record can still have a blank skill list. In the final selection, **4,697 advertisements have nonblank original skill lists**, while 69 do not.

| Career pathway | Explicit early-career title signals | Broader title matches | Total advertisements | Nonblank skill lists |
| --- | ---: | ---: | ---: | ---: |
| Data and Business Analytics | 94 | 1,261 | 1,355 | 1,323 |
| Finance and Accounting | 167 | 2,336 | 2,503 | 2,486 |
| Marketing | 41 | 209 | 250 | 240 |
| Software Development | 52 | 606 | 658 | 648 |
| **Total** | **354** | **4,412** | **4,766** | **4,697** |

Analysis scope materially affects interpretation. SQL appears in **45.1%** of valid explicit early-career skill lists in analytics, compared with **33.2%** in the broader-title group. Marketing project management mentions are **25.0%** and **46.0%**, respectively. These are differences between selected groups, not changes over time. This finding justifies an analysis-scope control.

### Three headline metrics

The three metrics appear side by side using `st.metric` within `st.columns`.

| Metric | Definition | Decision value |
| --- | --- | --- |
| Selected Advertisements | Advertisement count in the selected pathway and scope | Shows how much evidence supports the view |
| Skill Information Coverage | Advertisements with nonblank original skill lists divided by all selected advertisements | Shows whether missing information weakens interpretation |
| Selected Skill Mention Rate | Valid-skill advertisements mentioning the selected retained term divided by all valid-skill advertisements in the same pathway and scope | Shows how frequently the skill appears in the available evidence |

Each skill counts at most once per advertisement. Selecting a skill does not first remove advertisements that lack it. Missing skill lists are not interpreted as evidence that a skill is unnecessary.

### Two supporting charts

1. **Top Skill Mentions in the Selected Pathway:** a horizontal bar chart of up to eight retained terms, to help identify workshop topics. It breaks down the evidence behind the headline metrics.
2. **Selected Skill Across Career Pathways:** a bar chart showing the selected skill's mention rate across all four pathways, to help decide whether a workshop could serve multiple groups. It uses the selected state selection and analysis scope and displays each pathway's valid-record count.

The second chart intentionally compares all pathways rather than following the pathway selector; its caption explains this. No historical movement is claimed from this snapshot.

### Necessary controls

- **Target State:** a multi-select control for geographic markets relevant to the university. Leaving it empty includes all selected U.S. locations, including records with unspecified state. State selection affects all metrics, both charts, and examples. Explicit state codes and a limited reviewed label map assign states to 4,612 advertisements; 154 remain unspecified. Cross-state metropolitan labels are not forced into one state.
- **Career Pathway:** focuses planning on a relevant student career direction.
- **Analysis Scope:** separates all selected advertisements, explicit early-career title signals, and broader title matches with eligibility unverified.
- **Skill of Interest:** supports investigation of a specific workshop topic and its relevance across pathways.

### Two things deliberately excluded

- **Daily hiring growth:** first-seen dates reflect a short observation window and cannot reliably measure hiring growth.
- **Remote-work share:** work arrangement does not directly guide workshop-topic selection, and the source is heavily concentrated in onsite records.

### Misleading data and how the design handles it

| Issue | Handling |
| --- | --- |
| Historical snapshot | Show the observation period and clearly distinguish intended production refresh from actual updates |
| Unverified graduate eligibility and inconsistent `job_level` labels | Preserve title-based scope labels; explain that neither title rules nor `job_level` confirm eligibility |
| Extracted labels include qualifications and inconsistent wording | Normalize case and whitespace; merge a small set of aliases; withhold rule-flagged degree, authorization, and similar terms from rankings while preserving raw information |
| Missing skill lists | Display coverage; calculate mention rates using nonblank original lists, even after qualification-like terms are withheld |
| Small groups and unequal coverage | Show valid-record counts and flag small groups; avoid interpreting percentages as precise market estimates |
| Possible repeated advertisements | Retain flagged records, label counts as advertisements, and disclose the sensitivity analysis |
| Volunteer advertisements and old links | Identify volunteer-title signals in examples; do not imply that listed jobs are paid or still available |
| Heuristic pathway and location selection | Document the rules and acknowledge omissions and possible classification errors |

**Duplicate sensitivity:** 872 advertisements belong to possible duplicate groups based on normalized company, title, and location. Matching these fields does not prove that they represent one vacancy, so they were not automatically deleted. An alternative calculation counted each group once and combined its retained skill terms. Among the advertisement-level top ten skills in each pathway and scope, the largest absolute change was **5.78 percentage points**, for early-career Software Development JavaScript (34.69% to 40.48%). This alternative is a sensitivity check, not validated deduplication.

### Page order

**Top:** title with team name, one-line audience caption, data-period line, essential controls, and the three headline metrics. The director first sees the size and completeness of the evidence and the prominence of the selected skill. The prototype cannot establish whether something changed or is wrong "right now."

**Middle:** the two charts explain the skill pattern and its relevance across pathways.

**Bottom:** expandable example advertisements and data notes let the director verify the evidence before discussing a workshop with advisers or employer partners. Examples show titles, companies, original locations, analysis scopes, retained terms, withheld qualifications, volunteer signals, possible-duplicate flags, and clickable original LinkedIn URLs. A checkbox restricts examples to advertisements mentioning the selected skill without changing headline denominators. Up to 50 examples are shown, sorted by company and title. Historical links may no longer work.

A paper sketch of this layout must be completed before writing the app.

**Dashboard audience caption:**

> For U.S. university Career Services directors planning skill workshops across four career pathways.

## Step 4 — Refresh Frequency and Action

### Data refresh

The production dashboard would refresh **weekly**. Workshop planning does not require minute-by-minute updates, and weekly collection provides recent evidence without the complexity of real-time processing. The submitted prototype uses a fixed Kaggle CSV and does not actually refresh external data.

### Review frequency

The director would review it **monthly**, when allocating workshop resources. Refresh and review are different: weekly updates prepare the evidence, while monthly reviews align with the decision cycle.

### Tracked metric and action trigger

Production would track skill mention rates in comparable, non-overlapping monthly collection cohorts, keeping pathway definitions, analysis scope, extraction methods, and duplicate handling consistent.

A proposed trigger is a rise of at least **10 percentage points** from the previous month, with at least **100 advertisements containing usable skill lists in each compared cohort**. If the increase persists at the next monthly review, the director would contact advisers and employer partners to validate the signal and review workshop coverage before committing resources.

The threshold is a proposed operating rule, not an empirically validated result. Small groups remain exploratory. This snapshot cannot test the rule, so the prototype will not display invented trend deltas or alerts.

### Cost of stale data

A one-day delay would usually have little effect on monthly scheduling. A one-week delay could omit recent signals from a planning meeting. Sustained staleness could lead staff to repeat outdated workshop topics and overlook emerging skills, wasting limited programming capacity. These are plausible operational costs, not measured financial losses.

**Dashboard freshness line:**

> Data: first observed Jan 12–17, 2024, Kaggle snapshot. Proposed production refresh: weekly; planning review: monthly.

## Project Files and Submission Status

- `app.py`: the Streamlit dashboard with four planning controls, three metrics, two charts, and linked advertisement examples.
- `notebooks/eda.ipynb`: EDA, selection rules, skill processing, sensitivity analysis, and CSV export.
- `data/career_postings_expanded.csv`: the single intended dashboard input, below approximately 25 MB.
- `pyproject.toml` and `uv.lock`: the project initialized with `uv`, including dependencies and Python requirements.
- `README.md`: the written decisions and justifications for Steps 1–4.

The earlier 354-row export is local reference material; the expanded CSV is the intended deployment input. Original downloaded files are not intended for the public repository.

Before submission, complete the required paper sketch if not already done, replace the team-name placeholder in `app.py`, visually review the app, publish the individual public repository, and deploy with **Python 3.14** selected in Streamlit Cloud Advanced settings. Update this document to match the finished app and replace the URL placeholders. Submit the deployed app URL and GitHub repository URL individually on Canvas.

## Run Locally

From the project root:

```bash
uv sync
uv run streamlit run app.py
```

The CSV path is resolved relative to `app.py`; it does not depend on a personal Downloads directory. Reliable salary data is unavailable in the input and no salary metric is displayed.
