---
title: "Interviewing at the Marginal Cost of Computation"
subtitle: "What AI Interviewers Change About Disclosure, Adaptivity, and Measurement"
author: "Literature review"
lang: en
---

::: {.abstract}
**Abstract.** Interview research has traditionally traded standardization and scale for interviewer judgment and conversational depth. Automated interviewers alter that production constraint: they can administer a common protocol while responding contingently to what each person says. This review synthesizes seventeen empirical studies spanning virtual humans, conversational surveys, language-model probing, scaled qualitative research, and criterion-based interviews. The literature has developed in three waves. Early systems established that perceived automation changes disclosure and rapport. Conversational-survey research then showed that platform, listening behavior, and probe design—not conversation alone—shape response quality and burden. Recent language-model studies make adaptivity inexpensive and flexible, but their strongest results concern transcript richness rather than measurement validity. Across the field, the evidence supports a conditional conclusion: automated interviewing can improve particular elicitation tasks, but performance depends on the respondent, modality, probe policy, comparator, and intended use of the data. The research frontier is therefore not machine-versus-human equivalence. It is the design and validation of an interview production function that allocates decisions among protocols, models, respondents, and human reviewers.
:::

**Keywords:** artificial intelligence; interview methods; survey methodology; measurement; qualitative research; disclosure

**JEL codes:** C81, C83, C93, D91

::: {.explorer-callout}
**Explore the evidence.** The embedded literature explorer contains the 17 included papers, 38 unscreened metadata leads, source summaries, structured findings, appraisals, and citation relationships. [Open the explorer full screen](../ai-interviewers-explorer.html).
:::

<figure id="explorer-embed" class="explorer-panel">
<iframe id="literature-explorer" src="../ai-interviewers-explorer.html" title="Interactive explorer for the AI interviewer literature" loading="lazy"></iframe>
<figcaption>Interactive literature explorer. Select an included paper to inspect its evidence record, or switch on the full traversal network to examine discovery leads.</figcaption>
</figure>

# 1. Introduction

Interviews are a production technology for evidence. A questionnaire fixes most interviewer decisions before data collection; a qualitative interview delegates many of them to a person who can clarify, probe, repair misunderstandings, and pursue unanticipated material. That discretion can reveal mechanisms and meanings that a fixed form would miss. It is also expensive, difficult to reproduce, and a source of interviewer effects. The familiar methodological trade-off is therefore not simply between quantitative and qualitative data. It is between standardization, adaptivity, scale, and judgment.

Automated conversational systems change this feasible set. A system can ask thousands of respondents the same opening question while generating a different follow-up for each answer. It can record every intervention, enforce stopping rules, and operate in text or voice at low marginal cost. Those properties matter for economics because they potentially lower the price of producing contextual evidence and make experimental variation in interviewer behavior unusually tractable.

But elicitation is not measurement. Longer answers may contain more relevant information, more repetition, or more model-induced framing. A respondent may disclose more to a machine because it seems nonjudgmental, or less because it seems untrustworthy. A probe may improve specificity among completers while increasing attrition. An expert may prefer a transcript that is no more accurate than a short answer. The appropriate question is thus not whether an AI can sustain a plausible conversation. It is when machine-mediated conversation produces evidence that is more useful for a specified research purpose.

This article reviews seventeen empirical papers selected for that question. The corpus includes foundational virtual-human experiments, pre-LLM survey chatbots, recent systems that generate adaptive probes, economics applications of long-form AI interviews, matched human comparisons, and an interview task with observable ground truth. Papers used only to analyze human-conducted interviews and generic service chatbots are outside scope. The review is analytic rather than exhaustive: studies enter because they identify a mechanism, design margin, comparator, or validity problem.

The literature is best understood as three overlapping generations. The first studied the *social meaning of automation*: whether a virtual interviewer changes evaluation apprehension, disclosure, rapport, or usability. The second studied the *design of conversational surveys*: whether interactivity, listening, style, and topic management improve answers relative to static forms or simpler chatbots. The third studies *generative adaptivity*: whether language models can choose useful probes, conduct extended interviews, and approach human performance. This history matters because current systems combine all three channels. A modern AI interview treatment changes who appears to be listening, how the exchange is presented, and what follow-up is asked.

The central result is conditional. Automation can improve selected elicitation outcomes, but there is no general conversational advantage and no general human-equivalence result. Effects depend on the function being automated, the comparison condition, modality, duration, respondent beliefs, and the criterion used to define quality. The field has advanced much further in making rich conversation scalable than in establishing when the resulting evidence is valid.

