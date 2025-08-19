
# PC Remote Agent — **Blueprint** (for ZenCoder)

> **Goal**: Evolve the stock `main.py` from the Windows‑Use repo into a lean, reliable “poor man’s ChatGPT Agent” for Windows desktop automation using an **outer loop** (Planner → Actor → Critic), with **small, auditable iterations**: `V1` → `V2` → `V3`.
> **Non‑goal**: We do **not** modify Windows‑Use internals. We keep prompts short so the agent preserves its tool schema. We avoid bloat.

---

## 0) Operating Principles (read every time)

* **Outer loop only**: plan → act (Windows‑Use) → critique → (at most one micro‑retry). No “smart agent” frameworks, no graph refactors.
* **Small, reversible steps**: Each version is a single PR with <300 LOC net change. Preserve a clean diff and a clear `repo.md` update.
* **Cost aware**: Prefer budget models (e.g., Qwen‑72B, Gemini Flash‑Lite) for Planner/Critic and a cheap strong Actor (e.g., GPT‑OSS‑120B). Temperature low. Keep prompts short.
* **Deterministic defaults**: Temperatures 0.0–0.2; short token caps; zero vision by default (`use_vision=False`) unless strictly required.
* **Don’t hard‑code user‑specific flows** (e.g., store ZIPs or shopping sites). Keep the system **task‑agnostic**.
* **No Windows‑Use internals touched**: Only build a wrapper around `Agent(llm=..., browser='chrome', use_vision=...)`.
* **Privacy & safety**: Don’t log secrets. Never ask for or print API keys. Guard against credentials in user prompts.
* **Clear success**: Every plan must define a **success probe** (short visible phrase or condition) the Critic can check in the transcript.

---

## 1) Repository Expectations

ZenCoder, you will maintain:

* `main.py` (original starter) and create `v1.py`, `v2.py`, `v3.py` as evolutions. Do **not** delete `main.py`.
* `repo.md`: a living project log updated **after each change** (see template below).
* `logs/` directory: runtime CSV logs (token estimates, verdicts).
* `.env-example`: minimal env keys required to run (no secrets).

### `repo.md` update rules (mandatory after each PR)

Append a dated section with:

```
## YYYY-MM-DD — V{N} Summary
- What changed (bullets, ≤6 lines)
- Why (1–2 lines)
- Models + temps + caps
- How to run (exact CLI)
- Known limitations
- Next step proposal
```

---

## 2) Tech Stack & Keys

* **Windows-Use** (PyPI) + **LangChain** chat models.
* **OpenRouter** for all models via `langchain_openai.ChatOpenAI`.
* **Browser**: Chrome.

### `.env` (example; keep minimal)

```
OPENROUTER_API_KEY=...
OPENROUTER_HTTP_REFERER=https://github.com/your-repo
OPENROUTER_X_TITLE=Windows-Use Personal
# Optional search warm-up (V3)
SERPER_API_KEY=...                # optional
ENABLE_SEARCH=0                   # "1" to enable in V3 only
BUDGET_USD=0.20                   # soft cap guidance (V3)
```

---

## 3) Model Roles (default targets)

* **Planner**: `qwen/qwen-2.5-72b-instruct` **or** `google/gemini-2.5-flash-lite`
  Temp: `0.2`, Max tokens: `~300–400`.
* **Critic**: same as Planner, Temp: `0.0`, Max tokens: `~160–200`.
* **Actor**: `openai/gpt-oss-120b` (Temp: **0.0** to preserve schema compliance); Fallback: `qwen/qwen-2.5-72b-instruct` (Temp: 0.0).

> Do **not** use providers with questionable privacy; avoid DeepSeek models. Keep everything through **OpenRouter** 

---

## 4) Version Plan (what to build, exactly)

### V1 — **Slim Planner → Actor → Critic**

**Purpose**: Prove the outer loop works from `main.py` with minimal changes.

**Files**: create `v1.py`.

**Behavior**:

* Input: single-line user query.
* **Planner** returns JSON: `{"objective": str, "steps": [2..7 literal UI steps], "success_probe": str}`.
  `success_probe` is **one short on-screen phrase** that must appear when done.
* **Actor** builds a short imperative prompt and calls Windows‑Use; capture the **full transcript** (actions + observations).
* **Critic**: PASS if transcript contains `success_probe` (case‑insensitive substring). Else FAIL and produce **one micro follow‑up action**, then run **one** retry only.

**Implementation constraints**:

