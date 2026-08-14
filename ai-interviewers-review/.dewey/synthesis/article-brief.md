# Article brief: Interviewing at the Marginal Cost of Computation

> This is a writing brief, not manuscript prose. Use it to write an economics literature review
> organized around an argument, intellectual development, and evidence-weighted claims.

## Positioning

- **Audience:** Economists, survey methodologists, and social scientists considering AI-mediated interviews
- **Genre:** JEL-style economics literature review
- **Central question:** When does AI-mediated adaptivity improve the economic production of interview evidence, and when does it merely change respondent behavior or transcript volume without improving measurement?
- **Thesis:** AI interviewers relax the cost and standardization constraints on adaptive interviewing, but they do not remove the core measurement problem: benefits are conditional on respondent trust, the purpose and timing of probes, and validation against outcomes beyond transcript length or user preference.
- **Abstract:** Adaptive interviewing has traditionally exchanged standardization and scale for interviewer judgment and conversational depth. AI interviewers relax that production constraint, but their value depends on whether conversational gains become valid measurements rather than merely longer transcripts. This review connects research on virtual humans, conversational surveys, adaptive probing, and criterion-based interview evaluation. Across seven studies, the evidence supports a conditional conclusion: automation can reduce evaluation apprehension and can improve selected dimensions of probing and transcript quality, yet effects depend on disclosure, trust, probe purpose, modality, and the availability of external validity criteria. The field has advanced faster on scalable elicitation than on measurement theory. Its central agenda is therefore to identify which interviewer decisions should be automated, for whom, and against which substantive benchmark.
- **Keywords:** artificial intelligence, interview methods, survey methodology, measurement, qualitative research, disclosure
- **JEL codes:** C83, C81, C93, D91

## Motivation and context

- Interviews produce contextual and open-ended evidence that fixed questionnaires often miss, but trained interviewer time makes adaptive interviewing expensive and difficult to standardize.
- Large language models make contingent follow-up questions cheap to produce at scale, potentially changing the feasible frontier between standardized measurement and conversational depth.
- The resulting policy and research value depends on measurement, not fluency: longer or more natural conversations need not be more accurate, comparable, or decision-relevant.

### Field context

- Interview design has long managed a tension between standardization, which supports comparability, and interviewer discretion, which supports clarification, rapport, and discovery.
- Earlier virtual-human systems separated the social effects of perceived automation from the capabilities of generative language models; contemporary systems combine those channels.
- The literature spans human-computer interaction, survey methodology, forensic interviewing, and applied economics, with different outcome standards and weak cross-field integration.

### Contribution

- Recasts AI interviewing as a change in the production technology of measurement rather than as a contest between humans and machines.
- Connects the disclosure mechanism identified in virtual-human research to modern evidence on adaptive probing and interview quality.
- Separates conversational output, respondent experience, and criterion validity, which the emerging literature often treats as interchangeable indicators of success.
- Develops a research agenda centered on task allocation, heterogeneous effects, and external validation.

## Scope

### Include

- Empirical studies in which an automated conversational system conducts or materially adapts an interview or open-ended survey interaction.
- Evidence on disclosure, rapport, probing behavior, respondent burden, transcript quality, factual accuracy, and comparisons with human or conventional modes.
- Foundational virtual-human studies needed to identify mechanisms as well as recent generative-AI evaluations.

### Exclude or treat as boundary evidence

- AI used only to code or summarize interviews conducted by humans.
- Generic customer-service chatbots without a data-elicitation objective.
- Claims about population representativeness, downstream causal inference, or truthful reporting that the included designs do not directly test.

## Literature map

### Virtual humans and disclosure (`virtual_humans`)

Early embodied-agent studies ask how perceived automation, social presence, and evaluation apprehension change what respondents reveal.

**Relationship to review:** Provides the behavioral mechanism behind potential disclosure gains and distinguishes automation effects from language-model capability.

**Sources:** src_ca3e033a6b39, src_418b4c4f1a21

### Conversational surveys and adaptive probes (`conversational_surveys`)

