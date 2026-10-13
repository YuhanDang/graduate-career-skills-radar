# Graduate Career Skills Radar

A Career Services–hosted dashboard for U.S. university students exploring career pathways and choosing their next skill-learning topic.

**Group 3:** Yuhan Dang, Yanxi Wang, Wenbo Hu, Borui Su.
**Live app:** https://graduate-career-skills-radar.streamlit.app
**Repository:** [Add public GitHub repository URL]

## Step 1 — Dataset and Decision-Maker

### Dataset and provenance

I independently selected [1.3M LinkedIn Jobs & Skills (2024) by asaniczka on Kaggle](https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024) for my individual submission. It contains real-world LinkedIn job job postings and extracted skill labels, rather than synthetic student employment outcomes. I use the postings and skills files, joined by `job_link`.

One row in the dashboard CSV represents one selected job posting. It does not necessarily represent a distinct vacancy, an available job today, or a hire. The source postings were first observed from **January 12–17, 2024**. These are collection dates, not verified publication dates or a complete period of recruiting activity.

The original postings file contains **1,348,454 rows**. In the Pandas notebook, I reduced the source through reproducible location and title rules, joined the skill information, and exported **one CSV with 4,766 rows and 19 columns, approximately 5.484 MB**. This is rule-based selection, not random sampling. The selected records are not representative estimates of the entire U.S. labor market.

### One primary decision-maker

The dashboard is for **a U.S. university undergraduate preparing for an internship or first full-time role in business, computing, or a related field**. The student wants to compare career directions, investigate skill mentions in relevant job postings, and decide which learning topic to pursue or discuss with a career adviser.

The university Career Services office is the potential institutional buyer and host. The student is the primary user and decision-maker; department directors are not a second primary audience for this version.

### Geographic and career scope

The selected job postings cover:

- Data and Business Analytics
- Finance and Accounting
- Marketing
- Software Development

U.S. location screening uses `job_location`, including explicit country names, state abbreviations, and a reviewed list of location labels. `search_country` is search metadata, not proof of job location. Ambiguous country locations were excluded. In the final selection, explicit state codes and reviewed single-state labels assign **4,612 job postings** to a state; **154** remain `Unspecified`. Cross-state metropolitan areas are not forced into a single state.

The dataset distinguishes **354 job postings with explicit early-career title signals** from **4,412 broader title matches with eligibility unverified**. Broader matches come from selected exact normalized titles in the unclear-stage group. Neither group has been verified against full descriptions for experience, degree, or work-authorization requirements. The app will preserve these distinctions instead of labeling the whole selection as entry-level jobs.

## Step 2 — Justify the Dashboard

### 1. Who looks at it, and how often?

The student would review the production dashboard **weekly during active internship or job preparation**, and before a career-advising appointment. Outside an active search, a monthly review would be sufficient. The student returns when considering a different pathway or location, updating self-reported skills, or reconsidering a learning plan.

### 2. What decision does it support?

**If a student sees a frequently mentioned skill in their target career pathway that they have not selected as a current skill, they will review relevant job posting examples and choose a learning topic to discuss with a career adviser or pursue next.**

For example, a student considering analytics might investigate SQL after seeing frequent SQL mentions, inspect the associated job postings, and discuss a SQL course or project with an adviser. Frequency is a starting point for investigation, not proof that a skill is essential for every role or the best next step for every student.

### 3. What does the student do today without it, and what does that cost?

In the assumed workflow, the student reads job postings individually, takes notes on recurring skills, and consults broad career guides or an adviser. Comparing multiple career directions and locations requires repeating that work. Inconsistent notes or memorable individual job postings can lead to an incomplete view and a poorly chosen learning priority.

The potential costs are time spent repeatedly compiling information and effort spent on a learning topic that is less relevant to the student's goals. These are workflow hypotheses, not measured interview findings; no quantified savings or placement improvement is claimed.

### 4. Why a dashboard rather than an email, report, poster, or alert?

A report or poster can communicate a fixed list of common skills. This dashboard supports a recurring decision with changing inputs: the same student can compare pathways and locations, distinguish title-based scopes, update self-reported skills, and inspect supporting job postings as their preparation progresses.

A weekly email could summarize changes but would not directly support all of those comparisons. An alert could flag a change but would not provide enough context to choose a learning topic. Embedding the tool in a university website makes it accessible; repeated review and action are what justify the dashboard.

