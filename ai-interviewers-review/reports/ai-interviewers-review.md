---
title: "Interviewing at the Marginal Cost of Computation"
subtitle: "What AI Interviewers Change About Disclosure, Adaptivity, and Measurement"
date: "August 2026"
lang: en
---

::: {.abstract}
**Abstract.** Adaptive interviewing has traditionally exchanged standardization and scale for interviewer judgment and conversational depth. AI interviewers relax that production constraint, but their value depends on whether conversational gains become valid measurements rather than merely longer transcripts. This review connects research on virtual humans, conversational surveys, adaptive probing, and criterion-based interview evaluation. Across seven papers, the evidence supports a conditional conclusion: automation can reduce evaluation apprehension and improve selected dimensions of probing and transcript quality, yet effects depend on trust, probe purpose, modality, and the availability of external validity criteria. The field has advanced faster on scalable elicitation than on measurement theory. Its central agenda is therefore to identify which interviewer decisions should be automated, for whom, and against which substantive benchmark.

**Keywords:** artificial intelligence; interview methods; survey methodology; measurement; qualitative research; disclosure
**JEL codes:** C81, C83, C93, D91
:::

::: {.related-resource}
**Explore the evidence behind the review.** Use the interactive dashboard below to inspect paper-level metadata, summaries, notes, and citation relationships. [Open the literature explorer full screen](../ai-interviewers-explorer.html).
:::

<figure class="explorer-panel">
<iframe src="../ai-interviewers-explorer.html" title="Interactive explorer for the AI interviewer literature" loading="lazy"></iframe>
<figcaption>Interactive literature explorer. Select a paper to inspect its summary and source record, or open the dashboard full screen for a larger workspace.</figcaption>
</figure>

# Introduction: Interviewing as a Production Technology

Interviews occupy an awkward place in empirical social science. They can recover context, language, and causal narratives that fixed-response instruments often miss, but the very discretion that makes an interview informative also makes it expensive and difficult to standardize. A skilled interviewer decides when an answer is incomplete, which ambiguity is worth pursuing, how to ask a follow-up without leading the respondent, and when another question would impose more burden than it yields information. These decisions consume scarce labor. Consequently, large-scale data collection has usually purchased comparability and low marginal cost by limiting conversational adaptation.

Generative artificial intelligence changes this production constraint. Once an interview protocol and model are in place, a system can generate contingent follow-up questions for another respondent at close to the marginal cost of computation. It can apply the same high-level rules across thousands of conversations while varying the words and sequence used in each one. The economically relevant comparison is therefore not simply “AI versus human.” It is between feasible systems for producing evidence: fixed forms, lightly conversational surveys, autonomous interviews, and human interviews with different levels of training and supervision.

Lower elicitation costs do not imply better measurement. A fluent system may produce a longer transcript without recovering more of the construct a researcher intends to measure. Respondents may disclose more because they feel less judged, or disclose less because they distrust an automated agent. A probe may increase specificity while also increasing attrition. Expert raters may prefer a transcript whose claims are no more accurate than those in a shorter answer. The same technology can thus improve conversational output, respondent experience, and criterion validity by different amounts—or move them in opposite directions.

This article reviews seven empirical papers that illuminate these margins. The sample is deliberately analytic rather than exhaustive. It includes foundational virtual-human work, survey chatbots, recent experiments with language-model probing, an economics application of AI-led qualitative interviews, and a child-witness experiment with an observable ground truth. It excludes systems used only to code human-conducted interviews and generic service chatbots without a data-elicitation objective. The organizing claim is that AI relaxes the cost and standardization constraints on adaptive interviewing but does not remove the measurement problem. Whether it improves evidence depends on respondent beliefs, the purpose and timing of probes, modality, and validation against outcomes beyond transcript length or user preference.

The literature supports this claim in four steps. Early virtual-human experiments isolate a behavioral channel: perceived automation can reduce evaluation apprehension. More recent conversational-survey studies show that adaptivity has selective benefits rather than a uniform effect on answer quality. Direct human comparisons place some AI modes near trained-human transcript quality but reveal persistent differences in rapport and modality. Finally, criterion-based studies demonstrate why disclosure and richness cannot substitute for validity. Together these results point toward an economics of task allocation and measurement rather than a horse race between interviewer types.

# Scope, Intellectual Lineage, and the Included Evidence

