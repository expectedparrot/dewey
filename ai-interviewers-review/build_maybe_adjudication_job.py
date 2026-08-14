"""Build and inspect, but do not run, second-pass adjudication of Dewey maybes."""

from __future__ import annotations

import json
from pathlib import Path

from edsl import Model, ScenarioList, Survey
from edsl.questions import QuestionDict


INPUT = Path("triage-maybes-2026-08-13.jsonl")
OUTPUT = "triage-maybes-2026-08-13_jobs.ep"

records = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines()]
source_list = json.loads(Path("/tmp/dewey-source-list.json").read_text(encoding="utf-8"))
known_titles = "\n".join(f"- {item['title']}" for item in source_list["sources"])

scenarios = ScenarioList.from_list_of_dicts(
    [{"candidate_id": row["candidate_id"], **row["context"], "known_titles": known_titles} for row in records]
)

question = QuestionDict(
    question_name="adjudication",
    question_text="""
Adjudicate a previously uncertain title/citation for a focused literature review.

Research question: {{ research_question }}
Candidate: {{ title }}
Authors: {{ authors }}
Year: {{ year }}
Abstract if present: {{ abstract }}

Works already in the corpus:
{{ known_titles }}

Return `retrieve` only when the work itself is likely to provide evidence or a close
methodological benchmark about one of these:
1. AI, automated, virtual, or chatbot interviewers used to elicit research data;
2. adaptive or conversational survey/interview systems and generated follow-up probes;
3. direct comparisons of automated, human, conversational, or conventional interviewing;
4. effects on disclosure, rapport, social desirability, response quality, respondent
   experience, measurement error, or interviewer effects in an interview-like setting;
5. an evaluation framework applied closely enough to inform AI interviewer assessment.

Return `exclude` for generic chatbot/dialogue/LLM engineering; agents used for therapy,
tutoring, customer service, or information retrieval rather than research data collection;
generic survey, qualitative, or AI methods; substantive studies merely using interviews;
post-hoc coding without adaptive data collection; and broad background that is not needed
to answer the research question.

Return `duplicate` if this is evidently the same work as one already in the corpus, even
when its citation is truncated, differently formatted, or refers to another version.
Use your scholarly knowledge to resolve recognizable citations, but do not invent missing
facts. When genuinely uncertain, prefer `retrieve` only if obtaining the work is warranted
under the focused criteria above; otherwise exclude it with a candid rationale.
""".strip(),
    answer_keys=["decision", "category", "canonical_title", "rationale"],
    value_types=["str", "str", "str", "str"],
    value_descriptions=[
        "Exactly one of retrieve, exclude, duplicate",
        "One of direct-ai-interview, conversational-benchmark, outcome-mechanism, evaluation-framework, out-of-scope, duplicate",
        "Best normalized title, or the supplied title when unknown",
        "One concise sentence explaining the decision",
    ],
    include_comment=False,
)

model = Model("gpt-4.1", service_name="openai", temperature=0, max_tokens=180)
jobs = Survey([question]).by(scenarios).by(model)
jobs.save(OUTPUT)

print(json.dumps({
    "records": len(records),
    "model": model.to_dict(),
    "estimated_cost": jobs.estimate_job_cost(),
    "job_path": OUTPUT + ".json.gz",
}, indent=2))
print("\nFIRST PROMPT\n")
print(jobs.prompts().select("user_prompt").first())
