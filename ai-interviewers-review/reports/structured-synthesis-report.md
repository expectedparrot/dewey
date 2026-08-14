---
title: "AI Interviewers: What the Evidence Supports"
subtitle: "A structured synthesis of disclosure, probing, performance, and validity"
date: "August 14, 2026"
---

> **Evidence boundary.** This report synthesizes the seven sources currently included in the
> Dewey review. Those sources contain eight distinct studies, twelve source-located findings,
> and eight methodological appraisals. Four reviewed synthesis claims organize the evidence.
> The broader discovery corpus contains additional queued and unread material, so this is a
> rigorous synthesis of the included evidence rather than a claim of exhaustive coverage.

## Executive summary

AI interviewers do not simply reproduce human interviews at lower cost. They change the social,
conversational, and measurement conditions under which answers are produced. The included
evidence suggests that those changes can be valuable: perceived automation may lower evaluation
apprehension, adaptive questions can elicit more specific or reflective answers, and some AI-led
interviews receive transcript-quality ratings comparable to trained humans under constrained
online conditions. But none of these findings supports a general conclusion that AI interviews
are equivalent or superior to human interviews.

Four conclusions emerge.

First, machine framing can make disclosure feel safer. In a randomized virtual-human experiment,
participants who believed the interviewer was computer-controlled reported less fear of
self-disclosure and impression management, displayed more sadness, and were judged more willing
to disclose. This is credible evidence for reduced evaluation apprehension as a mechanism. It is
not evidence that the information disclosed was true or clinically valid.

Second, adaptive probing improves particular dimensions of an answer rather than “quality” in
general. LLM probes can increase specificity, explanation, word count, or reflection, but the
effect varies with the purpose of the probe, the question, and the stage of research. Probing
also increases time and can impose modest experience and attrition costs.

Third, AI performance depends heavily on modality and autonomy. Expert evaluators rated voice
AI interviews competitively in one small matched comparison, while an earlier automatic virtual
interviewer lost listening quality, usability, and rapport relative to its human-guided
predecessor. These findings describe different systems and designs, but together they rule out a
simple equivalence claim.

Fourth, the field must distinguish response production from measurement validity. Longer,
richer, or more confidently expressed answers are not necessarily more accurate. The strongest
included validity study uses a witnessed mock event with externally knowable details; most other
studies rely on respondent judgments, human ratings, or textual proxies. The next research
frontier is therefore not merely eliciting more text, but demonstrating that AI interviewing
improves the evidence used for inference.

## Review approach

The review question asks how AI interviewers are designed and evaluated, and how they affect
interview quality, respondent experience, and resulting data relative to human or conventional
interviewing. The included evidence spans virtual-human health screening, LLM-assisted web
surveys, child-witness questioning, qualitative interviewing, probe design, and chatbot
acceptability.

Each paper was separated into its constituent studies. Findings were extracted atomically with
page, section, table, or figure locators. Authors' claims, reported evidence, and reviewer
interpretations were stored separately. Study appraisals considered internal validity,
measurement validity, external validity, and applicability. Findings were then linked to claims
as supporting, contradicting, or qualifying evidence. Confidence reflects the designs and
appraisals, not a vote count across papers.

## 1. Disclosure: reduced judgment is a real but bounded advantage

The clearest mechanism evidence comes from Lucas et al. (2014). Participants completed a health
screening with the same visible virtual human but were randomly led to believe that it was
controlled either by a person or by a computer. Computer framing reduced self-reported fear of
disclosure and impression management. It also increased facial displays of sadness and
blind-observer ratings of willingness to disclose (pp. 98–99).

Holding the visible interviewer constant makes the result unusually informative. The operative
factor was not the agent's appearance, and not necessarily its actual autonomy, but the belief
that a person was not immediately evaluating the respondent. The agreement among self-report,
facial behavior, and transcript ratings supports moderate confidence that perceived automation
can reduce evaluation apprehension in short, sensitive interviews.