The relevant literature did not begin with large language models. Its intellectual lineage starts with embodied virtual humans designed for sensitive or health-related conversations, passes through rule-based and conversational survey interfaces, and only then reaches generative systems capable of producing open-ended follow-ups. That sequence matters because contemporary AI bundles two distinct treatments: being interviewed by something perceived as nonhuman, and being interviewed by a system capable of linguistic adaptation. Early work helps separate the first mechanism from the second.

| Period | Development | Papers | Interpretive importance |
|---|---|---|---|
| 2014 | Virtual-human interviewing establishes feasibility and manipulates perceived automation | [DeVault et al. (2014)](#ref-devault2014); [Lucas et al. (2014)](#ref-lucas2014) | Identifies evaluation apprehension and perceived agency as mechanisms before modern language models |
| 2021 | Conversational interfaces enter ordinary survey and service settings | [Đuka and Njeguš (2021)](#ref-duka2021) | Shifts attention from technical feasibility to familiarity, trust, and acceptance |
| 2025 | Generative systems enable experiments on probing, coding, and factual recall | [Barari et al. (2025)](#ref-barari2025); [Jacobsen et al. (2025)](#ref-jacobsen2025); [Sun et al. (2025)](#ref-sun2025) | Decomposes design choices and introduces stronger measures of answer quality and validity |
| 2026 | AI-led interviews are proposed as scalable infrastructure for qualitative research | [Geiecke and Jaravel (2026)](#ref-geiecke2026) | Moves the frontier toward deployment, human benchmarks, and the economics of scale |

The papers also play different evidentiary roles. [DeVault et al.](#ref-devault2014) establish the system lineage and show the feasibility of a semi-automated, multimodal interview. [Lucas et al.](#ref-lucas2014) provide the cleanest mechanism evidence on disclosure. [Đuka and Njeguš](#ref-duka2021) bridge specialized virtual humans and broadly accessible chatbots, albeit with limited causal leverage. [Barari et al.](#ref-barari2025) and [Jacobsen et al.](#ref-jacobsen2025) evaluate modern conversational designs and decompose probing into distinct interventions. [Geiecke and Jaravel](#ref-geiecke2026) provide the frontier scale application and comparisons across human and AI modalities. [Sun et al.](#ref-sun2025) serve as a crucial counterpoint because the witnessed event supplies an external criterion against which elicited information can be checked.

These are not seven estimates of a common treatment effect. The systems differ in embodiment, autonomy, voice, task, population, interviewer benchmark, and outcome. Treating them as interchangeable votes would erase precisely the design margins a useful review should expose. The synthesis below therefore asks what each design identifies and uses disagreements to locate boundary conditions.

# From Virtual Humans to Generative Interviewers

The early virtual-human literature suggests a reason automated interviewers might elicit information that respondents withhold from people. In the experiment reported by [Lucas et al. (2014)](#ref-lucas2014), participants interacted with the same virtual interviewer but received different information about whether a person was operating it. Those assigned to the computer-operated framing reported less fear of self-disclosure and less impression management than those who believed a human operator was involved. Blind observers also rated their interview transcripts as showing greater willingness to disclose, and participants displayed more intense sadness. Because the visible interface was held comparatively stable, the result points to perceived human judgment—not merely conversational fluency—as a mechanism.

This mechanism is economically and methodologically important. An automated agent may lower the perceived social price of reporting stigmatized behavior or distress. If so, the relevant design variable is not just model capability but the respondent’s belief about observation, storage, and evaluation. The result also makes clear what has *not* been shown: willingness to disclose is neither truthfulness nor population validity. Reduced impression management could reveal otherwise hidden information, but it could also change how respondents narrate themselves without bringing reports closer to an external criterion.

Evidence from the companion system literature appropriately narrows the claim. [DeVault et al. (2014)](#ref-devault2014) describe SimSensei, a virtual-human interviewer combining speech, nonverbal sensing, and an automated dialogue manager. In its evaluation, automatic and Wizard-of-Oz cohorts reported similar willingness and comfort sharing, but the fully automatic system scored lower as a good listener and on usability and rapport. The comparison provides useful feasibility and design evidence, though it is weaker as a causal estimate because system assignment and implementation differences complicate interpretation.

Nor should low evaluation apprehension be mistaken for universal acceptance. In the smaller survey reported by [Đuka and Njeguš (2021)](#ref-duka2021), familiarity with the idea of a chatbot was much greater than actual use, and respondents strongly preferred waiting for a human service agent. The setting differs from confidential research interviewing, but the tension is revealing. Automation can reduce fear of human judgment while simultaneously lowering trust in competence, empathy, privacy, or recourse. A disclosure advantage is therefore conditional: it depends on which source of apprehension dominates for a respondent and task.

The transition to generative AI does not supersede this older literature. It adds a second channel—adaptive language generation—to the social response produced by perceived automation. Modern evaluations should measure both. Otherwise, a better answer may be attributed to the model’s probe when it actually reflects reduced evaluation apprehension, or a capable probe may look ineffective because respondents distrust the agent delivering it.

# What Adaptivity Produces

The clearest recent result is that “probing” is not a single treatment. Follow-ups can ask for elaboration, request a reason, test relevance, confirm a classification, or pursue respondent-specific material. Their value depends on what is missing from the initial answer and on where the interview sits in its sequence.

[Barari et al. (2025)](#ref-barari2025) experimentally evaluate AI-assisted conversational interviewing across open-ended tasks. Elaboration and relevance probes increased specificity and explanation on two opinion questions and produced longer answers with higher Shannon entropy. Yet the treatment did not consistently improve completeness, relevance, lexical diversity, or distributional similarity. Confirmation probes, meanwhile, had little effect on respondent experience. These patterns reject both an easy optimistic account—conversation improves data quality—and an easy null—probing does nothing. It changes some dimensions of the response and leaves others largely intact.

[Jacobsen et al. (2025)](#ref-jacobsen2025) sharpen this point by comparing four theory-based probe types across 1,287 responses. Explanatory probes were less relevant, specific, and clear than several alternatives. Idiographic probes, which pursue material particular to the respondent, performed better than explanatory probes on multiple outcomes during the requirements and evaluation stages. No overall difference emerged for informativeness. The useful unit of analysis is therefore a probe policy conditioned on interview purpose and stage, not the presence of a chatbot.

Adaptivity also consumes respondent attention. In [Barari et al.](#ref-barari2025), elaboration and relevance probing raised first-question dropout by roughly two to three percentage points and doubled mean completed-interview duration from about three to six minutes. Average movements in normalized ease, frustration, and satisfaction were small, but attrition and time are real components of data-production cost. A probe that enriches the answers of completers can still worsen the realized sample or increase selection if burden falls unevenly across respondents.

These findings suggest a decision rule rather than a blanket design recommendation. Probe when the expected value of resolving a consequential ambiguity exceeds the expected burden and risk of inducing or steering an answer. That rule requires an explicit measurement target. If a study needs a categorical classification, confirmation may be more valuable than narrative elaboration. If it seeks mechanisms or language, respondent-specific follow-up may dominate generic requests for explanation. Systems should also be permitted to stop: universal persistence is not the same as intelligent adaptivity.

# Humans, Machines, and the Quality Frontier

Comparisons with humans are attractive because they offer an intuitive benchmark, but “the human interviewer” is not a stable control condition. A trained qualitative researcher, an untrained online worker, a face-to-face interviewer, and a text-chat interviewer produce different interactions at very different costs. AI performance likewise depends on voice, embodiment, prompting, and the degree of autonomous control. Rankings are meaningful only within a specified task and modality.

[Geiecke and Jaravel (2026)](#ref-geiecke2026) offer a revealing set of expert transcript comparisons. Against an online-text expert benchmark, average grades were 3.93 for AI voice, 3.51 for human face-to-face, 2.98 for AI text, and 2.42 for human text, based on 40 ratings per modality. Against a face-to-face benchmark, AI voice and human face-to-face were essentially level at 3.50 and 3.53, while both text modes scored lower. These results show that an AI-led voice interview can approach a trained-human benchmark under the evaluated conditions. They also show that modality may matter at least as much as the human-machine distinction.

The finding should not be generalized into human equivalence. Expert transcript ratings capture dimensions of conversational and substantive quality, but not every feature of rapport, sampling, construct validity, or downstream usefulness. The small and heterogeneous comparison cells also limit precision. [DeVault et al.’s](#ref-devault2014) earlier results point in the opposite direction on relational outcomes: full automation reduced ratings of listening, usability, and rapport relative to Wizard-of-Oz operation, even as willingness and comfort sharing changed little.

The combined evidence places systems on a multidimensional frontier rather than a single ladder. Automation offers replicability and low marginal cost. Human interviewers may contribute situated judgment, repair, empathy, and accountability. Voice can restore social cues lost in text while potentially increasing evaluation apprehension. The design problem is consequently one of allocation: which decisions should be fixed in advance, delegated to a model, escalated to a human, or audited afterward? Hybrid systems may dominate either pure mode when rare, consequential conversational failures can be detected and escalated cheaply.

# The Measurement Problem

The emerging literature commonly reports answer length, specificity, transcript ratings, respondent satisfaction, or willingness to disclose. Each is potentially useful, but none is synonymous with measurement validity. More text may contain more signal, more noise, or both. A pleasant interaction may improve completion without improving the measure. Agreement between a respondent and an AI-generated code may reflect acquiescence rather than correct classification.

[Sun et al. (2025)](#ref-sun2025) illustrate the value of an external criterion. Children were interviewed about a witnessed mock event, allowing elicited statements to be classified against known details. The language-model interviews produced a similar number of unique correct details to interviews by naive humans (8.50 versus 7.50), more unique correct information per question (0.90 versus 0.46), and less false information overall, while asking 471 questions rather than 872. This is stronger evidence of task-specific measurement performance than a transcript preference because the researcher can distinguish correct from incorrect content. It remains bounded by a structured child-witness setting and a comparison with naive rather than expert interviewers.

[Barari et al.’s](#ref-barari2025) live-coding results expose another validity margin. Respondent-confirmed accuracy ranged from 66.1 to 96.2 percent across tasks, while agreement with independent human coding was lower for several tasks. Respondents also selected “none of the above” less frequently. Confirmation may correct a proposed code, but it can also anchor respondents or encourage acquiescence. A respondent’s endorsement and an independent coder’s assessment answer different questions; neither should silently become ground truth.

Reflective interviews introduce yet another complication. In [Geiecke and Jaravel’s](#ref-geiecke2026) randomized meaning-in-life application, 51.69 percent of AI-interview respondents said they could clearly pinpoint sources of meaning, compared with 41.18 percent in an open-text condition; fewer said their thoughts were still evolving. This may be a valuable treatment effect of guided reflection. But if the goal is to measure a preexisting state, the interview may partly create the object it records. Interactive measurement is not necessarily defective—many interviews are intended to help respondents articulate beliefs—but researchers must distinguish elicitation from intervention.

The general lesson is to define success outside the conversational surface whenever possible. Factual tasks can use known events or records. Construct measurement can use reliability, convergent and discriminant validity, or prediction of later behavior. Qualitative discovery can test whether independent analysts recover novel, consequential themes and whether those themes survive follow-up work. Without such criteria, claims should remain about disclosure, richness, or rated quality rather than validity writ large.

# An Economics Research Agenda

The next phase of research should treat AI interviewing as a problem in the economics of information production. Five questions are especially important.

First, studies should estimate a production frontier rather than report output alone. Relevant inputs include design labor, model and transcription costs, interview duration, monitoring, human escalation, respondent incentives, attrition, and the cost of correcting failures. Relevant outputs depend on the application: factual recall, predictive power, conceptual novelty, classification accuracy, or decision value. Near-zero marginal interviewing cost is not near-zero total cost if validation and oversight are expensive.

Second, designs should decompose interviewer decisions. Randomizing an entire conversational system reveals whether a bundle works in one setting but offers little guidance for improvement. Experiments can separately vary disclosure framing, voice versus text, probe objective, timing, stopping rules, memory, and human escalation. [Jacobsen et al.’s](#ref-jacobsen2025) probe comparison is useful precisely because it opens this black box.

Third, average effects are unlikely to be sufficient. Evaluation apprehension, digital familiarity, language proficiency, topic sensitivity, disability, and prior experience with AI may all change both engagement and measurement error. A system that lowers social pressure for one group may signal surveillance or low accountability to another. Attrition caused by probing can also change composition even when satisfaction among completers barely moves.

Fourth, researchers should study respondent adaptation. As people learn how automated interviewers store, summarize, and act on information, their disclosure strategies may change. Novelty effects in early experiments need not describe equilibrium behavior. Institutional commitments about privacy, human review, and recourse are therefore part of the treatment, not merely implementation details.

Fifth, validation should follow the intended use of the data. An interview used to generate hypotheses faces a different loss function from one used to allocate benefits, diagnose risk, or estimate a population parameter. High-stakes uses require evidence on false statements, leading questions, omitted groups, and auditability. For exploratory research, the important benchmark may instead be whether scaled conversations reveal mechanisms that a structured survey would not have anticipated.

# Conclusion

AI does not make interviewing costless, neutral, or automatically valid. It changes the feasible set. Standardized protocols can now support contingent conversation at a scale previously associated with fixed surveys, while voice and language generation can reproduce parts of the interaction once supplied by trained labor.

The evidence reviewed here gives qualified reasons for optimism. Perceived automation can reduce evaluation apprehension; well-chosen probes can improve specificity and explanation; AI voice interviews can approach trained-human transcript ratings; and, in one criterion-based setting, a language model elicited correct information efficiently while producing less false information than naive interviewers. Each result has a boundary. Trust can offset disclosure gains, probes impose burden and work selectively, modality changes comparisons, and richer transcripts do not establish validity.

The field has therefore progressed further in scalable elicitation than in measurement theory. Its most valuable next studies will specify the target construct before choosing the conversational technology, identify which interviewer decisions create value, benchmark claims against independent criteria, and compare total production costs. The central question is no longer whether a machine can conduct something recognizable as an interview. It is when machine-mediated conversation produces evidence worth using.

# References

<div id="ref-barari2025" class="reference"></div>
Barari, Soubhik, Jarret Angbazo, Natalie Wang, Leah M. Christian, Elizabeth Dean, Zoe Slowinski, and Brandon Sepulvado. 2025. “AI-Assisted Conversational Interviewing: Effects on Data Quality and Respondent Experience.” [DOI](https://doi.org/10.48550/arXiv.2504.13908) · [Explorer record](../ai-interviewers-explorer.html#source=src_2a843bf69441).

<div id="ref-devault2014" class="reference"></div>
DeVault, David, Ron Artstein, Grace Benn, Teresa Dey, Ed Fast, Alesia Gainer, Kallirroi Georgila, Jonathan Gratch, Arno Hartholt, Margaux Lhommet, and others. 2014. “SimSensei Kiosk: A Virtual Human Interviewer for Healthcare Decision Support.” [DOI](https://doi.org/10.5555/2615731.2617415) · [Explorer record](../ai-interviewers-explorer.html#source=src_ca3e033a6b39).

<div id="ref-duka2021" class="reference"></div>
Đuka, Isidora, and Angelina Njeguš. 2021. “Conversational Survey Chatbot: User Experience and Perception.” [DOI](https://doi.org/10.15308/Sinteza-2021-322-327) · [Explorer record](../ai-interviewers-explorer.html#source=src_db7efbce68d9).

<div id="ref-geiecke2026" class="reference"></div>
Geiecke, Friedrich, and Xavier Jaravel. 2026. “Conversations at Scale: Robust AI-led Interviews.” [DOI](https://doi.org/10.2139/ssrn.4974382) · [Explorer record](../ai-interviewers-explorer.html#source=src_6541b25ef96e).

<div id="ref-jacobsen2025" class="reference"></div>
Jacobsen, Rune M., Samuel Rhys Cox, Carla F. Griggio, and Niels van Berkel. 2025. “Chatbots for Data Collection in Surveys: A Comparison of Four Theory-Based Interview Probes.” [DOI](https://doi.org/10.1145/3706598.3714128) · [Explorer record](../ai-interviewers-explorer.html#source=src_af8750017209).

<div id="ref-lucas2014" class="reference"></div>
Lucas, Gale M., Jonathan Gratch, Aisha King, and Louis-Philippe Morency. 2014. “It’s Only a Computer: Virtual Humans Increase Willingness to Disclose.” *Computers in Human Behavior* 37: 94–100. [DOI](https://doi.org/10.1016/j.chb.2014.04.043) · [Explorer record](../ai-interviewers-explorer.html#source=src_418b4c4f1a21).

<div id="ref-sun2025" class="reference"></div>
Sun, Yongjie, Haohai Pang, Liisa Järvilehto, Ophelia Zhang, David Shapiro, Julia Korkman, Shumpei Haginoya, and Pekka Santtila. 2025. “Comparing the Performance of a Large Language Model and Naive Human Interviewers in Interviewing Children about a Witnessed Mock-Event.” *PLOS ONE* 20. [DOI](https://doi.org/10.1371/journal.pone.0316317) · [Explorer record](../ai-interviewers-explorer.html#source=src_5e242e942988).