The frozen Kaggle prototype demonstrates this workflow. If the only goal were to describe this snapshot once, a report would be sufficient. Production value depends on refreshed data and continued student use.

### Commercial application

A plausible delivery model is a university subscription for a student-facing tool linked from its Career Services website. The recurring need is career exploration and preparation between advising appointments. Institutional adoption would require student and staff interviews and a pilot to test usefulness and willingness to pay. The dataset alone does not establish market demand, employment benefits, or commercial data-use rights. Production would require a sustainable, appropriately licensed data source.

## Step 3 — Decide What Matters

### EDA and findings that influence the design

The notebook uses **Pandas and Matplotlib** to examine shape, data types, missing values, categorical distributions, title-stage signals, skill frequencies, and relationships between career pathway, analysis scope, and skill mentions.

Both source files have unique `job_link` values. The skill-record match rate is **96.14%**, although a matched record can still have an empty skill list. In the final selection, **4,697 job postings have nonblank original skill lists** and 69 do not.

| Career pathway | Explicit early-career title signals | Broader title matches | Total job postings | Nonblank skill lists |
| --- | ---: | ---: | ---: | ---: |
| Data and Business Analytics | 94 | 1,261 | 1,355 | 1,323 |
| Finance and Accounting | 167 | 2,336 | 2,503 | 2,486 |
| Marketing | 41 | 209 | 250 | 240 |
| Software Development | 52 | 606 | 658 | 648 |
| **Total** | **354** | **4,412** | **4,766** | **4,697** |

The source `job_level` labels are inconsistent with some titles, so they are not used to confirm entry-level eligibility. Scope also affects skill patterns: SQL appears in **45.1%** of valid explicit early-career analytics lists versus **33.2%** of broader-title lists. Marketing project management mentions are **25.0%** versus **46.0%**. These are differences between selected cohorts, not temporal changes. The findings justify a visible analysis-scope control and cautious interpretation of small groups.

### Three headline numbers

The student version will use `st.metric` side by side in `st.columns` for:

| Metric | Definition | Why the student needs it |
| --- | --- | --- |
| Selected Job Postings | Number of job postings matching the pathway, state selection, and analysis scope | Establishes how much evidence supports the view |
| Postings with skill information | Job Postings with nonblank original skill lists divided by all selected job postings | Makes incomplete evidence visible |
| My selected top skills | Displayed top skill terms selected by the student as current skills divided by the number of displayed top terms | Shows which frequently mentioned topics the student has and has not selected |

The third metric compares exact normalized terms among up to eight displayed skills. It is an unweighted descriptive overlap, not an assessment of proficiency, qualification, employability, or hiring probability. With no displayed terms it is unavailable; with no skills selected, zero overlap reflects the current input rather than a verified lack of ability. Changes in the filters can change both the displayed skill set and this percentage.

### Two supporting charts

1. **Top Skill Mentions in the Selected Pathway:** a horizontal bar chart of up to eight retained terms. Color and labels distinguish terms selected as current skills from terms not selected. This breakdown explains the self-reported coverage metric and identifies topics worth investigating.
2. **Where Else Is This Skill Mentioned?:** a bar chart comparing one skill's mention rate across all four pathways, using the same state selection and analysis scope. Each pathway displays its own valid-record count. This helps the student investigate whether a learning topic is relevant to more than one direction.

Each term counts at most once per job posting. Mention-rate denominators use nonblank **original** skill lists, even when qualification-like terms are withheld. Selecting a skill or changing the personal skill profile does not remove job postings lacking that skill from these denominators. The historical prototype shows segment comparisons, not fabricated trend movement.

### Only necessary controls

- **Career direction:** chooses the career direction under consideration.
- **Preferred state(s):** selects one or more employment locations. The all-location view includes `Unspecified` records.
- **Posting scope:** distinguishes explicit early-career title signals, broader title matches with eligibility unverified, or all selected job postings. It is not a verified experience-level filter.
- **My Current Skills:** self-reported input that changes coverage, chart highlighting, and learning candidates without filtering the job posting evidence.
- **Skill Library Search:** type a partial name and select a matching catalogued skill for the cross-pathway chart and supporting examples. Exact and prefix matches appear first, with A–Z ordering within each match tier; skills in the first chart remain ordered by mention rate.