The boundary of that conclusion matters. More willingness to disclose does not demonstrate more
truthful disclosure. Sadness is evidence of emotional expression, not diagnostic accuracy.
Moreover, disclosure depends on trust as well as reduced judgment. Đuka and Njeguš's descriptive
Serbian survey found that although 87% of respondents knew what a chatbot was, only 44% had used
one and 88% preferred waiting for a human service agent (pp. 325–326). That result concerns
customer-service agents rather than research interviewers and receives low confidence for this
review. It nevertheless shows that machine interaction can generate distrust rather than safety.

SimSensei provides a further qualification. Participants in automatic and Wizard-of-Oz cohorts
reported similar willingness and comfort sharing, but the cohorts were not randomized. The
finding is consistent with automated interviewing being acceptable once respondents enter the
interaction, yet it cannot establish causal equivalence.

The evidence therefore supports a conditional claim: perceived automation can lower one social
barrier to disclosure, but trust, context, and implementation determine whether that mechanism
becomes an advantage. Researchers should measure truthful or externally validated reporting
separately from comfort and willingness.

## 2. Adaptive probing: useful because it is selective, not because it is conversational

Barari et al. provide the strongest included experiment on LLM-assisted probing. Roughly 2,000
U.S. panel participants were assigned to standardized questions, confirmation probes, or
elaboration/relevance probes across four survey modules. Elaboration and relevance probing
increased specificity and explanation for opinion questions and increased word counts and
Shannon entropy. It did not consistently improve completeness, relevance, lexical diversity, or
KL divergence (Figures 2–3, pp. 16–18).

This pattern is more useful than a blanket finding that the chatbot produced “better” answers.
The system enriched some dimensions—especially detail and explanation—while leaving others
unchanged. More words did not consistently introduce vocabulary that was more distinctive from
the sample's existing distribution. The result supports selective enrichment, not universal
improvement in informational value.

Jacobsen et al. make the selectivity explicit by comparing descriptive, idiographic, clarifying,
and explanatory probes across exploration, requirements, and evaluation tasks. Across 1,287
responses from 64 participants, explanatory probes were often less relevant, specific, and
clear than alternatives. Idiographic probes performed well across several stage-specific
comparisons, while no overall difference in informativeness appeared among probe types (Tables
5–6 and Figures 1–3, pp. 8–12).

The implication is that “adaptive probing” is too coarse a system description. A clarifying
probe attempts to recover meaning; an idiographic probe seeks a concrete personal instance; an
explanatory probe asks for reasons. Their value depends on what the researcher needs to learn at
that moment. Systems should identify the uncertainty that motivates each follow-up rather than
generating another conversational turn by default.

Probing also has costs. In Barari et al., elaboration/relevance probes approximately doubled
average completed-interview time from three to six minutes, increased dropout by roughly two to
three percentage points at the first question, and produced small declines in ease,
frustration, and satisfaction. Confirmation probes imposed less burden (Figures 4–5, pp. 18–19).
The practical objective should therefore be expected information gain per unit of respondent
burden, not the maximum possible number of follow-ups.

Overall confidence in this claim is moderate. Two experiments converge on conditional,
multidimensional effects, but both involve short online tasks. Long qualitative interviews,
repeated interviewing, mobile use, and high-stakes settings may produce different trade-offs.

## 3. Human comparison: competitive performance is not general equivalence

Geiecke and Jaravel compare AI and trained-human interviews across text, voice, and face-to-face
modalities. Sociology PhD evaluators rated transcripts without being told which modality
produced them. Against a hypothetical expert using online text chat, average grades were 3.93
for AI voice, 3.51 for human face-to-face, 2.98 for AI text, and 2.42 for human text. Against a
face-to-face expert benchmark, grades were 3.50, 3.53, 2.70, and 1.99 respectively, with 40
ratings per modality (Table II, pp. 16–18).

These results demonstrate that an AI system—particularly one accepting voice input—can generate
transcripts experts regard as competitive under specified conditions. They also illustrate why
modality cannot be treated as incidental. AI voice and AI text differed substantially, and
online human text interviews received lower ratings than face-to-face human interviews.

