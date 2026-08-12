# AI interviewer meta-analysis protocol

## Review question

Among human respondents, how does interview or survey data collection mediated by an AI or conversational agent compare with a human interviewer or conventional self-administered instrument?

## Quantitative inclusion criteria

- Empirical study with human respondents.
- AI, LLM, chatbot, virtual-agent, or conversational interviewing intervention.
- Concurrent comparator such as a human interviewer, static/open-text survey, web questionnaire, non-adaptive chatbot, or alternative interviewer design.
- Reports a sample size by condition and at least one outcome from which an effect size can be calculated or requested from authors.
- Outcomes concern elicited-information quality, correctness, richness, specificity, relevance, disclosure, completion/attrition, interview duration, respondent experience, trust, privacy, or safety.

Model-only simulations, purely descriptive deployments, qualitative feasibility studies, and papers without a comparator remain part of the narrative review but not the primary quantitative synthesis.

## Extraction and dependence rules

- Treat the study, not each reported outcome, as the independent sampling unit.
- Record all eligible outcomes, their direction, time point, and rater type; do not select outcomes based on significance.
- Prefer human-coded outcomes over unvalidated LLM judgments; preserve both when reported.
- Record whether raters were blinded and whether reliability was reported.
- Keep multiple effects from one sample linked by `study_id`; use robust variance estimation or a prespecified within-study aggregation rather than treating them as independent.
- Code randomized and nonrandomized comparisons separately.
- Keep pre-LLM conversational agents and modern LLM interviewers in separate technology subgroups.
- Flag shared or overlapping samples and retain only one estimate per sample/outcome/time point in any single model.

## Candidate effect metrics

- Continuous outcomes: Hedges' g from group means/SDs, or a convertible test statistic.
- Binary outcomes: log odds ratio.
- Counts or rates: log rate ratio when exposure is comparable.
- Repeated-measures studies: standardized mean change using the reported or sensitivity-tested within-person correlation.
- Attrition/completion: risk ratio or log odds ratio.

Positive effects should consistently indicate better performance by the more adaptive or AI-mediated interviewer; reverse-code adverse outcomes such as errors, attrition, or discomfort.