Below the charts, **Skills to Explore** will list up to three unselected terms from the displayed ranking, ordered by mention rate. These are candidate discussion topics, not automatic learning prescriptions; students should consider their interests, prerequisites, and adviser guidance. If every displayed term is selected, the app will not invent a missing skill.

### Two things deliberately not shown

1. **Salary estimates and skill–salary comparisons:** the dashboard input has no reliable structured salary field. Occasional salary text in titles cannot support a defensible median salary or salary premium.
2. **Daily hiring growth:** first-seen dates span a short collection window and do not establish publication dates or hiring activity. A growth chart would imply evidence the data does not provide.

### Potentially misleading data and handling

| Issue | Design response |
| --- | --- |
| Old snapshot and possibly expired links | Keep a brief period and eligibility notice near the top; identify URLs as historical examples |
| Unverified eligibility | Preserve scope labels and explain that title signals do not establish internship or graduate suitability |
| Extracted labels and qualifications mixed together | Normalize terms, merge a limited alias set, and withhold rule-flagged degree, authorization, clearance, and numeric-experience terms; retain originals and flagged terms for inspection |
| Missing lists and small groups | Show information coverage and valid-record counts; flag small selections; display unavailable rather than zero when no denominator exists |
| Possible repeated job postings | Keep duplicate flags, label counts as job postings, and explain sensitivity to the counting method |
| Volunteer titles | Flag examples so students do not assume every job posting describes paid employment |
| Geographic and title-selection errors | Explain heuristic rules, excluded ambiguous locations, and omitted title variants |
| Self-reported skill choices | Explain exact-term overlap and avoid presenting it as a tested ability score or a personal skill-gap diagnosis |

There are **872 job postings in possible duplicate groups** based on normalized company, title, and location. They remain because these fields do not prove that job postings represent the same vacancy. An earlier sensitivity analysis counted each comparison group once and combined its retained terms. In the earlier exploratory analysis, before introducing the maintained skill library, in each pathway and scope had a largest absolute difference of **5.78 percentage points**, for early-career Software Development JavaScript: 34.69% across 49 valid job postings versus 40.48% across 42 valid groups. This is an alternative calculation, not validated deduplication.

### Page order and rationale

**Introduction:** a project-specific AI-generated career-exploration illustration, a brief explanation, a three-step guide, group attribution, and one button lead into the dashboard. The introduction is separate from the analytical page and adds no extra charts or headline metrics. Students can return to it using the Introduction button.

**Dashboard first screen:** a compact title, with the student audience caption and Group 3 member attribution alongside each other, historical-period notice, three essential filters, self-reported skill buttons, and three headline metrics. On wide screens, the top-skill chart and up to three learning candidates sit side by side, with approximately two-thirds of the row allocated to the chart. The student can assess the evidence and identify topics to investigate without needing to scroll through secondary comparisons.

**Skill library and search:** the app uses `data/skill_catalog.json`, a maintained vocabulary of 256 named skills and tools with explicit aliases. Bullet markers and wrapping quotes are removed before exact matching. Salary text, numeric IDs, experience statements, and other unmatched descriptions are excluded from rankings and search; unrecognized terms are retained for review in the example table. Technical punctuation is preserved: `.NET`, `C++`, and `C#` are valid tool/language names. This initial vocabulary is incomplete and requires review before extension. Each canonical skill is counted once per posting; original nonblank-list denominators do not change.

**Optional quick tour:** first-session visitors can start or skip a three-step guide. The guide groups career direction, posting scope and preferred states in one step, then introduces current skills and Where Else Is This Skill Mentioned? for skill searches and comparisons across career directions. Back, Next, Skip and Finish change only guide state; filter settings and the skill profile are preserved. The How to use button restarts the guide. Completion is remembered within the current session, without cookies or a persistent student account. Prominent plain-language filter labels also support students who skip the guide. All modules share a fluid, centered content area with consistent left/right boundaries and responsive side whitespace. The final tour step temporarily hides earlier controls, metrics, the primary chart and header details to bring the skill-search field and cross-pathway chart forward. Widgets remain mounted, preserving filters and skill selections; finishing or skipping restores the complete dashboard. Smaller screens may still require normal scrolling, without clipping or fixed-height chart panels.