The study does not justify a broad equivalence conclusion. Modality samples were small, topics
varied, and the outcome was a subjective rating relative to a hypothetical benchmark. The
evaluators assessed transcripts, not the full embodied experience or the correctness of what
was learned. The appraisal consequently assigns low-to-moderate confidence to comparative
performance claims.

SimSensei supplies contrary design evidence. Its fully automatic system and human-guided
Wizard-of-Oz predecessor elicited similar reported willingness to share, but the automatic
version scored lower on being a good listener (3.56 versus 4.10, *d* = 0.61), usability (68.68
versus 74.37, *d* = 0.44), and rapport (75.43 versus 80.71, *d* = 0.44; Table 2, p. 1067).
Because cohorts were recruited separately, the comparison has high internal-validity concern.
It remains useful engineering evidence: preserving the agent's appearance and interview
structure does not guarantee that automation preserves responsiveness.

The best synthesis is asymmetric. AI systems can approach trained-human transcript quality in
some short, constrained settings. At the same time, autonomy and modality can materially change
rapport, listening, and usability. Evaluation must specify which human benchmark, interaction
mode, interviewer expertise, and outcome are being compared.

## 4. Validity: more text is not the same as better evidence

The review's most consequential distinction is between elicitation success and measurement
validity. Engagement, response length, specificity, perceived accuracy, and expert transcript
ratings describe important properties of an interview. None alone shows that the resulting
data correspond more closely to the construct or event the researcher wants to understand.

Sun et al. offer the strongest included design for testing validity directly. Seventy-eight
children aged six to eight viewed a mock-event video and were randomly assigned to questions
formulated by ChatGPT-3.5 or by naive student interviewers. Human assistants delivered the LLM
questions, so this was a test of question formulation rather than autonomous delivery. The LLM
condition asked 471 questions compared with 872 in the human condition, elicited similar unique
correct details (8.50 versus 7.50, *p* = .290), produced more unique correct information per
question (0.90 versus 0.46, *p* < .001), and elicited less false information overall (pp. 12–14).

This finding receives moderate confidence because randomization and externally knowable event
details support causal and measurement validity. Generalization is constrained by the young
Mandarin-speaking sample, mock forensic setting, human delivery, and comparison with naive
rather than trained forensic interviewers. Even so, the study demonstrates the right validation
logic: measure correct and false content against a criterion, and assess efficiency per question.

Barari et al.'s live-coding results show the danger of weaker validation. Respondent-confirmed
coding accuracy ranged from 66.1% to 96.2% across tasks. Independent human coders disagreed with
the AI more often than respondents did for several questions, while respondents rarely selected
“none of the above.” Confirmation appears vulnerable to acquiescence: presenting an AI
interpretation can shape the response intended to validate that interpretation (Tables 2–3,
pp. 14–15).

Geiecke and Jaravel's randomized meaning-in-life comparison identifies a different benefit.
About 51.7% of AI-interview respondents reported being able to clearly pinpoint sources of
meaning, compared with 41.2% in the open-text condition; fewer said their thoughts were still
evolving (Table IV, pp. 24–27). This supports a reflective effect of conversation. It does not
independently prove that the resulting accounts are more truthful or qualitatively deeper.

The evidence supports a moderate-confidence conclusion: validity is task-specific and must be
tested using independent or external criteria whenever possible. Richness and reflection should
be reported as distinct outcomes rather than used as proxies for truth.

## Implications for research and system design

The findings suggest several design principles.

1. **Define the evidential objective before the conversation.** A system designed to improve
   recall accuracy needs different probes and validation than one designed to discover themes or
   help respondents reflect.
2. **Treat probe selection as a policy.** Each follow-up should have an identified purpose and an
   expected information gain, balanced against time, fatigue, and attrition.
3. **Avoid suggestive confirmation.** Respondents should be able to correct or reject model
   interpretations without being anchored to a single proposed category.
4. **Preserve provenance.** Analysts should be able to distinguish seed answers from content
   elicited by particular AI probes and recover the exact system action behind each segment.
5. **Benchmark the feasible alternative.** “Human interviewer” must specify expertise, modality,
   time, and degree of standardization. Static open text, naive humans, online trained humans,
   and expert face-to-face interviews are not interchangeable controls.
