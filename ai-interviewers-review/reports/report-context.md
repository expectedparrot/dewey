# AI interviewers

**Research question:** How are AI interviewers designed and evaluated, and how do they affect interview quality, respondent experience, and resulting data compared with human or conventional interviewing?

## Evidence status

Report-ready: **yes**
Studies: 8 · Findings: 12 · Appraisals: 8 · Claims: 4

## Drafting instructions

- Organize the report by themes and claims, not by paper.
- Treat claim statements as bounded synthesis propositions, not immutable conclusions.
- Weight evidence using appraisal and applicability; do not count findings as equal votes.
- Represent supporting, contradicting, and qualifying evidence fairly.
- Preserve source locators for every substantive empirical statement.
- Do not infer that unused or unavailable evidence is negative evidence.

## Disclosure, trust, and evaluation apprehension

How perceived automation, social judgment, familiarity, and trust shape willingness to disclose; excludes claims about the truth or validity of disclosed content.

### Claim: Perceived automation can reduce evaluation apprehension and support disclosure, but this advantage is conditional on trust and does not establish truthful reporting.

- **Scope:** Short virtual-human and automated health or survey interactions; evidence does not establish accuracy of sensitive disclosures.
- **Confidence:** moderate
- **Rationale:** One strong framing experiment provides convergent mechanism evidence, qualified by indirect and low-confidence acceptability studies.

| Relationship | Study | Finding | Locator | Appraisal |
|---|---|---|---|---|
| supports | Lucas et al. perceived automation experiment | Compared with human-operation framing, computer framing produced lower self-reported fear of self-disclosure and impression management. | page: 98-99, section: Results | moderate confidence |
| supports | Lucas et al. perceived automation experiment | Participants in the computer-framed condition displayed more intense sadness and received higher blind-observer ratings of willingness to disclose in interview transcripts. | page: 98-99, section: Results | moderate confidence |
| qualifies | SimSensei automatic-versus-Wizard-of-Oz evaluation | Automatic and Wizard-of-Oz cohorts were similar on willingness to share (4.07 vs 4.03), comfort sharing (3.80 vs 3.92), and feeling good talking (3.60 vs 3.69); reported differences were small and not marked significant. | page: 1067, section: Evaluation, table: Table 2 | low confidence for causal effects; moderate confidence for feasibility |
| contradicts | Đuka and Njeguš conversational survey perception study | Although 87% knew what a chatbot was, only 44% had used one; 88% preferred waiting for a human service agent, while 48% said they would use a brand lacking a human agent and 35% were unsure. | page: 325-326, section: 4.2 Data Collection and 4.3 Result Analysis, figure: Figures 2-5 | low confidence |

## Adaptive probing and conversational quality

How probe type, timing, listening behavior, rapport, and autonomy affect response production and interview quality.

### Claim: AI interviewers can approach trained-human transcript quality under constrained online conditions, but autonomy and modality alter rapport and performance enough to preclude a general equivalence claim.

- **Scope:** Short online or embodied interviews evaluated through transcript ratings and post-interview experience.
- **Confidence:** low to moderate
- **Rationale:** Promising expert ratings and feasibility results are based on small, heterogeneous, or nonrandomized comparisons.

| Relationship | Study | Finding | Locator | Appraisal |
|---|---|---|---|---|
| supports | Geiecke and Jaravel matched modality expert evaluation | Against an online-text expert benchmark, mean grades were 3.93 for AI voice, 3.51 for human face-to-face, 2.98 for AI text, and 2.42 for human text; against a face-to-face benchmark they were 3.50, 3.53, 2.70, and 1.99 respectively, with 40 ratings per modality. | page: 16-18, section: 2.2.1 Comparison to human experts, table: Table II | low-to-moderate confidence |
| contradicts | SimSensei automatic-versus-Wizard-of-Oz evaluation | The automatic system scored lower for being a good listener (3.56 vs 4.10, d=0.61), system usability (68.68 vs 74.37, d=0.44), and rapport (75.43 vs 80.71, d=0.44), with differences marked p<.05. | page: 1067, section: Evaluation, table: Table 2 | low confidence for causal effects; moderate confidence for feasibility |
| qualifies | SimSensei automatic-versus-Wizard-of-Oz evaluation | Automatic and Wizard-of-Oz cohorts were similar on willingness to share (4.07 vs 4.03), comfort sharing (3.80 vs 3.92), and feeling good talking (3.60 vs 3.69); reported differences were small and not marked significant. | page: 1067, section: Evaluation, table: Table 2 | low confidence for causal effects; moderate confidence for feasibility |

### Claim: Adaptive probing produces selective rather than universal improvements, and its value depends on probe purpose and interview stage while imposing additional burden.

- **Scope:** Short online survey and HCI interview tasks using LLM-generated follow-ups.
- **Confidence:** moderate
- **Rationale:** Two experiments converge that probing effects are multidimensional and conditional; samples and tasks remain bounded.