**Further exploration:** the cross-pathway skill comparison appears below the primary decision view. Students type part of a name (for example `pyt`), press Enter, and click a matching skill suggestion. Matches prioritize exact names, then prefixes, then contained text; ties use A–Z order. Search covers observed catalogued skills across the full dataset, so changing pathways does not hide a selected skill. Its selected term, locations, and scope are explicitly identified. Changing the skill, locations, or scope updates the underlying counts; changing personal selections does not alter job posting mention rates.

**Detail and notes:** an expandable job posting table supports evidence checking through original links and retained/withheld terms. Full Data Notes and Limitations remain separately visible at the bottom as five compact, secondary-text items. Key historical, eligibility, and small-group cautions remain close to the relevant evidence.

The layout uses available desktop width with a maximum reading width. The primary chart and learning candidates stack in smaller windows; filters and metrics stack on mobile. First-screen completeness is a desktop goal, not a reason to hide information or shrink text on small screens. Update the required paper sketch to reflect this design.

### Visual style and asset use

The interface references the University of Delaware's blue (`#00539F`) and gold (`#FFD200`) palette, condensed headings, and readable sans-serif body text. Open Sans and Oswald are bundled under SIL Open Font License 1.1, with notices in `assets/fonts/`. The University's [brand style guide](https://www.udel.edu/content/dam/udelImages/ocm/style-guide/brand-style-guide.pdf) lists these as digital alternatives when official fonts are unavailable. Gold identifies self-reported selections; blue identifies unselected skill terms and the cross-pathway chart, with text labels preserving the distinction.

The project uses an original geometric compass icon rather than official university marks. It does not copy the university logo, seal, mascot, proprietary font files, or official website header. A visible note identifies this as an independent class project, not an official university service. The landing illustration depicts a student linking current skills to data analytics, finance, marketing and software directions. It is AI-generated illustrative artwork, clearly identified as such, rather than documentary photography or measured dataset results. The complete image is displayed without cropping, with a responsive text area beside it or below it on smaller screens. Asset sources and notices are recorded in `assets/CREDITS.md`.

**One-line audience caption:**

> For U.S. university students exploring career pathways and choosing their next skill-learning topic.

## Step 4 — Decide the Refresh Frequency

### 1. How often should production data refresh?

Production would refresh **weekly**. Job Postings change frequently, but students generally choose courses, projects, and advising actions over days or weeks. Weekly refresh supports those decisions without the collection and processing complexity of real-time updates. Current availability of a specific vacancy must still be checked at its source.

The submitted prototype reads a fixed Kaggle CSV. It does not actually refresh external data.

### 2. How often should students review it?

Students in active preparation would review it **weekly**, and before an advising appointment or a change in target pathway or location. They would update their self-reported selections after learning or completing a relevant project. Outside an active search, monthly review is sufficient.

Refresh is a system schedule; review is a student action. They may both occur weekly during an active search, but students do not need to open the page whenever the system updates.

### 3. What should be tracked, and what triggers action?

Production would track a selected skill's mention rate in comparable four-week collection cohorts, using consistent pathway, location, analysis scope, extraction, and duplicate rules. Compare the latest cohort with the preceding non-overlapping cohort rather than confusing filter changes with market changes.

A proposed trigger is an increase of at least **10 percentage points**, with at least **100 job postings containing usable skill lists in each cohort**. If the increase remains visible after the next weekly refresh and the student has not selected that skill, they would contact a career adviser, inspect example job postings, and reconsider their learning plan. Students can explore existing high-frequency terms without waiting for this trigger.

The threshold is a planning hypothesis, not an empirically validated rule. Persistence across refreshes is a follow-up check, not independent statistical confirmation. Smaller groups remain exploratory, and the historical snapshot cannot test this trigger or display a real change alert.

### 4. What does stale data cost?

A one-day delay is unlikely to change a course or project decision. A one-week delay could leave a student using an outdated shortlist during an application or advising discussion. Longer staleness could direct limited learning time toward older job posting patterns or encourage reliance on expired job examples. These are plausible consequences, not measured financial losses.

**Dashboard freshness line:**

> Data: first observed Jan 12–17, 2024, Kaggle snapshot. Proposed production refresh: weekly; review weekly during active career preparation.