Survey and HCI studies evaluate whether conversational interfaces and theoretically motivated probes improve open-ended answers and respondent experience.

**Relationship to review:** Identifies design margins and shows that adaptivity has selective benefits and measurable burden costs.

**Sources:** src_db7efbce68d9, src_2a843bf69441, src_af8750017209

### Qualitative evidence at scale (`scaled_qualitative`)

Recent economics work treats AI-led conversation as infrastructure for producing rich qualitative data at survey-like scale.

**Relationship to review:** Shows the frontier application and motivates the production-technology framing.

**Sources:** src_6541b25ef96e

### Criterion-based interview validity (`criterion_validity`)

Forensic-style experiments compare elicited accounts against events known to the researcher rather than treating verbosity as quality.

**Relationship to review:** Supplies the strongest warning against equating more conversational output with better measurement.

**Sources:** src_5e242e942988

## Study map

| Study | Role | Contribution | Claims | Caveat |
|---|---|---|---|---|
| @devault2014simsensei: SimSensei Kiosk: A Virtual Human Interviewer for Healthcare Decision Support | foundational | Establishes the virtual-human system lineage and feasibility of semi-automated sensitive interviewing. | claim_0eea6a57de7b | A specialized multimodal system, not a modern autonomous language-model interviewer. |
| @lucas2014computer: It's Only a Computer: Virtual Humans Increase Willingness to Disclose | foundational | Isolates perceived automation and evaluation apprehension as mechanisms affecting disclosure. | claim_61ea2c6b6b95 | Disclosure willingness is not equivalent to factual accuracy or population-level validity. |
| @duka2021conversational: Conversational Survey Chatbot: User Experience and Perception | bridge | Connects embodied virtual humans to accessible survey chatbots and foregrounds user experience and trust. | claim_61ea2c6b6b95, claim_0eea6a57de7b | Small and context-specific evaluation with limited causal leverage. |
| @barari2025aiassisted: AI-Assisted Conversational Interviewing: Effects on Data Quality and Respondent Experience | evaluation | Provides a broad contemporary experiment on conversational interviewing, data quality, and respondent experience. | claim_afb1fe75ab9d, claim_0eea6a57de7b, claim_5e6f2020b1ed | Online tasks and study-specific quality measures bound generalization to field interviews. |
| @jacobsen2025chatbots: Chatbots for Data Collection in Surveys: A Comparison of Four Theory-Based Interview Probes | evaluation | Decomposes adaptive interviewing into theory-based probe types rather than evaluating a monolithic chatbot treatment. | claim_afb1fe75ab9d | Probe effects depend on question and stage; no universal optimal probe follows. |
| @sun2025comparing: Comparing the Performance of a Large Language Model and Naive Human Interviewers in Interviewing Children about a Witnessed Mock-Event | counterpoint | Evaluates factual interview performance against a witnessed event and demonstrates the importance of criterion validity. | claim_5e6f2020b1ed, claim_0eea6a57de7b | A child-witness mock event is unusually structured and high stakes. |
| @geiecke2026conversations: Conversations at Scale: Robust AI-led Interviews | frontier | Shows how AI-led interviews can scale qualitative elicitation and benchmark transcript quality against trained humans. | claim_0eea6a57de7b, claim_afb1fe75ab9d, claim_5e6f2020b1ed | Transcript-quality benchmarks do not by themselves establish construct or predictive validity. |
## Timeline

| Year | Development | Why it matters | Sources |
|---:|---|---|---|
| 2014 | Virtual-human interviewing separates automation from human evaluation | The first wave establishes feasibility and a disclosure mechanism before general-purpose generative models. | src_ca3e033a6b39, src_418b4c4f1a21 |
| 2021 | Conversational survey chatbots move into ordinary data collection | The interface becomes cheaper and more familiar, shifting attention toward usability and trust. | src_db7efbce68d9 |
| 2025 | Generative systems enable randomized tests of adaptivity and probe design | Studies begin to compare conversational treatments, isolate probe types, and test performance against external criteria. | src_2a843bf69441, src_af8750017209, src_5e242e942988 |
| 2026 | AI-led interviews become infrastructure for qualitative evidence at scale | The research question shifts from technical feasibility to optimal deployment and measurement validity. | src_6541b25ef96e |