| Relationship | Study | Finding | Locator | Appraisal |
|---|---|---|---|---|
| supports | Barari et al. four-module conversational survey experiment | Probing increased specificity and explanation for the two opinion questions and increased word count and Shannon entropy, but did not improve completeness, relevance, lexical diversity, or KL divergence consistently. | page: 16-18, section: 5.3 Effects of Elaboration and Relevance Probing, figure: Figures 2-3 | moderate confidence |
| supports | Jacobsen et al. theory-based probe experiment | Across 1,287 responses, explanatory probes were less relevant, specific, and clear than several alternatives; idiographic probes outperformed explanatory probes on multiple outcomes in requirements and evaluation stages, while informativeness showed no overall probe difference. | page: 8-12, section: 5.1 Assessing Response Quality, table: Tables 5-6, figure: Figures 1-3 | low-to-moderate confidence |
| qualifies | Barari et al. four-module conversational survey experiment | Elaboration/relevance probing increased dropout by roughly 2-3 percentage points at the first question, doubled average completed-interview duration from about 3 to 6 minutes, and shifted ease, frustration, and satisfaction by less than 0.05 on normalized scales; confirmation probes had little effect. | page: 18-19, section: 5.4 Effects of Probing on Respondent Experience, figure: Figures 4-5 | moderate confidence |

## Respondent burden and deployment trade-offs

Time, attrition, usability, acceptability, and the practical costs of conversational data collection.

_Cross-theme claim: see `claim_0eea6a57de7b` above._

_Cross-theme claim: see `claim_afb1fe75ab9d` above._

## Measurement validity and evidential value

Whether AI-collected or AI-coded material is correct, novel, construct-valid, and useful for inference, distinct from verbosity or engagement.

### Claim: Evidence that AI interviews yield more or richer text should not be treated as measurement validity; validity is task-specific and requires external or independent criteria.

- **Scope:** AI-assisted surveys, reflective interviews, live coding, and child-witness questioning.
- **Confidence:** moderate
- **Rationale:** The studies consistently separate engagement or richness from validity, but only one included study uses a direct ground-truth outcome.

| Relationship | Study | Finding | Locator | Appraisal |
|---|---|---|---|---|
| supports | Sun et al. child witness interview experiment | LLM interviews elicited similar unique correct details (8.50 vs 7.50, p=.290), more unique correct information per question (0.90 vs 0.46, p<.001), and less false information overall, while asking 471 questions versus 872 in the human condition. | page: 12-14, section: Hypothesis 2 and exploratory analyses, figure: Figure 2 | moderate confidence |
| supports | Barari et al. four-module conversational survey experiment | Respondent-confirmed accuracy ranged from 66.1% to 96.2% across tasks; agreement with independent human coding was lower for several tasks, and respondents selected 'none of the above' less often. | page: 14-15, section: 5.1 Live Coding and Confirmation Probing, table: Tables 2-3 | moderate confidence |
| qualifies | Barari et al. four-module conversational survey experiment | Probing increased specificity and explanation for the two opinion questions and increased word count and Shannon entropy, but did not improve completeness, relevance, lexical diversity, or KL divergence consistently. | page: 16-18, section: 5.3 Effects of Elaboration and Relevance Probing, figure: Figures 2-3 | moderate confidence |
| qualifies | Geiecke and Jaravel meaning-in-life randomized comparison | In the randomized meaning-in-life study, 51.69% of AI-interview respondents said they could clearly pinpoint sources of meaning versus 41.18% in open text; 33.82% versus 41.57% said their thoughts were still evolving. | page: 24-27, section: 3.1 Measuring Meaning in Life, table: Table IV | moderate confidence for reflective effects |

## Reporting gaps

- No structural reporting gaps detected.

## Sources

- `src_2a843bf69441` — Barari, Soubhik and Angbazo, Jarret and Wang, Natalie and Christian, Leah M. and Dean, Elizabeth and Slowinski, Zoe and Sepulvado, Brandon, 2025, AI-Assisted Conversational Interviewing: Effects on Data Quality and Respondent Experience
- `src_418b4c4f1a21` — Lucas, Gale M. and Gratch, Jonathan and King, Aisha and Morency, Louis-Philippe, 2014, It's Only a Computer: Virtual Humans Increase Willingness to Disclose
- `src_5e242e942988` — Sun, Yongjie and Pang, Haohai and Järvilehto, Liisa and Zhang, Ophelia and Shapiro, David and Korkman, Julia and Haginoya, Shumpei and Santtila, Pekka, 2025, Comparing the Performance of a Large Language Model and Naive Human Interviewers in Interviewing Children about a Witnessed Mock-Event
- `src_6541b25ef96e` — Geiecke, Friedrich and Jaravel, Xavier, 2026, Conversations at Scale: Robust AI-led Interviews
- `src_af8750017209` — Jacobsen, Rune M. and Cox, Samuel Rhys and Griggio, Carla F. and van Berkel, Niels, 2025, Chatbots for Data Collection in Surveys: A Comparison of Four Theory-Based Interview Probes
- `src_ca3e033a6b39` — DeVault, David and Artstein, Ron and Benn, Grace and Dey, Teresa and Fast, Ed and Gainer, Alesia and Georgila, Kallirroi and Gratch, Jonathan and Hartholt, Arno and Lhommet, Margaux and others, 2014, SimSensei Kiosk: A Virtual Human Interviewer for Healthcare Decision Support
- `src_db7efbce68d9` — Đuka, Isidora and Njeguš, Angelina, 2021, Conversational Survey Chatbot: User Experience and Perception
