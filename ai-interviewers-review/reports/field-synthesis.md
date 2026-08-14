---
title: "AI Interviewers: From Conversational Surveys to Scalable Qualitative Research"
subtitle: "A preliminary field synthesis across the reviewed Dewey corpus"
date: "August 14, 2026"
---

> **Review status.** Dewey contains 57 sources discovered through direct search and citation
> traversal, with 839 screened-out candidates and 913 recorded discovery sightings. Eighteen
> sources have been substantively summarized: seven are currently included, nine remain queued
> for final inclusion decisions, and two are excluded or duplicate analytic versions. This report
> synthesizes all 16 distinct, substantively relevant summarized studies while preserving those
> status differences. Three studies currently have finding-level extraction and formal appraisal.

## Executive summary

The AI-interviewer literature has moved through three overlapping stages. Early work asked
whether a conversational interface could administer surveys or health screenings acceptably.
The next wave decomposed interviewer behavior into design features such as conversational style,
active listening, multiple agent roles, and different kinds of probes. Recent LLM systems make
a larger claim: that adaptive interviews can provide qualitative depth at survey scale and, in
some settings, approach human interviewers.

Taken together, the reviewed studies support four conclusions.

First, conversational systems often—but not always—elicit longer, more specific, or more
engaging responses than static forms. Xiao et al. report strong gains over a conventional web
survey; Barari et al. find improvements concentrated in specificity and explanation; Chopra and
Haaland and Geiecke and Jaravel argue that LLM-led interviews reveal richer themes than open-text
alternatives. Yet Cuevas et al. find that apparently fluent interviews often fail to elicit the
motives and individualized examples that constitute qualitative richness, and Zarouali et al.
find no general chatbot advantage in a 14-day longitudinal study.

Second, interviewer behavior matters more than the chatbot label. Active listening, probe type,
tone, timing, and division of labor across agents change response quality and experience.
Conversationality is therefore not a single treatment. Systems that ask many generic follow-ups
can produce more text without producing better evidence.

Third, AI and human interviewers have different—not uniformly ordered—failure modes. AI systems
offer consistency, speed, and reduced evaluation apprehension, but can miss appropriate
follow-ups, give evaluative encouragement, over-classify answers, or lose rapport. Humans can
suggest answers, omit active-listening behaviors, and vary across interviewers. The relevant
question is which error profile is acceptable for a particular research purpose.

Fourth, the field's largest unresolved issue is validity. Disclosure, engagement, response
length, thematic breadth, and linguistic richness are useful intermediate outcomes, but they do
not establish truth or construct validity. A notable exception is Sun et al.'s child-witness
experiment, which evaluates objectively correct and false information. More work needs similarly
external criteria and downstream behavioral validation.

The resulting throughline is that AI interviewers should be understood as configurable
measurement systems, not generic substitutes for human interviewers. Their value depends on the
match among interview purpose, probe policy, respondent population, comparison condition, and
validation criterion.

## Scope and evidence tiers

The corpus spans generative and pre-LLM systems, text and embodied interfaces, surveys and
semi-structured interviews, and populations ranging from online adults to children recalling a
witnessed event. Because these designs answer different questions, this review organizes the
literature by claims and mechanisms rather than calculating a pooled average.

Three evidence tiers are used:

1. **Included and structured:** Barari et al., DeVault et al., and Lucas et al. have atomic
   findings, locators, and study appraisals.
2. **Included and summarized:** Sun et al., Geiecke and Jaravel, Jacobsen et al., and Đuka and
   Njeguš are accepted into the review but await finding-level extraction.
3. **Queued and summarized:** nine directly relevant studies have been read sufficiently for a
   concise summary but await final inclusion and detailed appraisal. They inform the map of the
   field but should carry less weight in definitive conclusions.

The published 2026 Barari article is retained as a version of the already-counted preprint, not
as independent evidence. The child-avatar training study is excluded because the AI serves as
interviewee and coach rather than interviewer.

## 1. The field has evolved from interface comparisons to adaptive interviewing

Early conversational survey studies mainly tested whether a chatbot interface changed response
behavior. Kim et al.'s 2-by-2 experiment separated platform from conversational style, finding
more differentiated responses and less satisficing in chatbot conditions, with casual style
helping only inside the chatbot interface. Xiao et al.'s larger field study compared an
AI-powered conversational survey with Qualtrics across more than 5,200 free-text answers. The
chatbot increased engagement and produced responses rated more informative, relevant, specific,
and clear, including a reported 39% increase in information and 25.7% gain in aggregate response
quality.