## Planned argument

### 1. Introduction: Interviewing as a Production Technology

**Purpose:** Begin with the economics of producing adaptive evidence, state the thesis, define scope, and preview the article.


### 2. From Virtual Humans to Generative Interviewers

**Purpose:** Trace the intellectual lineage and distinguish the behavioral effect of automation from advances in conversational capability.

**Themes:** Disclosure, trust, and evaluation apprehension

#### Claim: Perceived automation can reduce evaluation apprehension and support disclosure, but this advantage is conditional on trust and does not establish truthful reporting.

- Scope: Short virtual-human and automated health or survey interactions; evidence does not establish accuracy of sensitive disclosures.
- Confidence: moderate — One strong framing experiment provides convergent mechanism evidence, qualified by indirect and low-confidence acceptability studies.
- **supports** (lucas2014computer): Compared with human-operation framing, computer framing produced lower self-reported fear of self-disclosure and impression management. Locator: `[{"page": "98-99", "section": "Results", "table": null, "figure": null, "passage": null}]`. Appraisal: moderate confidence.
- **supports** (lucas2014computer): Participants in the computer-framed condition displayed more intense sadness and received higher blind-observer ratings of willingness to disclose in interview transcripts. Locator: `[{"page": "98-99", "section": "Results", "table": null, "figure": null, "passage": null}]`. Appraisal: moderate confidence.
- **qualifies** (devault2014simsensei): Automatic and Wizard-of-Oz cohorts were similar on willingness to share (4.07 vs 4.03), comfort sharing (3.80 vs 3.92), and feeling good talking (3.60 vs 3.69); reported differences were small and not marked significant. Locator: `[{"page": "1067", "section": "Evaluation", "table": "Table 2", "figure": null, "passage": null}]`. Appraisal: low confidence for causal effects; moderate confidence for feasibility.
- **contradicts** (duka2021conversational): Although 87% knew what a chatbot was, only 44% had used one; 88% preferred waiting for a human service agent, while 48% said they would use a brand lacking a human agent and 35% were unsure. Locator: `[{"page": "325-326", "section": "4.2 Data Collection and 4.3 Result Analysis", "table": null, "figure": "Figures 2-5", "passage": null}]`. Appraisal: low confidence.

### 3. What Adaptivity Produces

**Purpose:** Evaluate whether adaptive probes improve answer content, where they work, and what burden they impose.

**Themes:** Adaptive probing and conversational quality; Respondent burden and deployment trade-offs

#### Claim: Adaptive probing produces selective rather than universal improvements, and its value depends on probe purpose and interview stage while imposing additional burden.

- Scope: Short online survey and HCI interview tasks using LLM-generated follow-ups.
- Confidence: moderate — Two experiments converge that probing effects are multidimensional and conditional; samples and tasks remain bounded.
- **supports** (barari2025aiassisted): Probing increased specificity and explanation for the two opinion questions and increased word count and Shannon entropy, but did not improve completeness, relevance, lexical diversity, or KL divergence consistently. Locator: `[{"page": "16-18", "section": "5.3 Effects of Elaboration and Relevance Probing", "table": null, "figure": "Figures 2-3", "passage": null}]`. Appraisal: moderate confidence.
- **supports** (jacobsen2025chatbots): Across 1,287 responses, explanatory probes were less relevant, specific, and clear than several alternatives; idiographic probes outperformed explanatory probes on multiple outcomes in requirements and evaluation stages, while informativeness showed no overall probe difference. Locator: `[{"page": "8-12", "section": "5.1 Assessing Response Quality", "table": "Tables 5-6", "figure": "Figures 1-3", "passage": null}]`. Appraisal: low-to-moderate confidence.
- **qualifies** (barari2025aiassisted): Elaboration/relevance probing increased dropout by roughly 2-3 percentage points at the first question, doubled average completed-interview duration from about 3 to 6 minutes, and shifted ease, frustration, and satisfaction by less than 0.05 on normalized scales; confirmation probes had little effect. Locator: `[{"page": "18-19", "section": "5.4 Effects of Probing on Respondent Experience", "table": null, "figure": "Figures 4-5", "passage": null}]`. Appraisal: moderate confidence.