6. **Evaluate multiple outcome families.** Disclosure, conversational quality, burden, coding
   performance, correctness, and construct validity should remain separate.
7. **Use hybrid escalation where appropriate.** AI may be valuable for routine, scalable, or
   low-uncertainty questioning while humans handle sensitive disclosures, unresolved ambiguity,
   or interpretation requiring contextual judgment.

## What remains unknown

The included studies leave several important gaps:

- whether increased disclosure is more truthful or merely more expressive;
- whether gains in short interviews persist in longitudinal or repeated deployments;
- how performance varies across language, culture, age, disability, and digital literacy;
- whether selective attrition offsets improvements among interview completers;
- how model, prompt, voice, latency, and interface independently affect outcomes;
- whether AI-collected qualitative material changes analysts' substantive conclusions;
- how current systems compare with trained experts in long-form interpretive interviews; and
- how rapidly findings become obsolete as models and product interfaces change.

These are not reasons to dismiss AI interviewing. They define the studies needed to turn
promising demonstrations into a mature measurement methodology.

## Conclusion

AI interviewers are best understood as configurable measurement systems. Their strongest
documented advantages are reduced evaluation apprehension, scalable adaptive questioning, and
the ability—under some conditions—to produce interviews judged competitive with human-led
alternatives. Their risks are equally specific: loss of rapport under automation, poorly chosen
or excessive probes, respondent burden, acquiescence in live coding, and confusion between
verbosity and validity.

The field should move beyond asking whether an AI can conduct an interview. The more useful
question is whether a particular interviewer, probe policy, modality, and validation procedure
produce better evidence for a specified research decision than the feasible alternative. On the
current included evidence, the answer is sometimes yes—but only under conditions that need to be
made explicit and tested directly.

## References

Barari, S., Angbazo, J., Wang, N., Christian, L. M., Dean, E., Slowinski, Z., & Sepulvado, B.
(2025). *AI-Assisted Conversational Interviewing: Effects on Data Quality and Respondent
Experience*. https://doi.org/10.48550/arXiv.2504.13908

DeVault, D., Artstein, R., Benn, G., Dey, T., Fast, E., Gainer, A., Georgila, K., Gratch, J.,
Hartholt, A., Lhommet, M., et al. (2014). SimSensei Kiosk: A virtual human interviewer for
healthcare decision support. *Proceedings of AAMAS*, 1061–1068.
https://doi.org/10.5555/2615731.2617415

Đuka, I., & Njeguš, A. (2021). Conversational survey chatbot: User experience and perception.
*Sinteza 2021*, 322–327. https://doi.org/10.15308/Sinteza-2021-322-327

Geiecke, F., & Jaravel, X. (2026). *Conversations at Scale: Robust AI-led Interviews*.
https://doi.org/10.2139/ssrn.4974382

Jacobsen, R. M., Cox, S. R., Griggio, C. F., & van Berkel, N. (2025). Chatbots for data
collection in surveys: A comparison of four theory-based interview probes. *CHI 2025*.
https://doi.org/10.1145/3706598.3714128

Lucas, G. M., Gratch, J., King, A., & Morency, L.-P. (2014). It's only a computer: Virtual
humans increase willingness to disclose. *Computers in Human Behavior, 37*, 94–100.
https://doi.org/10.1016/j.chb.2014.04.043

Sun, Y., Pang, H., Järvilehto, L., Zhang, O., Shapiro, D., Korkman, J., Haginoya, S., &
Santtila, P. (2025). Comparing the performance of a large language model and naive human
interviewers in interviewing children about a witnessed mock-event. *PLOS ONE, 20*(2),
e0316317. https://doi.org/10.1371/journal.pone.0316317

## Reproducibility

The machine-readable reporting context is stored at
`.dewey/synthesis/report-context.json`. The inspectable claim scaffold is
`reports/report-context.md`, and the evidence matrix is `evidence-matrix.csv`. Every empirical
statement in this report derives from a structured finding with a source locator and study
appraisal. `dewey report audit`, `dewey claim audit`, and `dewey doctor` report no structural
issues for the included evidence.
