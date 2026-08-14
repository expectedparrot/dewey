"""Build and inspect (but do not run) the current Dewey candidate-triage job."""

from __future__ import annotations

import json
from pathlib import Path

from edsl import Model, ScenarioList, Survey
from edsl.questions import QuestionDict


INPUT = Path("triage-2026-08-13.jsonl")
OUTPUT = Path("triage-2026-08-13_jobs.ep")

records = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines()]
scenarios = ScenarioList.from_list_of_dicts(
    [
        {
            "candidate_id": record["candidate_id"],
            **record["context"],
        }
        for record in records
    ]
)

question = QuestionDict(
    question_name="triage",
    question_text="""
You are screening a citation lead for a literature review about {{ topic }}.

Research question: {{ research_question }}
Candidate title or raw citation: {{ title }}
Authors: {{ authors }}
Year: {{ year }}
Abstract, when available: {{ abstract }}
Discovered by citation traversal from: {{ citation_provenance }}

At this title/abstract stage, decide whether the candidate should be retrieved and read.
Include work directly studying AI or automated interviewers, adaptive conversational surveys,
AI-generated interview probes, comparisons with human or conventional interviewing, or close
methodological foundations needed to evaluate interview quality and respondent experience.
Exclude generic AI/LLM work, substantive papers that merely used an interview or survey,
unrelated survey methodology, and citations whose relevance cannot reasonably be established.
Do not infer that a missing abstract is negative evidence. Use `maybe` when the citation is
plausibly relevant but insufficient for an include/exclude judgment.
""".strip(),
    answer_keys=["decision", "score", "rationale"],
    value_types=["str", "float", "str"],
    value_descriptions=[
        "One of include, exclude, or maybe",
        "Relevance confidence from 0 to 1",
        "One concise sentence grounded only in the supplied record",
    ],
    include_comment=False,
)

model = Model("gpt-4.1-mini", service_name="openai", temperature=0, max_tokens=150)
jobs = Survey([question]).by(scenarios).by(model)
jobs.save(str(OUTPUT))

print(json.dumps({
    "records": len(records),
    "model": model.to_dict(),
    "estimated_cost": jobs.estimate_job_cost(),
    "job_path": str(OUTPUT),
}, indent=2))
print("\nFIRST PROMPT\n")
print(jobs.prompts().select("user_prompt").first())