These results established that delivery format could affect response production, but neither
system resembles today's open-ended LLM interviewer. Both relied on bounded, pre-LLM behavior
and quality criteria derived largely from conversational maxims. Their historical importance is
to show that some apparent “AI effect” predates generative models: interface pacing, social cues,
and conversational framing already changed respondent behavior.

Đuka and Njeguš provide a useful trust counterpoint. Their descriptive Serbian study documents
familiarity with chatbots but substantial preference for waiting for a human service agent. It
does not directly measure research-interview preference and lacks a conventional-survey control,
so it should not be read as evidence that people reject AI interviews. It does show why general
chatbot familiarity cannot substitute for task-specific acceptability.

## 2. Good automated interviewing is a bundle of conversational skills

Later systems began isolating components of interview conduct. Xiao et al.'s active-listening
chatbot combined acknowledgment, comprehension, and adaptive follow-up behaviors. In a study of
206 users across four topics, active listening improved engagement and response quality relative
to a baseline chatbot. The result suggests that the value of conversation lies partly in showing
that prior content was heard and used, rather than merely presenting one question at a time.

CommunityBots extends this logic from skills to roles. Its multi-agent platform divided public
input elicitation across agents and, in a 96-person evaluation, improved engagement and response
quality while reducing conversational interruptions relative to a single-agent baseline. The
study predates modern LLMs, but it raises a still-relevant design possibility: planning,
rapport-building, clarification, and domain questioning need not all be performed by one agent.

Jacobsen et al. offer the clearest recent decomposition of probing. Their split-plot experiment
compares descriptive, idiographic, clarifying, and explanatory LLM probes across exploration,
requirements, and evaluation tasks. Both probe type and research stage affect response-quality
and experience measures. This makes indiscriminate “adaptive follow-up” an inadequate
description of a system. A probe designed to recover meaning, elicit a personal example, or
explain a cause is a different intervention, and its usefulness depends on the research stage.

Barari et al. reinforce that conclusion experimentally. Their LLM elaboration/relevance probes
increased specificity and explanation for opinion questions as well as word count and Shannon
entropy, but did not consistently improve completeness, relevance, lexical diversity, or KL
divergence. The benefit was selective enrichment, not universal quality improvement. Moreover,
probes were triggered for nearly all seed responses in several modules, implying that current
systems may probe far more often than the marginal value of information warrants.

## 3. Can AI-led interviews produce qualitative depth at scale?

The strongest contemporary claim is that LLMs can occupy the space between open-text survey
boxes and labor-intensive human interviews. Three major studies define this debate.

Chopra and Haaland evaluate AI-led qualitative interviews across economic applications and argue
that dynamic probing generates richer themes than scalable survey alternatives, reveals themes
researchers did not prespecify, relates responses to later behavior, and supports hypothesis
generation and thematic saturation. Geiecke and Jaravel develop a simple text-and-voice system
and compare it with trained human interviewers, respondent assessments, open-text responses, and
content-quality measures across questions about meaning in life, politics, education,
occupations, and policy mental models. They report that short AI interviews approach average
trained-human quality under comparable online conditions and substantially outperform open-text
fields in richness.

Cuevas et al. provide the essential counterargument. Across 399 participants and three systems,
including two LLM interviewers, conventional engagement and communication scores looked good,
but the systems rarely elicited the specific motives and personalized examples associated with
genuinely rich qualitative material. Human and LLM quality ratings also agreed poorly. The
disagreement is not merely that one study is positive and another negative. They operationalize
richness differently. One emphasizes thematic breadth, scalable discovery, and comparative
content measures; the other asks whether interviews recover situated motives and examples that
qualitative researchers consider evidentially important.

Guven et al.'s small same-interface comparison sharpens the issue. Human interviewers elicited
longer answers per question, while the AI asked questions faster and therefore conducted longer
interviews overall; coded specificity and relevance did not significantly differ. An AI can
increase total interaction by moving quickly without matching the depth achieved at each turn.
Turn-level and interview-level richness should therefore be reported separately.

The current synthesis cannot declare the scalability claim settled. It can identify the decisive
question: whether increased thematic coverage and response volume preserve the contextual,
motivational, and interpretive detail needed for the intended qualitative analysis.

## 4. AI-versus-human comparisons reveal different failure modes

