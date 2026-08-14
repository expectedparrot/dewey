---
title: "AI Interviewers: Promise, Trade-offs, and the Missing Validity Evidence"
subtitle: "A preliminary structured synthesis"
date: "August 14, 2026"
---

> **Status:** Preliminary synthesis. Dewey currently contains 57 sources, of which 18 have
> concise summaries and seven are included. This report synthesizes the first three studies
> to receive finding-level extraction and appraisal. It is an analytical starting point, not
> yet a comprehensive literature review.

## Executive summary

AI interviewers appear able to change both what people say and how an interview proceeds,
but the existing evidence supports a narrower conclusion than the technology's promise often
implies. Across the first three structured studies, automation offers two distinguishable
advantages. First, being perceived as a machine may reduce evaluation apprehension and make
people more willing to disclose. Second, adaptive probes can elicit more specific, explanatory,
and longer answers than standardized questions. Neither advantage establishes that the
resulting information is more accurate, more truthful, or more valid for downstream inference.

The studies also expose costs. Fully automatic interviewing can preserve basic willingness to
share while losing rapport, listening quality, and usability relative to a human-guided system.
Open-ended LLM probing lengthens interviews, modestly worsens respondent experience, and can
increase initial attrition. Live confirmation of AI coding may itself create acquiescence,
turning a proposed validation step into a source of measurement error.

The emerging throughline is therefore not that AI interviewers are simply better or worse
than human or standardized alternatives. They rearrange the error-and-burden profile of data
collection. The central research need is to determine when greater disclosure and verbal
elaboration improve substantive measurement—and when they merely produce more text.

## Scope and approach

The broader Dewey project uses screened discovery candidates, source-level inclusion decisions,
concise summaries, citation provenance, and detailed notes. For this preliminary synthesis,
three foundational or directly relevant studies were represented as study records. Seven
atomic findings were extracted with page, table, figure, or section locators. Each finding
separates the authors' claim, the reported evidence, and the reviewer's interpretation. Each
study also received a review-specific appraisal of internal validity, measurement validity,
external validity, and applicability.

The three studies cover different generations and functions of AI interviewing:

- Lucas et al. (2014) isolate the psychological effect of believing a virtual interviewer is
  computer-controlled.
- DeVault et al. (2014) evaluate whether the fully automatic SimSensei system retains the
  interaction quality of its Wizard-of-Oz predecessor.
- Barari et al. (2025) experimentally evaluate LLM-assisted coding and probing across four
  web-survey question modules.

This variation is analytically useful, but it also prevents a single pooled effect. The report
therefore synthesizes mechanisms and trade-offs rather than estimating an average treatment
effect.

## 1. Automation can lower social evaluation—but this is a mechanism, not a verdict

Lucas et al. held the visible virtual interviewer constant while varying whether participants
believed it was controlled by a computer or a person. Computer framing reduced reported fear
of self-disclosure and impression management. Participants also displayed more intense
sadness and received higher blind-observer ratings of willingness to disclose (pp. 98–99).
Because framing was experimentally varied and the study combined self-report with behavioral
and observer measures, it provides moderately strong evidence for a psychological mechanism:
people may feel less judged when they believe no human is immediately evaluating them.

That mechanism is important but easily overstated. Willingness to disclose is not the same as
truthful disclosure, and visible sadness is not a validation criterion. The experiment also
tests perceived agency rather than the quality of autonomous interviewing itself. Its strongest
contribution is thus to explain why an AI interviewer might elicit sensitive material, not to
show that an AI system interprets or follows up on that material well.

## 2. Autonomy and conversational quality can pull in opposite directions

The SimSensei evaluation helps separate the experience of talking to a virtual human from the
performance of the autonomous dialogue system behind it. Participants in the fully automatic
and Wizard-of-Oz cohorts reported broadly similar willingness and comfort sharing. On a
five-point scale, willingness to share was 4.07 in the automatic cohort and 4.03 in the
Wizard-of-Oz cohort; comfort sharing was 3.80 versus 3.92 (DeVault et al., 2014, Table 2,
p. 1067).

Yet the automatic system scored significantly lower on being a good listener (3.56 versus
4.10, standardized difference *d* = 0.61), usability (68.68 versus 74.37, *d* = 0.44), and
rapport (75.43 versus 80.71, *d* = 0.44). This creates an instructive tension: respondents may
remain willing to talk even when conversational responsiveness deteriorates. Disclosure and
interaction quality should therefore be modeled as separate outcomes.

The causal weight of this comparison is limited because the automatic and Wizard-of-Oz samples
were separately recruited rather than randomized concurrent conditions. The study is stronger
as feasibility and design evidence than as an estimate of automation's causal effect. Even so,
it identifies a durable engineering challenge: removing the hidden human can preserve the
interview's surface form without preserving all of its responsive qualities.

## 3. Adaptive probing enriches some answers, not information quality in general

Barari et al. provide the strongest directly applicable evidence in this first extraction
batch. They randomly assigned roughly 2,000 U.S. panel participants to standardized questions,
AI confirmation probes, or AI elaboration/relevance probes across modules concerning national
issues, economic conditions, news sources, and occupation.

Elaboration/relevance probing increased specificity and explanation for opinion questions and
increased word counts and Shannon entropy. It did not consistently improve completeness,
relevance, lexical diversity, or KL divergence (Figures 2–3, pp. 16–18). The distinction
matters: probes often made responses longer and more elaborated, but the additional words did
not reliably depart from the corpus's existing word distribution. “More detailed” and “more
informative” cannot be treated as interchangeable without a task-specific validity test.

