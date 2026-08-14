"""Add reviewed study, finding, appraisal, and claim links for the queued full-text tranche."""

from __future__ import annotations

from dewey.evidence import EvidenceStore
from dewey.repo import DeweyRepo


RECORDS = [
    {
        "source_id": "src_0876e37522c7",
        "study": {"label": "Cuevas et al. three-chatbot richness evaluation", "design": "three-condition comparative experiment", "population": "online adult participants", "sample_size": 399, "setting": "conversational study of views about AI", "intervention": "dynamic-prober and member-checker LLM chatbots", "comparator": "hard-coded baseline chatbot", "methods": ["participant experience measures", "human coding of response quality and qualitative richness"], "measures": ["relevance", "clarity", "specificity", "cognitive empathy", "palpability"]},
        "finding": {"author_claim": "LLM chatbots improved experience but did not reliably produce richer qualitative evidence.", "evidence_statement": "Across coded segments, relevance averaged 87.2% and clarity 82.1%, but cognitive empathy averaged 31.6% and palpability 22.2%; apart from follow-up quality, the LLM conditions did not significantly outperform the naive baseline.", "reviewer_interpretation": "Conversational fluency and conventional response-quality scores can coexist with weak qualitative richness, directly qualifying general claims about adaptive probing.", "outcome": "qualitative richness", "direction": "no general improvement", "measure": "human-coded communicative quality and richness", "certainty": "moderate", "locators": [{"section": "7.1 Coding Results Overall and Across Groups", "figure": "Figure 5"}]},
        "judgment": "moderate confidence", "applicability": "Direct evidence on LLM conversational data collection; the topic and operationalization of richness bound generalization.",
        "claims": {"claim_afb1fe75ab9d": "qualifies", "claim_5e6f2020b1ed": "supports"},
    },
    {
        "source_id": "src_2fc31ffa6791",
        "study": {"label": "Chopra and Haaland AI qualitative interview study", "design": "large online AI-led qualitative interview with mixed qualitative and quantitative validation", "population": "U.S. stock-market nonparticipants able to save", "sample_size": 395, "setting": "roughly 30-minute online text interviews", "intervention": "adaptive AI qualitative interviewer", "comparator": "closed-ended and one-shot open-ended survey measures", "methods": ["inductive coding", "respondent evaluation", "quantitative coding"], "measures": ["completion", "effort", "naturalness", "themes and behavioral associations"]},
        "finding": {"author_claim": "AI interviews can sustain effort and reveal explanations hidden beneath one-shot answers.", "evidence_statement": "More than 95% completed the interview; the median interview lasted 27 minutes and produced about 610 respondent words, while probing revealed risk beliefs and investing misconceptions obscured by initial low-income explanations.", "reviewer_interpretation": "This is strong feasibility and discovery evidence, although the value of emergent themes is not equivalent to criterion validity.", "outcome": "engagement and thematic depth", "direction": "positive", "measure": "completion, duration, text volume, and inductive themes", "certainty": "moderate", "locators": [{"section": "3.3 Results", "page": "15-18", "figure": "Figures 3-4"}]},
        "judgment": "moderate confidence", "applicability": "Highly relevant economics application, with validation bounded by one focal population and interview purpose.",
        "claims": {"claim_afb1fe75ab9d": "supports", "claim_0eea6a57de7b": "supports", "claim_5e6f2020b1ed": "qualifies"},
    },
    {
        "source_id": "src_43270b46dc12",
        "study": {"label": "Zarouali et al. longitudinal chatbot survey comparison", "design": "preregistered longitudinal chatbot-versus-web-survey comparison", "population": "Dutch adult participants", "sample_size": 304, "setting": "14-day repeated data collection", "intervention": "messaging-platform chatbot survey", "comparator": "conventional web survey", "methods": ["longitudinal response analysis", "user evaluation"], "measures": ["response characteristics", "data quality", "enjoyment", "usefulness", "security"]},
        "finding": {"author_claim": "Chatbot collection did not provide a general longitudinal data-quality or experience advantage.", "evidence_statement": "Web surveys often had more favorable response characteristics and quality, chatbot respondents supplied fewer words over time, and chatbot ratings of enjoyment, usefulness, and security were lower, although attention-check performance favored the chatbot.", "reviewer_interpretation": "Conversational interfaces can underperform conventional forms when repeated use and privacy perceptions matter; effects depend on metric and deployment horizon.", "outcome": "longitudinal data quality and experience", "direction": "mixed negative", "measure": "response behavior, attention checks, and user ratings", "certainty": "moderate", "locators": [{"section": "Results and General discussion", "page": "12-17"}]},
        "judgment": "moderate confidence", "applicability": "Direct mode comparison for repeated chatbot surveys, less direct for generative long-form interviewing.",
        "claims": {"claim_0eea6a57de7b": "contradicts", "claim_afb1fe75ab9d": "qualifies"},
    },
    {
        "source_id": "src_645a7d05436c",
        "study": {"label": "Xiao et al. conversational survey field study", "design": "large field comparison of conversational and conventional open-ended surveys", "population": "online survey participants", "sample_size": 600, "setting": "mostly open-ended survey with more than 5,200 responses", "intervention": "AI-powered conversational survey chatbot", "comparator": "Qualtrics online survey", "methods": ["between-mode field comparison", "human response coding"], "measures": ["engagement", "informativeness", "relevance", "specificity", "clarity"]},
        "finding": {"author_claim": "The conversational survey increased engagement and response quality.", "evidence_statement": "The chatbot elicited 39% more information and 25.7% higher aggregate response quality across informativeness, relevance, specificity, and clarity than the conventional survey.", "reviewer_interpretation": "A bounded pre-LLM adaptive system can improve coded open-response quality at scale, though Gricean metrics do not establish broader validity.", "outcome": "open-ended response quality", "direction": "positive", "measure": "human-coded Gricean response quality", "certainty": "moderate", "locators": [{"section": "4.4 Summary of Findings"}]},
        "judgment": "moderate confidence", "applicability": "Foundational comparative evidence for conversational surveys; technology predates general-purpose LLMs.",
        "claims": {"claim_afb1fe75ab9d": "supports", "claim_0eea6a57de7b": "supports", "claim_5e6f2020b1ed": "qualifies"},
    },
    {
        "source_id": "src_8f39b52d2f72",
        "study": {"label": "Guven et al. matched text AI-human comparison", "design": "randomized synchronous text interview comparison", "population": "adult study participants", "sample_size": 40, "setting": "chat interviews using an identical guide and interface", "intervention": "locally hosted OpenHermes 2.5 Mistral 7B interviewer", "comparator": "non-expert human interviewers", "methods": ["random assignment", "coded transcript comparison"], "measures": ["response length", "specificity", "relevance", "interview pace"]},
        "finding": {"author_claim": "AI and human text interviews showed different pacing but similar coded specificity and relevance.", "evidence_statement": "Humans elicited longer responses per question, while the AI asked questions faster and produced longer interviews overall; coded specificity and relevance did not differ significantly.", "reviewer_interpretation": "Holding text modality constant narrows the comparison, but the small sample and non-expert human benchmark preclude an equivalence conclusion.", "outcome": "human-AI transcript performance", "direction": "mixed", "measure": "response length and coded specificity and relevance", "certainty": "low", "locators": [{"section": "4 Results"}]},
        "judgment": "low confidence", "applicability": "Direct modality-matched comparison, limited by sample size, interviewer expertise, and an older local model.",
        "claims": {"claim_0eea6a57de7b": "qualifies"},
    },
    {
        "source_id": "src_924a2313c5a7",
        "study": {"label": "Xiao et al. active-listening chatbot evaluation", "design": "live randomized chatbot feature comparison", "population": "U.S. and Canadian MTurk adults", "sample_size": 206, "setting": "four common interview topics", "intervention": "chatbot with comprehension and active-listening skills", "comparator": "baseline interview chatbot", "methods": ["live user experiment", "manual coding of 824 responses"], "measures": ["response quality", "engagement", "agent comprehension", "user interest and experience"]},
        "finding": {"author_claim": "Active-listening capabilities improved engagement and elicited response quality.", "evidence_statement": "The full chatbot significantly outperformed the baseline across agent comprehension, user interest, chat experience, engagement duration, response word count, and manually coded response quality.", "reviewer_interpretation": "Specific conversational capabilities—not chatbot presence alone—can improve elicitation, although intent models performed unevenly across topics.", "outcome": "active-listening interview quality", "direction": "positive", "measure": "user ratings, engagement, word count, and coded response quality", "certainty": "moderate", "locators": [{"section": "5.2.4 Results", "table": "Table 6"}]},
        "judgment": "moderate confidence", "applicability": "Strong design evidence for active listening in bounded pre-LLM interview chatbots.",
        "claims": {"claim_afb1fe75ab9d": "supports", "claim_0eea6a57de7b": "supports"},
    },
    {
        "source_id": "src_a09d64694611",
        "study": {"label": "CommunityBots multi-agent public-input experiment", "design": "between-subject multi-agent versus single-agent chatbot experiment", "population": "U.S. crowd workers", "sample_size": 96, "setting": "public input across household, work, and health domains", "intervention": "three-agent CommunityBots with conversation and topic management", "comparator": "single-agent chatbot baseline", "methods": ["random assignment", "quantitative and qualitative response analysis"], "measures": ["engagement", "specificity", "clarity", "expansiveness", "interruptions"]},
        "finding": {"author_claim": "Dividing topics across managed agents improved elicitation and conversational flow.", "evidence_statement": "CommunityBots participants were significantly more engaged, provided more specific, clear, and expansive responses, and experienced fewer conversational interruptions than the single-agent baseline.", "reviewer_interpretation": "Interviewer architecture and topic management affect output, but the multi-agent treatment bundles several interface and conversation changes.", "outcome": "multi-agent elicitation quality", "direction": "positive", "measure": "engagement, coded quality, and interruptions", "certainty": "low to moderate", "locators": [{"section": "6.1-6.2 Results"}]},
        "judgment": "low-to-moderate confidence", "applicability": "Relevant design evidence for public-input elicitation; not a generative-model comparison.",
        "claims": {"claim_afb1fe75ab9d": "supports", "claim_0eea6a57de7b": "supports"},
    },
    {
        "source_id": "src_a7e84b286007",
        "study": {"label": "Wuttke et al. controlled AI-human political interview comparison", "design": "small randomized controlled AI-versus-human interview study", "population": "university students", "sample_size": None, "setting": "political interviews with identical questionnaires", "intervention": "LLM conversational interviewer", "comparator": "student human interviewer", "methods": ["random assignment", "qualitative and quantitative guideline coding"], "measures": ["response quality", "guideline adherence", "engagement", "failure modes"]},
        "finding": {"author_claim": "AI interviewing was viable and broadly comparable to human interviewing, with different implementation failures.", "evidence_statement": "Human coding found broadly similar response quality and overall guideline adherence; the AI more often missed follow-up opportunities or gave evaluative encouragement, while humans more often missed active listening or suggested answers.", "reviewer_interpretation": "Comparable averages conceal substantively different failure modes, and the small student sample makes the result proof-of-concept evidence.", "outcome": "guideline adherence and response quality", "direction": "mixed comparable", "measure": "coded interviewer behavior and response quality", "certainty": "low", "locators": [{"section": "4 Findings and 5 Discussion"}]},
        "judgment": "low confidence", "applicability": "Direct contemporary AI-human comparison but a small monitored student study.",
        "claims": {"claim_0eea6a57de7b": "qualifies", "claim_afb1fe75ab9d": "qualifies"},
    },
    {
        "source_id": "src_aa3e71d53846",
        "study": {"label": "Kim et al. platform-by-style survey experiment", "design": "2 by 2 experiment varying web versus chatbot platform and formal versus casual style", "population": "adult survey participants", "sample_size": 117, "setting": "structured survey administration", "intervention": "chatbot survey with formal or casual style", "comparator": "web survey with formal or casual style", "methods": ["factorial experiment", "qualitative thematic analysis"], "measures": ["response differentiation", "dropout", "ease", "enjoyment"]},
        "finding": {"author_claim": "Conversational platform and style jointly reduced satisficing.", "evidence_statement": "The chatbot produced more differentiated responses than the web survey (platform F(1,102)=9.83, p<.01), with a platform-by-style interaction (F(1,102)=14.33, p<.001); dropout and ease of use did not differ significantly.", "reviewer_interpretation": "Interface and tone interact: a chatbot label or layout alone is not the operative treatment, and structured-response differentiation is only one quality dimension.", "outcome": "survey satisficing", "direction": "positive conditional", "measure": "response differentiation index", "certainty": "moderate", "locators": [{"section": "Non-differentiation", "page": "7", "figure": "Figure 2"}]},
        "judgment": "moderate confidence", "applicability": "Useful causal evidence on conversational style in structured surveys; indirect for open-ended AI interviewing.",
        "claims": {"claim_0eea6a57de7b": "supports", "claim_afb1fe75ab9d": "qualifies"},
    },
]