Several studies directly or indirectly benchmark humans. Wuttke et al.'s small student study
finds broadly comparable response quality and overall adherence under AI and human interviewing,
but divergent errors. The AI misses appropriate follow-up opportunities and sometimes provides
evaluative encouragement; humans more often omit active listening or suggest answers. Guven et
al. similarly hold chat modality constant and find a speed–depth trade-off rather than a clear
winner. Geiecke and Jaravel report that short AI interviews approach the average quality of
trained humans under matched online conditions, a more demanding benchmark that warrants full
finding-level extraction.

DeVault et al.'s SimSensei work examines a different transition: from a human-controlled
Wizard-of-Oz virtual interviewer to a fully automatic one. The automatic cohort remained willing
to share, but rated the system lower as a listener and lower on usability and rapport. The effect
sizes for listening, usability, and rapport were moderate, although the separately recruited
cohorts prevent a clean causal interpretation. This study shows that retaining the same embodied
agent does not ensure that automation retains conversational quality.

Lucas et al. isolate a psychological benefit humans cannot easily reproduce: participants who
believed the visually identical interviewer was computer-controlled reported less disclosure
fear and impression management, displayed more sadness, and were judged more willing to
disclose. The randomized framing supports reduced evaluation apprehension as a mechanism.
However, perceived automation says little about whether the system asks good questions or
correctly interprets answers.

Together, these studies reject a one-dimensional ranking. AI may be less socially threatening
and more consistent, while humans may be more contextually responsive. Humans introduce their
own variability and suggestiveness; AI introduces systematic omissions, inappropriate
encouragement, and model-specific behavior. Evaluation should compare error types, not just
average quality scores.

## 5. Objective accuracy evidence changes the evaluation standard

Most studies assess engagement, respondent preference, response length, coder-rated quality, or
thematic content. Sun et al. stand out by using a witnessed mock event with externally knowable
details. Seventy-eight children aged six to eight were randomly assigned to questions formulated
by ChatGPT or naive human interviewers, though humans delivered both sets of questions. The
LLM-formulated condition used fewer questions, elicited similar total unique correct information,
more correct information per question, and less false information overall; false information per
question did not differ.

The specialized forensic context and human delivery limit generalization to autonomous AI
interviewers. Even so, the study demonstrates a stronger validation architecture: specify a
ground truth, distinguish correct from false elicitation, and measure efficiency per question.
Comparable designs are needed in other domains using administrative records, known events,
subsequent behavior, expert adjudication, or experimentally assigned experiences.

Barari et al.'s live-coding experiment shows why external validation matters. Respondents often
confirmed AI categories more readily than independent coders did, with evidence consistent with
acquiescence. Asking respondents to confirm the model's interpretation can alter the response it
is meant to validate. Accuracy ranged widely across tasks, with news-source coding substantially
weaker than economic-sentiment coding. Validation must therefore be outcome- and task-specific,
not inferred from overall conversational fluency.

## 6. Burden, longitudinal use, and selection can reverse short-session gains

Positive findings largely come from short, bounded encounters. Barari et al. show that
elaboration/relevance probing doubled average completed-interview time from about three to six
minutes, increased dropout by roughly two to three percentage points at the first question, and
slightly reduced ease and satisfaction. Confirmation probes imposed less burden. More probing
can improve the answers of those who stay while changing who completes the interview.

Zarouali et al.'s preregistered 14-day comparison is therefore especially valuable. Among 304
Dutch participants, web surveys often produced better response characteristics and data quality;
chatbot users supplied fewer words over time and rated the chatbot lower on enjoyment,
usefulness, and security, although chatbot users performed better on attention checks. The
contrast with one-session studies suggests novelty decay, privacy perception, and repeated-use
friction as moderators.

These findings favor selective probing and adaptive stopping over maximizing conversational
turns. Systems should estimate the expected value of a follow-up against respondent burden and
the risk of attrition, especially on mobile devices and in longitudinal designs.

## 7. What is settled, contested, and missing?

### Relatively well supported

- Conversational presentation and adaptive behavior can change response production relative to
  static forms.
- Active listening and probe design materially affect outcomes; “chatbot” is too coarse a
  treatment label.
- Machine framing can reduce evaluation apprehension in sensitive interviewing.
- AI systems can conduct coherent, scalable interviews, but feasibility alone does not establish
  qualitative or measurement validity.
- Benefits and costs vary by question type, task, interface, comparison condition, and duration.

### Still contested

- Whether LLM interviews approach trained-human qualitative depth rather than merely open-text
  survey quality.