## 1.1 The seventeen-study field map

The corpus does not contain seventeen estimates of a common effect. It contains a sequence of designs that move different margins:

| Research margin | Studies | What the comparison identifies |
|---|---|---|
| Perceived automation and embodied agents | [DeVault et al. (2014)](#ref-devault2014); [Lucas et al. (2014)](#ref-lucas2014); [Đuka and Njeguš (2021)](#ref-duka2021) | Disclosure, rapport, usability, and trust when the apparent interviewer changes |
| Platform and conversational presentation | [Kim et al. (2019)](#ref-kim2019); [Xiao et al. (2020a)](#ref-xiao2020tell); [Zarouali et al. (2024)](#ref-zarouali2024) | Chatbot versus web form, conversational style, and repeated-use effects |
| Listening and conversation architecture | [Xiao et al. (2020b)](#ref-xiao2020hear); [Jiang et al. (2023)](#ref-jiang2023); [Cuevas et al. (2025)](#ref-cuevas2025) | Active listening, agent specialization, and LLM versus scripted follow-up |
| Probe policy | [Seltzer et al. (2023)](#ref-seltzer2023); [Barari et al. (2025)](#ref-barari2025); [Jacobsen et al. (2025)](#ref-jacobsen2025) | Respondent-specific versus generic probes, probe type, timing, response quality, and burden |
| Long-form and scaled qualitative interviewing | [Chopra and Haaland (2023)](#ref-chopra2023); [Geiecke and Jaravel (2026)](#ref-geiecke2026) | Feasibility, thematic discovery, modality, respondent reflection, and production at scale |
| Matched AI-human performance | [Guven et al. (2025)](#ref-guven2025); [Wuttke et al. (2024)](#ref-wuttke2024) | Differences in pacing, follow-up, guideline adherence, and failure modes under more comparable protocols |
| Criterion-based accuracy | [Sun et al. (2025)](#ref-sun2025) | Correct and false information when the researcher knows what occurred |

This map also clarifies the evidentiary hierarchy. Randomized feature comparisons identify particular design margins more cleanly than bundled platform comparisons. Matched human comparisons are more interpretable than comparisons across modality and interviewer expertise. External criteria support stronger measurement claims than word count, satisfaction, or transcript preference. These differences govern the synthesis below.

# 2. From the Social Meaning of Automation to Conversational Surveys

The intellectual starting point is not language generation. It is the observation that respondents react socially to an interviewer even when the interviewer is a computer. [DeVault et al. (2014)](#ref-devault2014) demonstrated the feasibility of an embodied, semi-structured health interviewer combining speech, nonverbal sensing, and dialogue management. Its fully automatic version maintained willingness and comfort sharing at levels similar to an earlier Wizard-of-Oz implementation, but it was rated lower as a listener and on usability and rapport. Because the cohorts were separately recruited, this is not a clean causal estimate of automation. It nevertheless established an enduring distinction: a system may successfully elicit personal material while remaining detectably worse at interactional repair and relationship management.

[Lucas et al. (2014)](#ref-lucas2014) isolated a more specific mechanism by varying whether participants believed a virtual interviewer was controlled by a human or a computer. Computer framing reduced fear of self-disclosure and impression management; blind observers also rated the resulting transcripts as showing greater willingness to disclose, and participants displayed more intense sadness. The mechanism is evaluation apprehension. If a respondent expects less social judgment from a machine, the private cost of revealing stigmatized or emotional material can fall.

That result is foundational but bounded. Willingness to disclose is not truthfulness, and lower human judgment does not imply greater trust in data storage, competence, or recourse. [Đuka and Njeguš (2021)](#ref-duka2021) illustrate the countervailing channel. In their small survey, awareness of chatbots greatly exceeded actual use and respondents strongly preferred waiting for a human service agent. The setting was customer service rather than confidential research, but it shows why “people prefer machines for sensitive questions” is too simple. Human evaluation can deter disclosure; perceived machine incompetence or opacity can deter participation.

The next wave moved from embodied agents to ordinary survey interfaces. [Kim et al. (2019)](#ref-kim2019) crossed chatbot versus web presentation with formal versus casual conversational style. Chatbot administration reduced nondifferentiation, but the effect depended on style: platform and tone interacted rather than contributing separable, universal gains. Ease and dropout did not differ significantly. The treatment was therefore not “conversation” in the abstract; it was a particular combination of interface conventions and language.

[Xiao et al. (2020a)](#ref-xiao2020tell) shifted the focus toward open-ended elicitation. Their conversational survey produced 39 percent more information and 25.7 percent higher aggregate coded response quality than a conventional open-ended survey across more than 5,200 responses. This is important evidence that a bounded, pre-LLM system can improve more than respondent preference. Yet its outcomes—informativeness, relevance, specificity, and clarity—remain properties of answers, not independent tests of construct validity.

The later longitudinal comparison by [Zarouali et al. (2024)](#ref-zarouali2024) supplies a valuable negative case. Across fourteen days, conventional web surveys often performed better on response characteristics, data quality, and user evaluation; chatbot participants supplied fewer words over time and rated enjoyment, usefulness, and security less favorably. The chatbot performed better on attention checks. Repetition changes the result: an interface that seems engaging in a single session may impose friction or privacy concerns when it becomes routine.

Together, these studies overturn a platform-level account. A conversational shell can alter disclosure, satisficing, attention, and burden, but the direction is not stable. What matters is the behavioral mechanism activated by the interface and how that mechanism interacts with topic and duration.

# 3. What the Interviewer Does: Listening, Architecture, and Probe Policy

The core design advance in this literature is a move from asking whether a chatbot works to asking which interviewer functions create value. Three functions recur: demonstrating understanding, managing the structure of a conversation, and selecting a follow-up question.

## 3.1 Listening and conversation management

[Xiao et al. (2020b)](#ref-xiao2020hear) experimentally added comprehension and active-listening skills to an interview chatbot. Relative to a baseline system, the full design improved perceived comprehension, user interest, chat experience, engagement duration, response length, and manually coded response quality. Because the comparison varies a defined bundle of listening functions within the same general medium, it is more informative for design than a chatbot-versus-form contrast. The caveat is that intent recognition varied across topics, revealing that apparent listening depends on classification quality beneath the conversational surface.

[Jiang et al. (2023)](#ref-jiang2023) decomposed architecture differently. CommunityBots assigned topics to multiple coordinated agents and compared that design with a single-agent chatbot. Participants were more engaged, gave more specific, clear, and expansive responses, and experienced fewer conversational interruptions. Agent multiplicity itself is unlikely to be the causal primitive; the treatment bundled topic specialization, handoffs, and conversation management. The useful result is that state management and topical organization are part of interview quality, not merely engineering details.

[Cuevas et al. (2025)](#ref-cuevas2025) provide the necessary counterweight. Comparing a dynamic prober, a member-checking LLM, and a hard-coded baseline, they found high average relevance and clarity but low cognitive empathy and palpability. Aside from follow-up quality, the LLM conditions did not reliably outperform the scripted system. Fluent contingency therefore need not produce the concrete, respondent-centered evidence valued in qualitative research. A cheap deterministic policy may perform competitively when the task is narrow and the evaluation criterion is conventional response quality.

## 3.2 Probe choice is a policy, not a switch

Generative models make it tempting to treat probing as a binary treatment: either a system follows up or it does not. The evidence instead describes a policy problem. A useful probe must diagnose what is missing, select an objective, formulate a nonleading question, and decide whether the expected informational value exceeds respondent burden.

[Seltzer et al. (2023)](#ref-seltzer2023) demonstrate respondent-specific generation in SmartProbe. Market researchers rated 69 percent of 300 generated probes as good or very good. In parallel samples, 76 percent of SmartProbe-elicited responses received those ratings, compared with 25 percent under generic probing. This is strong feasibility evidence for conditioning on the preceding answer, but weak causal evidence: the samples were not randomized, systems were bundled, and the evaluation was conducted in-house.

[Barari et al. (2025)](#ref-barari2025) provide a broader experimental test. Elaboration and relevance probes increased specificity and explanation for two opinion questions, as well as word count and Shannon entropy. They did not consistently improve completeness, relevance, lexical diversity, or distributional similarity. The same probes increased first-question dropout by roughly two to three percentage points and doubled mean completed-interview duration from about three to six minutes. Small average changes in reported ease or frustration do not remove these production costs: attrition can alter the realized sample even if completers tolerate the experience.

[Jacobsen et al. (2025)](#ref-jacobsen2025) compare four theory-based probe types across 1,287 responses. Explanatory probes were less relevant, specific, and clear than several alternatives. Idiographic probes, which pursue material particular to the respondent, performed better on multiple outcomes during requirements and evaluation stages, while informativeness showed no overall probe difference. There is consequently no universally optimal follow-up. Probe value is indexed to the interview stage, the deficiency in the initial answer, and the target outcome.

The combined evidence suggests a decision rule. Probe when resolving a consequential ambiguity is worth the added time, selection risk, and possibility of steering the respondent. Confirmation may be appropriate for a classification target; idiographic follow-up may be better for mechanisms; a scripted probe may dominate an LLM when the relevant deficiency is predictable. Intelligent adaptivity also requires stopping. A system that always asks another plausible question is persistent, not necessarily informative.

# 4. From Short Answers to Qualitative Evidence at Scale

Two studies make the economic promise of generative interviewing especially concrete. [Chopra and Haaland (2023)](#ref-chopra2023) conducted roughly half-hour text interviews with U.S. stock-market nonparticipants. More than 95 percent of 395 participants completed; the median respondent produced about 610 words. Follow-up questions revealed risk beliefs and misconceptions that were obscured by initial explanations centered on low income. This is evidence that adaptive interviews can uncover candidate mechanisms beneath a one-shot response. It is not, by itself, proof that the discovered themes are correct or complete.

[Geiecke and Jaravel (2026)](#ref-geiecke2026) push the production frontier further, applying a common interview architecture across subjective well-being, political choice, education and occupation, and policy mental models. In expert transcript comparisons, AI voice interviews approached human face-to-face performance and outperformed both text modes under the reported benchmarks. In a randomized meaning-in-life application, AI-interview respondents were more likely than open-text respondents to say they could clearly identify sources of meaning. The applications demonstrate versatility, large-sample deployment, and the possibility of discovering unanticipated categories.

These papers change the role of qualitative evidence in economics. When interview cost falls, qualitative work need not be confined to a small preparatory sample. Researchers can examine heterogeneity in mechanisms, estimate the prevalence of themes, and connect narratives to experimental assignments or administrative outcomes. But scale does not dissolve the epistemic role of the interviewer. The prompt, model, stopping rule, and coding pipeline jointly produce the data. A system that helps respondents articulate a belief may also change that belief; an interview can be both measurement and treatment.

The appropriate comparison is therefore total research production, not API cost. Design labor, piloting, respondent time, monitoring, privacy safeguards, transcript validation, coding, and failure correction remain inputs. AI makes contingent language cheap. It does not make the interpretation of that language free.

# 5. Humans and Machines Are Bundles of Capabilities

Human comparisons are attractive because they promise a simple ranking. The studies instead show why “human interviewer” and “AI interviewer” are underspecified treatments.

[Guven et al. (2025)](#ref-guven2025) held modality and interview guide relatively constant by randomly assigning forty participants to human or locally hosted AI text interviewers using the same interface. Humans elicited longer responses per question; the AI asked questions faster and the sessions lasted longer overall. Coded specificity and relevance did not differ significantly. The small sample cannot establish equivalence, but it shows that pacing and answer quality need not move together.

[Wuttke et al. (2024)](#ref-wuttke2024) compared AI and student interviewers conducting political interviews from identical questionnaires. Aggregate response quality and guideline adherence were broadly similar, yet the failure modes differed. The AI missed follow-up opportunities and sometimes gave evaluative encouragement; humans more often omitted active listening or suggested answers. Similar averages can conceal errors with different consequences for measurement and audit.

[Geiecke and Jaravel (2026)](#ref-geiecke2026) add trained interviewers and modality variation. Against an online-text expert benchmark, mean grades were 3.93 for AI voice, 3.51 for human face-to-face, 2.98 for AI text, and 2.42 for human text; against a face-to-face benchmark, AI voice and human face-to-face were nearly level. These cells are small and the ratings subjective, but the ordering makes an essential point: modality can matter at least as much as whether the interviewer is human.

The earlier SimSensei evidence completes the picture. [DeVault et al. (2014)](#ref-devault2014) found that full automation reduced perceived listening, usability, and rapport relative to Wizard-of-Oz operation even when willingness to share was similar. Human control, voice, embodiment, expertise, and interface are separate dimensions. A single machine-human coefficient averages over them.

The design problem is consequently one of task allocation. Protocols are good at consistency; models at low-cost contingent generation; humans at situated repair, accountability, and handling rare consequential cases. Hybrid systems may dominate pure modes when failures can be detected and escalated. But escalation itself must be studied: a nominally automated interview may recreate human evaluation apprehension if respondents expect hidden review.

# 6. The Measurement Problem

Most studies in this field evaluate the conversational surface: words, specificity, engagement, satisfaction, rapport, or expert transcript ratings. These outcomes are useful intermediate products. They should not silently become evidence that an interview measures the intended construct.

[Sun et al. (2025)](#ref-sun2025) offer the corpus’s clearest external criterion. Children were interviewed about a witnessed mock event, so statements could be checked against known details. The language-model interviews elicited a similar number of unique correct details to naive-human interviews (8.50 versus 7.50), more correct information per question (0.90 versus 0.46), and less false information while asking 471 rather than 872 questions. This is stronger task-specific performance evidence than transcript preference. It remains bounded by a structured event, child witnesses, and naive rather than expert human interviewers.

[Barari et al. (2025)](#ref-barari2025) expose a different validity problem in respondent-confirmed coding. Confirmation accuracy ranged from 66.1 to 96.2 percent across tasks, while agreement with independent human coding was lower for several tasks. Respondents selected “none of the above” less frequently. Confirmation can repair a proposed code, but it can also anchor or invite acquiescence. Respondent endorsement and independent coding are different criteria, and neither automatically supplies ground truth.

The rest of the corpus can be organized by distance from the target construct. Word count and duration measure production. Relevance, specificity, clarity, and differentiation measure answer properties, as in [Kim et al. (2019)](#ref-kim2019), [Xiao et al. (2020a)](#ref-xiao2020tell), and [Jacobsen et al. (2025)](#ref-jacobsen2025). Engagement and satisfaction measure respondent experience. Expert transcript ratings, used by [Geiecke and Jaravel (2026)](#ref-geiecke2026), measure professional judgment about the evidence available in a transcript. Known events, records, later behavior, or validated constructs are closer to external validity.

No single level is always required. A hypothesis-generation interview may be successful if independent analysts recover novel themes that survive later investigation. A diagnostic or allocation interview requires calibration, false-positive and false-negative analysis, and auditability. A population measure requires sampling and measurement invariance in addition to good conversation. Claims should therefore name the level supported: richer responses, better experience, stronger rated transcripts, or valid measurement.

# 7. A Research Agenda for the Economics of AI Interviewing

The literature now supports a more demanding experimental agenda.

First, estimate production frontiers. Studies should report design and monitoring labor, model and transcription expense, respondent time, attrition, human escalation, and correction costs alongside the relevant output. Cheap interviews can be expensive evidence if validation is labor intensive.

Second, randomize interviewer decisions rather than entire opaque systems. Disclosure framing, voice, embodiment, probe objective, timing, memory, stopping, and escalation can be varied separately. The active-listening experiment of [Xiao et al. (2020b)](#ref-xiao2020hear), the architecture comparison of [Jiang et al. (2023)](#ref-jiang2023), and the probe comparison of [Jacobsen et al. (2025)](#ref-jacobsen2025) are useful because they begin to open the bundle.

Third, measure heterogeneity and selection. Evaluation apprehension, digital familiarity, language, disability, topic sensitivity, and prior AI experience can change both participation and response error. Probe-induced attrition may alter sample composition even when average satisfaction among completers changes little.

Fourth, benchmark against the intended use. Factual interviews can use known events or administrative records. Construct measurement can use reliability, convergent validity, and prediction. Discovery studies can test whether themes replicate across interviewers, models, and follow-up samples. The criterion should be specified before a conversational metric is chosen.

Fifth, study equilibrium trust. Respondents’ beliefs about storage, model training, hidden human review, and recourse are part of the treatment. Early novelty effects may not survive routine deployment. The contrast between lower evaluation apprehension in [Lucas et al. (2014)](#ref-lucas2014) and weaker repeated chatbot evaluations in [Zarouali et al. (2024)](#ref-zarouali2024) makes this an empirical, not merely ethical, issue.

Finally, compare failure distributions rather than only averages. Humans and models omit different probes, lead in different ways, and fail at different times. A useful system may not minimize average error; it may make consequential errors observable, auditable, and cheap to escalate.

# 8. Conclusion

AI interviewing is neither a fluent replacement for qualitative researchers nor simply a richer survey widget. It is a reallocation of decisions in the production of evidence. The seventeen studies reviewed here show a field moving from the social effects of virtual interviewers, through conversational interface and listening design, to flexible language-model probing and scaled qualitative deployment.

Three conclusions survive that broader synthesis. First, automation changes respondent behavior, but disclosure advantages are conditional on trust and do not establish truth. Second, adaptivity has value when a probe is matched to a particular informational deficiency; generic conversation and indiscriminate follow-up do not reliably improve data. Third, promising human comparisons remain task- and modality-specific, while the strongest measurement claim in the corpus comes from the unusual study that observes the underlying event.

The field’s achievement is to make standardized adaptivity inexpensive. Its unresolved problem is to decide when that adaptivity improves the evidence a researcher ultimately needs. Progress will come from defining the target first, decomposing interviewer decisions, measuring total costs and heterogeneous effects, and validating beyond the conversational surface.

# References

<div id="ref-barari2025" class="reference"></div>
Barari, Soubhik, Jarret Angbazo, Natalie Wang, Leah M. Christian, Elizabeth Dean, Zoe Slowinski, and Brandon Sepulvado. 2025. “AI-Assisted Conversational Interviewing: Effects on Data Quality and Respondent Experience.” [DOI](https://doi.org/10.48550/arXiv.2504.13908) · [Explorer record](../ai-interviewers-explorer.html#source=src_2a843bf69441).

<div id="ref-chopra2023" class="reference"></div>
Chopra, Felix, and Ingar Haaland. 2023. “Conducting Qualitative Interviews with AI.” CESifo Working Paper 10666. [DOI](https://doi.org/10.2139/ssrn.4572954) · [Explorer record](../ai-interviewers-explorer.html#source=src_2fc31ffa6791).

<div id="ref-cuevas2025" class="reference"></div>
Cuevas, Alejandro, Jennifer V. Scurrell, Eva M. Brown, Jason Entenmann, and Madeleine I. G. Daepp. 2025. “Collecting Qualitative Data at Scale with Large Language Models: A Case Study.” *Proceedings of the ACM on Human-Computer Interaction*. [DOI](https://doi.org/10.1145/3710947) · [Explorer record](../ai-interviewers-explorer.html#source=src_0876e37522c7).

<div id="ref-devault2014" class="reference"></div>
DeVault, David, Ron Artstein, Grace Benn, Teresa Dey, Ed Fast, Alesia Gainer, Kallirroi Georgila, Jonathan Gratch, Arno Hartholt, Margaux Lhommet, and others. 2014. “SimSensei Kiosk: A Virtual Human Interviewer for Healthcare Decision Support.” [DOI](https://doi.org/10.5555/2615731.2617415) · [Explorer record](../ai-interviewers-explorer.html#source=src_ca3e033a6b39).

<div id="ref-duka2021" class="reference"></div>
Đuka, Isidora, and Angelina Njeguš. 2021. “Conversational Survey Chatbot: User Experience and Perception.” [DOI](https://doi.org/10.15308/Sinteza-2021-322-327) · [Explorer record](../ai-interviewers-explorer.html#source=src_db7efbce68d9).

<div id="ref-geiecke2026" class="reference"></div>
Geiecke, Friedrich, and Xavier Jaravel. 2026. “Conversations at Scale: Robust AI-led Interviews.” [DOI](https://doi.org/10.2139/ssrn.4974382) · [Explorer record](../ai-interviewers-explorer.html#source=src_6541b25ef96e).

<div id="ref-guven2025" class="reference"></div>
Guven, Semra Yuksel, Tobias Gårdhus, Andreas Bjerre-Nielsen, and Hjalmar Bang Carlsen. 2025. “Comparing AI-led to Human-led Chat-based Interviews: Motivations, Initial Results, and Challenges.” [Explorer record](../ai-interviewers-explorer.html#source=src_8f39b52d2f72).

<div id="ref-jacobsen2025" class="reference"></div>
Jacobsen, Rune M., Samuel Rhys Cox, Carla F. Griggio, and Niels van Berkel. 2025. “Chatbots for Data Collection in Surveys: A Comparison of Four Theory-Based Interview Probes.” [DOI](https://doi.org/10.1145/3706598.3714128) · [Explorer record](../ai-interviewers-explorer.html#source=src_af8750017209).

<div id="ref-jiang2023" class="reference"></div>
Jiang, Zhiqiu, Mashrur Rashik, Kunjal Panchal, Mahmood Jasim, Ali Sarvghad, Pari Riahi, Erica DeWitt, Fey Thurber, and Narges Mahyar. 2023. “CommunityBots: Creating and Evaluating a Multi-Agent Chatbot Platform for Public Input Elicitation.” *Proceedings of the ACM on Human-Computer Interaction* 7. [DOI](https://doi.org/10.1145/3579469) · [Explorer record](../ai-interviewers-explorer.html#source=src_a09d64694611).

<div id="ref-kim2019" class="reference"></div>
Kim, Soomin, Joonhwan Lee, and Gahgene Gweon. 2019. “Comparing Data from Chatbot and Web Surveys: Effects of Platform and Conversational Style on Survey Response Quality.” *CHI 2019*. [DOI](https://doi.org/10.1145/3290605.3300316) · [Explorer record](../ai-interviewers-explorer.html#source=src_aa3e71d53846).

<div id="ref-lucas2014" class="reference"></div>
Lucas, Gale M., Jonathan Gratch, Aisha King, and Louis-Philippe Morency. 2014. “It’s Only a Computer: Virtual Humans Increase Willingness to Disclose.” *Computers in Human Behavior* 37: 94–100. [DOI](https://doi.org/10.1016/j.chb.2014.04.043) · [Explorer record](../ai-interviewers-explorer.html#source=src_418b4c4f1a21).

<div id="ref-seltzer2023" class="reference"></div>
Seltzer, Josh, James Pan, Kathy Cheng, Yichen Sun, Sreekar Kolagati, Junchen Lin, and Sarah Zong. 2023. “SmartProbe: A Virtual Moderator for Market Research Surveys.” arXiv:2305.08271. [DOI](https://doi.org/10.48550/arXiv.2305.08271) · [Explorer record](../ai-interviewers-explorer.html#source=src_20b583c660b2).

<div id="ref-sun2025" class="reference"></div>
Sun, Yongjie, Haohai Pang, Liisa Järvilehto, Ophelia Zhang, David Shapiro, Julia Korkman, Shumpei Haginoya, and Pekka Santtila. 2025. “Comparing the Performance of a Large Language Model and Naive Human Interviewers in Interviewing Children about a Witnessed Mock-Event.” *PLOS ONE* 20. [DOI](https://doi.org/10.1371/journal.pone.0316317) · [Explorer record](../ai-interviewers-explorer.html#source=src_5e242e942988).

<div id="ref-wuttke2024" class="reference"></div>
Wuttke, Alexander, Matthias Aßenmacher, Christopher Klamm, Max M. Lang, Quirin Würschinger, and Frauke Kreuter. 2024. “AI Conversational Interviewing: Transforming Surveys with LLMs as Adaptive Interviewers.” [DOI](https://doi.org/10.48550/arXiv.2410.01824) · [Explorer record](../ai-interviewers-explorer.html#source=src_a7e84b286007).

<div id="ref-xiao2020hear" class="reference"></div>
Xiao, Ziang, Michelle X. Zhou, Wenxi Chen, Huahai Yang, and Changyan Chi. 2020b. “If I Hear You Correctly: Building and Evaluating Interview Chatbots with Active Listening Skills.” *CHI 2020*. [DOI](https://doi.org/10.1145/3313831.3376131) · [Explorer record](../ai-interviewers-explorer.html#source=src_924a2313c5a7).

<div id="ref-xiao2020tell" class="reference"></div>
Xiao, Ziang, Michelle X. Zhou, Q. Vera Liao, Gloria Mark, Changyan Chi, Wenxi Chen, and Huahai Yang. 2020a. “Tell Me About Yourself: Using an AI-Powered Chatbot to Conduct Conversational Surveys with Open-ended Questions.” *ACM Transactions on Computer-Human Interaction* 27 (3). [DOI](https://doi.org/10.1145/3381804) · [Explorer record](../ai-interviewers-explorer.html#source=src_645a7d05436c).

<div id="ref-zarouali2024" class="reference"></div>
Zarouali, Brahim, Theo Araujo, Jakob Ohme, and Claes de Vreese. 2024. “Comparing Chatbots and Online Surveys for (Longitudinal) Data Collection.” *Communication Methods and Measures* 18 (1): 72–91. [DOI](https://doi.org/10.1080/19312458.2022.2156489) · [Explorer record](../ai-interviewers-explorer.html#source=src_43270b46dc12).