repo = DeweyRepo.discover()
store = EvidenceStore(repo.root)
represented = {source_id for study in store.studies() for source_id in study.source_ids}
finding_links: dict[str, list[tuple[str, str]]] = {}
for item in RECORDS:
    if item["source_id"] in represented:
        raise RuntimeError(f"Evidence already exists for {item['source_id']}")
    study = store.create_study(item["study"], item["source_id"])
    finding = store.create_finding(item["finding"], study.study_id)
    appraisal = store.set_appraisal(
        {
            "framework": "review-specific mixed-method risk-of-bias and applicability appraisal",
            "framework_version": "1",
            "dimensions": [{"name": "design and inference", "judgment": item["judgment"], "rationale": item["finding"]["reviewer_interpretation"], "locators": item["finding"]["locators"]}],
            "overall_judgment": item["judgment"],
            "applicability": item["applicability"],
            "reviewer": "Codex full-text review",
        },
        study.study_id,
    )
    repo.append_log("study.create", study_id=study.study_id, source_ids=study.source_ids)
    repo.append_log("finding.add", finding_id=finding.finding_id, study_id=study.study_id)
    repo.append_log("appraisal.set", appraisal_id=appraisal.appraisal_id, study_id=study.study_id)
    for claim_id, relationship in item["claims"].items():
        finding_links.setdefault(claim_id, []).append((finding.finding_id, relationship))

for claim_id, links in finding_links.items():
    claim = store.claim(claim_id)
    payload = claim.model_dump(mode="json")
    payload["evidence"].extend(
        {"finding_id": finding_id, "relationship": relationship, "rationale": "Full-text evidence added in the expanded reviewed tranche."}
        for finding_id, relationship in links
    )
    updated = store.update_claim(claim_id, payload)
    repo.append_log("claim.update", claim_id=updated.claim_id, added_findings=len(links))

print(f"Added {len(RECORDS)} studies, findings, and appraisals; updated {len(finding_links)} claims.")