* Keep the **actor prompt short** (no schemas, no JSON requests to the actor).
* `use_vision=False` by default.
* Temperature: Planner 0.2, Critic 0.0, Actor 0.0.
* Graceful JSON extraction (strip \`\`\`json fences, trailing commas).
* No logging yet (besides stdout).

**CLI**:

```
python v1.py --query "Open Chrome and search for the Louisville weather"
```

**Definition of Done (manual smoke tests)**:

1. “Open Chrome and go to lowes.com” → PASS (probe “Lowe’s” or “lowes.com” appears).
2. “Open Notepad and type ‘hello’” → PASS (probe “Notepad” or typed content visible).

---

### V2 — **Planner vote‑of‑3 + Probe‑aware Critic + CSV log**

**Purpose**: Increase robustness and provide basic observability.

**Files**: create `v2.py` (+ `logs/run_log.csv` on first run).

**Behavior**:

* **Planner vote‑3**: Generate 3 candidate plans and pick the best by a simple heuristic (e.g., longer concrete step list, higher min artifacts—if included—or simply highest step count within bounds).
* **Critic** becomes probe‑aware: PASS only if transcript shows the exact **domain/app context** (if present) **and** contains `success_probe`. Otherwise FAIL with one actionable next step.
* **CSV logger** appends per‑role rows (`planner`, `actor`, `critic`, `run_summary`) with crude token estimates (len/4 heuristic).

**CLI**:

```
python v2.py --query "Turn on Windows dark mode"
```

**Definition of Done**:

* Logs are written with run\_id, models used, and PASS/FAIL.
* One FAIL leads to one micro‑retry; never loops indefinitely.

---

### V3 — **Budget, Secret Guard, Optional Search Warm‑up, Repo Hygiene**

**Purpose**: Add safety & cost control and keep code tidy.

**Files**: create `v3.py`.

**Additions**:

* **Secret guard**: refuse if the user query appears to contain credentials (regex for api key / token / password / bearer / client secret).
* **Budget**: soft cap via `BUDGET_USD`—we don’t calculate real dollars, but gate optional steps (e.g., search warm‑up). If over cap, skip optional calls and continue core flow.
* **Optional Serper warm‑up**: if `ENABLE_SEARCH=1` and the query **looks web‑intent**, fetch 3–5 snippets and append a tiny bullet list to the **Planner** context only. Don’t pass links to Actor.
* **Repo hygiene**: Standardize headers, constants, temperatures, and env reads. Ensure default headers: `HTTP-Referer`, `X-Title`.

**CLI**:

```
python v3.py --query "Find the official NVIDIA driver download page and open it"
python v3.py --query "Open Settings and enable Bluetooth" --enable-search
```

**Definition of Done**:

* Secret-containing prompts are blocked with a clear message.
* With `ENABLE_SEARCH=1`, Planner gets a short “Context (web hints)” section.
* `repo.md` updated with version summary and known limits.

---

## 5) Prompts (exact text ZenCoder should reuse)

### Planner (V1+)

System:

```
You are a Windows task planner.
```

User template:

```
Return JSON ONLY as {"objective": str, "steps": [str...], "success_probe": str}.
- 2–7 literal UI steps (buttons/fields/menus)
- success_probe: ONE short phrase that appears on screen when the task is done

User request:
{{USER_REQUEST}}
```

### Actor directive (V1+)

```
Perform these Windows actions now. Interact with the UI directly.
Do not explain. Do not output JSON. Take actions.

Goal: {{objective}}
Steps:
1) {{step1}}
2) {{step2}}
...
Stop when you see on screen: "{{success_probe}}"
```

### Critic (V1: simple)

```
You are a strict evaluator. PASS if the RAW_TRANSCRIPT contains the exact success_probe
(case-insensitive substring ok). If not, FAIL and give one short next UI action.

Return JSON only: {"verdict":"PASS"|"FAIL","next_action": "<one short step or empty when PASS>"}
```

### Critic (V2+ probe-aware, if you add domain/app checks)

```
You are a strict evaluator. PASS only if:
- The RAW_TRANSCRIPT indicates the intended app or domain context (when obvious from the task).
- The transcript contains the success_probe (case-insensitive substring).

Return JSON only: {"verdict":"PASS"|"FAIL","next_action":"<one short corrective action or empty when PASS>"}
```

---

## 6) Cost & Performance Guardrails

* **Temperatures**: Planner 0.2; Critic 0.0; Actor 0.0.
* **Max tokens (guideline)**: Planner ≤ 320; Critic ≤ 160; Actor ≤ 800.
* **Search warm‑up**: Only if `ENABLE_SEARCH=1` **and** the request is clearly web‑oriented (“search, docs, download, news, price, site:”).
* **Budget**: If estimated tokens suggest overrun, skip warm‑up and proceed with core loop.

---

## 7) Commit & PR Discipline

* One PR per version (V1/V2/V3). Title: `V{N}: short action verb summary`.
* Include `repo.md` update in the same PR. CI is not required; manual verification is fine.
* Keep diffs readable; factor helper functions, but avoid over‑abstraction.

**PR template** (ZenCoder must paste in the PR body):

```
## What changed
- ...