### 4. Humans, Machines, and the Quality Frontier

**Purpose:** Synthesize comparative performance without collapsing different modalities, tasks, and notions of quality into a single ranking.

**Themes:** Adaptive probing and conversational quality; Respondent burden and deployment trade-offs

#### Claim: AI interviewers can approach trained-human transcript quality under constrained online conditions, but autonomy and modality alter rapport and performance enough to preclude a general equivalence claim.

- Scope: Short online or embodied interviews evaluated through transcript ratings and post-interview experience.
- Confidence: low to moderate — Promising expert ratings and feasibility results are based on small, heterogeneous, or nonrandomized comparisons.
- **supports** (geiecke2026conversations): Against an online-text expert benchmark, mean grades were 3.93 for AI voice, 3.51 for human face-to-face, 2.98 for AI text, and 2.42 for human text; against a face-to-face benchmark they were 3.50, 3.53, 2.70, and 1.99 respectively, with 40 ratings per modality. Locator: `[{"page": "16-18", "section": "2.2.1 Comparison to human experts", "table": "Table II", "figure": null, "passage": null}]`. Appraisal: low-to-moderate confidence.
- **contradicts** (devault2014simsensei): The automatic system scored lower for being a good listener (3.56 vs 4.10, d=0.61), system usability (68.68 vs 74.37, d=0.44), and rapport (75.43 vs 80.71, d=0.44), with differences marked p<.05. Locator: `[{"page": "1067", "section": "Evaluation", "table": "Table 2", "figure": null, "passage": null}]`. Appraisal: low confidence for causal effects; moderate confidence for feasibility.
- **qualifies** (devault2014simsensei): Automatic and Wizard-of-Oz cohorts were similar on willingness to share (4.07 vs 4.03), comfort sharing (3.80 vs 3.92), and feeling good talking (3.60 vs 3.69); reported differences were small and not marked significant. Locator: `[{"page": "1067", "section": "Evaluation", "table": "Table 2", "figure": null, "passage": null}]`. Appraisal: low confidence for causal effects; moderate confidence for feasibility.

### 5. The Measurement Problem

**Purpose:** Separate disclosure, verbosity, transcript ratings, and respondent experience from criterion and construct validity.

**Themes:** Measurement validity and evidential value; Disclosure, trust, and evaluation apprehension

#### Claim: Evidence that AI interviews yield more or richer text should not be treated as measurement validity; validity is task-specific and requires external or independent criteria.

- Scope: AI-assisted surveys, reflective interviews, live coding, and child-witness questioning.
- Confidence: moderate — The studies consistently separate engagement or richness from validity, but only one included study uses a direct ground-truth outcome.
- **supports** (sun2025comparing): LLM interviews elicited similar unique correct details (8.50 vs 7.50, p=.290), more unique correct information per question (0.90 vs 0.46, p<.001), and less false information overall, while asking 471 questions versus 872 in the human condition. Locator: `[{"page": "12-14", "section": "Hypothesis 2 and exploratory analyses", "table": null, "figure": "Figure 2", "passage": null}]`. Appraisal: moderate confidence.
- **supports** (barari2025aiassisted): Respondent-confirmed accuracy ranged from 66.1% to 96.2% across tasks; agreement with independent human coding was lower for several tasks, and respondents selected 'none of the above' less often. Locator: `[{"page": "14-15", "section": "5.1 Live Coding and Confirmation Probing", "table": "Tables 2-3", "figure": null, "passage": null}]`. Appraisal: moderate confidence.
- **qualifies** (barari2025aiassisted): Probing increased specificity and explanation for the two opinion questions and increased word count and Shannon entropy, but did not improve completeness, relevance, lexical diversity, or KL divergence consistently. Locator: `[{"page": "16-18", "section": "5.3 Effects of Elaboration and Relevance Probing", "table": null, "figure": "Figures 2-3", "passage": null}]`. Appraisal: moderate confidence.
- **qualifies** (geiecke2026conversations): In the randomized meaning-in-life study, 51.69% of AI-interview respondents said they could clearly pinpoint sources of meaning versus 41.18% in open text; 33.82% versus 41.57% said their thoughts were still evolving. Locator: `[{"page": "24-27", "section": "3.1 Measuring Meaning in Life", "table": "Table IV", "figure": null, "passage": null}]`. Appraisal: moderate confidence for reflective effects.