- Whether greater length, specificity, and thematic breadth constitute more informative evidence.
- Whether AI's consistency offsets missed probes, evaluative feedback, or systematic coding bias.
- Whether short-session engagement gains survive repeated or longitudinal use.

### Critical gaps

- External validation of truth, construct measurement, and downstream decisions.
- Larger matched comparisons with trained human interviewers and blinded outcome coding.
- Factorial tests separating machine identity, interface, model, prompt, probe policy, and voice.
- Population heterogeneity, accessibility, privacy, language, culture, and digital literacy.
- Selective attrition analyzed jointly with improvements among interview completers.
- Long-form, interpretive, expert, and longitudinal qualitative interviews.
- Reproducible reporting of models, prompts, sampling parameters, latency, failures, and version
  changes.
- Evidence about how analysts use AI-collected material and whether different collection modes
  lead to different substantive conclusions.

## Implications for designing AI interviewers

A defensible AI interviewer should be designed around the inferential task rather than generic
conversation quality. It should:

- define which uncertainty each probe is intended to resolve;
- distinguish clarification, elaboration, explanation, and personal-example probes;
- use respondent confirmations that permit correction without anchoring them to one suggested
  interpretation;
- preserve turn-level provenance so analysts can separate seed answers from AI-elicited content;
- monitor burden and stop when expected informational gain is low;
- report disclosure, conversational quality, burden, coding accuracy, and construct validity as
  separate outcomes;
- expose model and prompt configurations for replication; and
- escalate or hand off when sensitive content, ambiguity, or conversational failure exceeds the
  system's validated scope.

The most promising architecture may be hybrid rather than substitutive: AI can provide scalable
first-pass interviewing, identify ambiguity, and standardize routine probes, while humans handle
interpretive depth, sensitive follow-up, and cases where contextual judgment matters most.

## Conclusion

The reviewed literature has progressed well beyond the question of whether people will answer a
chatbot. It now demonstrates that AI systems can shape disclosure, deploy different interviewing
skills, collect large volumes of open-ended material, and in some contexts approach human or
outperform static-form benchmarks. It also shows that apparent success depends heavily on what
is counted as quality.

The field's central tension is between scale and evidential depth. AI interviewers make adaptive
conversation cheap enough to deploy widely, but scale does not guarantee that interviews recover
truth, causal explanation, personal context, or valid constructs. The next generation of studies
must make those inferential targets explicit. The right question is no longer simply whether AI
can conduct an interview. It is when a particular AI interviewing policy produces evidence that
is more valid, useful, and ethically collected than the feasible alternative.

## Evidence map

| Study | Current Dewey status | Main contribution |
|---|---|---|
| Barari et al. (2025/2026) | Included; structured | Randomized evidence on coding, probing, quality, and burden |
| DeVault et al. (2014) | Included; structured | Automatic virtual interviewer feasibility and rapport trade-offs |
| Lucas et al. (2014) | Included; structured | Reduced evaluation apprehension under machine framing |
| Sun et al. (2025) | Included | Objective correct/false recall under LLM- versus human-formulated questions |
| Geiecke & Jaravel (2026) | Included | AI-led interviews compared with trained humans and open text across domains |
| Jacobsen et al. (2025) | Included | Experimental comparison of four theory-based probe types |
| Đuka & Njeguš (2021) | Included | Early rule-based implementation and trust/UX evidence |
| Chopra & Haaland (2023/2026) | Queued | Qualitative richness, behavioral association, and saturation claims |
| Cuevas et al. (2025) | Queued | Caution that engagement metrics can mask weak qualitative richness |
| Xiao et al. (2020), conversational surveys | Queued | Large field comparison with conventional web surveys |
| Xiao et al. (2020), active listening | Queued | Isolates active-listening behaviors as a design mechanism |
| Zarouali et al. (2024) | Queued | Longitudinal counterevidence on quality, experience, and security |
| Guven et al. (2025) | Queued | Same-interface AI versus human speed/depth comparison |
| Wuttke et al. (2024) | Queued | AI and human interviewer failure modes |
| Kim et al. (2019) | Queued | Separates chatbot platform from conversational style |
| Jiang et al. (2023) | Queued | Multi-agent division of interviewing roles |

## Reproducibility and next step

The structured evidence records are under `.dewey/synthesis/`, and the current seven-finding
export is `evidence-matrix.csv`. Source-level summaries and detailed notes remain separate. The
next step is not more discovery: it is to resolve the nine queued summarized studies, promote or
reject them explicitly, and extend finding-level extraction and appraisal across the studies
that drive the field-level claims above.