The live-coding results add another warning. Respondent-confirmed accuracy varied substantially
by task, from 66.1% for preferred news source to 96.2% for economic sentiment. Independent human
coders agreed less with several AI classifications than respondents did, and respondents chose
“none of the above” much less often. The likely acquiescence effect means that asking a respondent
to confirm an AI interpretation does not produce an uncontaminated ground truth; the interviewer's
suggestion can shape the answer it is supposed to validate (Tables 2–3, pp. 14–15).

## 4. Richer interviewing carries burden and selection costs

The same Barari experiment makes the cost side visible. Elaboration/relevance probing roughly
doubled average completed-interview duration from three to six minutes. It increased dropout by
about two to three percentage points at the first question and produced statistically detectable
but substantively small declines in ease, frustration, and satisfaction—each less than 0.05 on
normalized scales (Figures 4–5, pp. 18–19). Confirmation probes were less costly.

These effects suggest that adaptive probing should be allocated rather than maximized. A useful
system would identify questions and responses for which elaboration has high expected value,
instead of probing nearly every answer. Burden is also a measurement issue: if probing selectively
drives away less patient, mobile, older, or otherwise distinct respondents, gains in within-response
detail may be offset by compositional change in who completes the interview.

## Synthesis: a three-part model of AI interviewer performance

The evidence is easier to reconcile if AI interviewing is treated as three linked but distinct
problems:

1. **Disclosure conditions:** Does the interface reduce evaluation apprehension and encourage
   respondents to speak?
2. **Conversational competence:** Does the system listen, interpret, and probe in ways that are
   relevant, responsive, and usable?
3. **Measurement validity:** Do the resulting answers more accurately capture the construct the
   researcher needs?

Lucas et al. primarily support the first link. SimSensei demonstrates feasibility while showing
losses in the second. Barari et al. provide evidence of selective gains and costs in the second,
but also reveal how difficult the third remains. A strong AI interviewer must perform well across
all three; success on disclosure or text generation cannot substitute for validity.

## Research gaps

The structured comparison brings several gaps into focus:

- **Accuracy and truth remain under-tested.** Most outcomes concern willingness, length,
  linguistic properties, or perceived quality rather than correspondence with an external
  criterion.
- **The causal contribution of adaptivity is unclear.** Studies need to distinguish the effects
  of machine identity, conversational interface, probe content, probe timing, and underlying
  language model.
- **Human interviewer benchmarks are inconsistent.** Standardized forms, Wizard-of-Oz systems,
  perceived human control, and actual human interviewers answer different comparative questions.
- **Selective attrition needs joint analysis with response enrichment.** Studies should report
  whether improved answers among completers compensate for changes in completion and sample
  composition.
- **Long-form qualitative interviewing is still weakly covered.** Short survey modules and
  structured health screenings do not establish performance in interpretive, longitudinal, or
  expert interviews.
- **Model and prompt dependence threaten durability.** Results from one platform and model
  version may age quickly; reproducible configuration reporting and cross-model replication are
  essential.

## Implications for system design

The preliminary evidence favors constrained, auditable assistance over unrestricted probing.
Systems should probe selectively, distinguish clarification from elaboration, allow respondents
to reject or revise machine interpretations without suggestive defaults, and record exactly which
model action produced each answer segment. Evaluation dashboards should keep disclosure,
conversational quality, respondent burden, coding accuracy, and construct validity separate.

The most promising near-term design is therefore not an AI interviewer that simply asks more
follow-ups. It is one that can justify when a follow-up is needed, show what uncertainty it is
trying to resolve, and demonstrate that the resulting information improves a downstream research
decision.

## Conclusion

The early literature supports cautious optimism. AI interviewers can make some respondents feel
safer, elicit more elaboration, and perform useful live coding. But the evidence also shows that
autonomy can reduce rapport, probing can increase burden, and confirmation can introduce its own
bias. The field's decisive next step is to move from demonstrations of engagement and verbosity
to explicit tests of validity: not merely whether people tell an AI more, but whether researchers
learn something more accurate and consequential as a result.

## References

Barari, S., Angbazo, J., Wang, N., Christian, L. M., Dean, E., Slowinski, Z., & Sepulvado, B.
(2025). *AI-Assisted Conversational Interviewing: Effects on Data Quality and Respondent
Experience*. arXiv:2504.13908. https://doi.org/10.48550/arXiv.2504.13908

DeVault, D., Artstein, R., Benn, G., Dey, T., Fast, E., Gainer, A., Georgila, K., Gratch, J.,
Hartholt, A., Lhommet, M., et al. (2014). SimSensei Kiosk: A virtual human interviewer for
healthcare decision support. *Proceedings of AAMAS*, 1061–1068.
https://doi.org/10.5555/2615731.2617415

Lucas, G. M., Gratch, J., King, A., & Morency, L.-P. (2014). It's only a computer: Virtual
humans increase willingness to disclose. *Computers in Human Behavior, 37*, 94–100.
https://doi.org/10.1016/j.chb.2014.04.043

## Evidence and reproducibility

The structured records are stored under `.dewey/synthesis/`. The seven-row export is available
as `evidence-matrix.csv`. Every substantive result above can be traced to a finding record and
source locator. The next review stage is to summarize the remaining unread sources, then extract
and appraise additional included studies before upgrading this report from preliminary to
comprehensive.