### 6. An Economics Research Agenda

**Purpose:** Frame open questions as optimal task allocation, heterogeneous treatment effects, equilibrium respondent adaptation, validation, and total data-production cost.

**Themes:** Respondent burden and deployment trade-offs; Measurement validity and evidential value

### 7. Conclusion

**Purpose:** Return to the conditional thesis and identify what evidence would change it.


## Intended conclusion

- AI changes the feasible set of interview designs by making standardized adaptivity inexpensive, not by making interviewer judgment or measurement error disappear.
- The most defensible current result is conditional: automation can improve disclosure and selected forms of probing, while trust, burden, task, and modality determine whether those gains survive.
- The next generation of studies should pre-specify the measurement target, benchmark against external criteria, report heterogeneous effects, and compare total production costs rather than transcript volume alone.

## Source metadata

- `src_2a843bf69441` / `@barari2025aiassisted` — Barari, Soubhik and Angbazo, Jarret and Wang, Natalie and Christian, Leah M. and Dean, Elizabeth and Slowinski, Zoe and Sepulvado, Brandon (2025), *AI-Assisted Conversational Interviewing: Effects on Data Quality and Respondent Experience*. DOI: 10.48550/arXiv.2504.13908
- `src_418b4c4f1a21` / `@lucas2014computer` — Lucas, Gale M. and Gratch, Jonathan and King, Aisha and Morency, Louis-Philippe (2014), *It's Only a Computer: Virtual Humans Increase Willingness to Disclose*. DOI: 10.1016/j.chb.2014.04.043
- `src_5e242e942988` / `@sun2025comparing` — Sun, Yongjie and Pang, Haohai and Järvilehto, Liisa and Zhang, Ophelia and Shapiro, David and Korkman, Julia and Haginoya, Shumpei and Santtila, Pekka (2025), *Comparing the Performance of a Large Language Model and Naive Human Interviewers in Interviewing Children about a Witnessed Mock-Event*. DOI: 10.1371/journal.pone.0316317
- `src_6541b25ef96e` / `@geiecke2026conversations` — Geiecke, Friedrich and Jaravel, Xavier (2026), *Conversations at Scale: Robust AI-led Interviews*. DOI: 10.2139/ssrn.4974382
- `src_af8750017209` / `@jacobsen2025chatbots` — Jacobsen, Rune M. and Cox, Samuel Rhys and Griggio, Carla F. and van Berkel, Niels (2025), *Chatbots for Data Collection in Surveys: A Comparison of Four Theory-Based Interview Probes*. DOI: 10.1145/3706598.3714128
- `src_ca3e033a6b39` / `@devault2014simsensei` — DeVault, David and Artstein, Ron and Benn, Grace and Dey, Teresa and Fast, Ed and Gainer, Alesia and Georgila, Kallirroi and Gratch, Jonathan and Hartholt, Arno and Lhommet, Margaux and others (2014), *SimSensei Kiosk: A Virtual Human Interviewer for Healthcare Decision Support*. DOI: 10.5555/2615731.2617415
- `src_db7efbce68d9` / `@duka2021conversational` — Đuka, Isidora and Njeguš, Angelina (2021), *Conversational Survey Chatbot: User Experience and Perception*. DOI: 10.15308/Sinteza-2021-322-327