## Why
- ...

## How to run
- `python vN.py --query "..."`

## Models
- planner=..., critic=..., actor=..., temps, max_tokens

## Evidence
- PASS/FAIL snippets, logs path

## Follow-ups
- Proposed next step
```

---

## 8) Testing Playbook (manual)

Run each against V1 → V3:

1. **Simple app**
   `"Open Notepad and type 'hello from agent'"` → PASS, probe “Notepad” or typed content.

2. **Browser basic**
   `"Open Chrome and go to https://www.python.org"` → PASS, probe “Python”.

3. **Settings toggle**
   `"Open Settings and turn on Bluetooth"` → PASS, probe “Bluetooth” + “On”.

4. **Web task (V3 with search hints on)**
   `"Find NVIDIA official driver download page and open it"` → PASS on “NVIDIA Driver Downloads”.

Record observations and issues in `repo.md`.

---

## 9) Error Handling & Safety

* **Secrets guard**: If the user query matches secret patterns (api key / token / password / bearer / client secret), **stop** with a safety message.
* **Resilience**: JSON parsing fallback (strip code fences; remove trailing commas).
* **Retry policy**: At most **one** micro‑retry suggested by the Critic.
* **No infinite loops**; if still FAIL, print final transcript and the critic verdict.

---

## 10) Exact Tasks for ZenCoder (copy/paste checklist)

**Task A — Create V1**

* [ ] Add `v1.py` implementing Slim Planner → Actor → Critic as specified.
* [ ] Defaults: Planner=`qwen/qwen-2.5-72b-instruct`, Critic same, Actor=`openai/gpt-oss-120b`.
* [ ] Temperatures: 0.2 / 0.0 / 0.0 respectively.
* [ ] `use_vision=False`.
* [ ] Print plan JSON, run actor, print critic JSON, run one micro‑retry if FAIL.
* [ ] Update `repo.md` section for V1.

**Task B — Create V2**

* [ ] Add `v2.py` with vote‑of‑3 Planner and probe‑aware Critic.
* [ ] Add `logs/run_log.csv` writer (create folder if missing).
* [ ] Log: timestamps, run\_id, role, model, prompt/output char counts, est tokens, verdict.
* [ ] Update `repo.md` for V2 (include example CLI and a log excerpt).

**Task C — Create V3**

* [ ] Add `v3.py` with Secret guard, Budget module, optional Serper warm‑up for Planner only.
* [ ] Respect `ENABLE_SEARCH` & `SERPER_API_KEY`.
* [ ] Keep actor prompt short (no schemas).
* [ ] Update `.env-example` (or create if missing) with keys listed above.
* [ ] Update `repo.md` for V3 with known limits and next‑step ideas.

---

## 11) Known Pitfalls (read before coding)

* **Overlong actor prompts** can break Windows‑Use tool behavior. Keep them short and imperative.
* **Vision**: default off. Only enable when a task truly needs spatial cues.
* **Bloated “fixes”**: Critic must output **one** short next action, not a new plan.
* **Hard‑coding flows** (e.g., shopping ZIPs) will not generalize—avoid.
* **Model swaps**: Keep roles stable across versions to isolate changes.

---

## 12) Future Considerations (not in scope for V1–V3)

* Tiny **CSV cost dashboard** (merge logs by model; optional price table).
* **Micro‑memory** file appended to Planner prompt with empirical wins (selectors, phrasing, app aliases).
* Toggle **vision=True** for specific tasks only (e.g., drag/drop, canvas UIs).
* Optional **dry‑run** mode that prints the actor prompt without executing.

---

## 13) Run Commands (quick reference)

```
# V1
python v1.py --query "Open Chrome and search for 'Yosemite fall colors'"

# V2
python v2.py --query "Open Settings and turn on Bluetooth"

# V3 (with warm-up)
set ENABLE_SEARCH=1
python v3.py --query "Find the official Python downloads page"
```

---

## 14) Definition of “Perfect Agent” (north star)

* **Agent-quality behavior** on Windows with minimal cost: plan smartly, act reliably, self‑check, and correct once.
* **General-purpose**: works for browsing, apps, settings, light file ops without site/app hard‑coding.
* **Lean**: short prompts, stable temps, few tokens, no bloat. Logs enough to learn, not enough to leak.
* **Autonomous enough**: can run tasks end‑to‑end with one micro‑correction and produce clear PASS/FAIL.

---

**ZenCoder: follow this blueprint exactly. After each step, run the manual smoke tests, commit, open a PR, and update `repo.md` per the template.**
