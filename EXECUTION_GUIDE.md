# Execution Guide

This runbook turns `MIGRATION_PLAN.md` into a Microsoft Agent Framework application, deploys it as a Microsoft Foundry hosted agent, and publishes the source to the `tanmoycuat` GitHub profile.

Run each stage separately and complete its check before continuing.

## 1. Repair and verify local tools

The current machine has Python 3.12.10, GitHub CLI authentication for `tanmoycuat`, Azure Developer CLI 1.25.4, and the Foundry extensions. Git 2.36.1 is installed at `C:\Users\se-tansan01\AppData\Local\Programs\Git\cmd\git.exe`, but the current terminal does not include that directory in `PATH`. The current Foundry sample requires `azd >= 1.27.1`.

Open PowerShell and run:

```powershell
$gitPath = "$env:LOCALAPPDATA\Programs\Git\cmd"
$env:Path = "$gitPath;$env:Path"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($userPath -split ';') -notcontains $gitPath) {
  [Environment]::SetEnvironmentVariable("Path", "$userPath;$gitPath", "User")
}
winget upgrade Microsoft.Azd
```

The first two commands make Git available in the current terminal. The user-level update makes it available to newly opened terminals. After the `azd` upgrade completes, close and reopen the terminal, then verify:

```powershell
git --version
gh auth status
azd version
azd extension list
py --version
```

Ensure:

- Git returns a version.
- GitHub CLI shows `tanmoycuat` as the active account.
- `azd` is version 1.27.1 or newer.
- `microsoft.foundry` is installed without an incompatibility warning.
- Python is 3.10 or newer.

If needed, refresh the unified Foundry extension:

```powershell
azd extension install microsoft.foundry
```

## 2. Authenticate and select a Foundry project

Authenticate interactively:

```powershell
az login
azd auth login
```

Do not paste credentials or tokens into project files.

Use the Foundry Toolkit in VS Code to select an existing Foundry project, or create one during initialization. Record these non-secret values:

```text
Azure subscription ID
Resource group
Foundry project endpoint
Default model deployment name
Azure region
```

Check that the region supports hosted agents, the selected models, Toolbox, and Skills. Skills are preview and currently require public network access to their API.

## 3. Capture the current repository before conversion

After Git is available:

```powershell
git status --short
git remote -v
```

Do not delete the current `agents/`, `skills/`, or `realestate/` directories. They are the migration source and rollback baseline.

Create a working branch if this directory is already a Git repository:

```powershell
git switch -c feature/foundry-hosted-agent
```

If it is not a Git repository:

```powershell
git init
git switch -c feature/foundry-hosted-agent
```

## 4. Inspect the maintained Foundry sample

Create a temporary sibling folder so sample initialization cannot overwrite this repository:

```powershell
$samplePath = Join-Path (Split-Path $PWD -Parent) "foundry-toolbox-sample"
New-Item -ItemType Directory -Force $samplePath
Push-Location $samplePath
azd ai agent init -m "https://github.com/microsoft-foundry/foundry-samples/blob/main/samples/python/hosted-agents/agent-framework/responses/04-foundry-toolbox/azure.yaml"
Pop-Location
```

Use that generated project as the reference for dependency versions, `azure.yaml`, the Responses host, and Toolbox integration. Do not copy its demonstration tools or credentials.

## 5. Create the simplified project structure

Create this layout in the current repository:

```text
src/
  realestate_agent/
    __init__.py
    main.py
    agent.py
    skills.py
    data.py
    models.py
    calculations.py
    reports.py
    config.py
skills-baseline/
tests/
  test_calculations.py
  test_skills.py
  test_workflow.py
  test_hosted_agent.py
  evaluation_cases.jsonl
Dockerfile
.dockerignore
.env.example
pyproject.toml
agent.yaml
azure.yaml
toolbox.yaml
```

Use the modules as follows:

| File | Responsibility |
|---|---|
| `main.py` | Build the agent and start `ResponsesHostServer` |
| `agent.py` | Model selection, command routing, specialist factory, concurrent workflow |
| `skills.py` | Discover, load, validate, cache, and record Foundry Skill versions |
| `data.py` | Call Toolbox tools and normalize evidence with provenance |
| `models.py` | Pydantic requests, evidence, specialist results, and final result |
| `calculations.py` | All mortgage, rental, investment, comparison, and score calculations |
| `reports.py` | JSON, Markdown, and PDF rendering |
| `config.py` | Environment validation and model profiles |

Do not create a Python class for every legacy command. Treat commands and specialist roles as configuration loaded from Foundry Skills.

## 6. Create the Python environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Add these dependencies to `pyproject.toml`, using versions from the generated Foundry sample where applicable:

```text
agent-framework-foundry
agent-framework-foundry-hosting>=1.0.0b260813
azure-identity
httpx
pydantic
pydantic-settings
python-dotenv
reportlab>=4.0
pytest
pytest-asyncio
```

Install the project:

```powershell
python -m pip install -e .
```

## 7. Implement deterministic models and calculations

Implement `models.py` first:

- `AnalysisRequest`
- `PropertyProfile`
- `EvidenceItem`
- `EvidenceBundle`
- five specialist result models
- `FinancialAssumptions`
- `AnalysisResult`
- `ReportArtifact`

Then implement `calculations.py` by moving formulas out of prompts:

- mortgage payment and amortization;
- PMI and PITI;
- NOI, cap rate, cash-on-cash, GRM, and DSCR;
- flip and BRRRR returns;
- comparable-sale adjustments;
- weighted property score, grade, and signal.

Write tests before connecting an LLM:

```powershell
pytest tests/test_calculations.py -q
```

Checkpoint: all calculations pass without Azure, an LLM, or network access.

## 8. Adapt PDF generation

Move the reusable functions from `scripts/generate_realestate_pdf.py` into `reports.py` without changing the visual style. Replace Markdown-directory scanning with an `AnalysisResult` input.

Support:

- `render_json(result)`
- `render_markdown(result)`
- `render_pdf(result, output_path)`

Store generated files under `$HOME/reports/<analysis-id>/` when hosted. Return them through the Foundry session file mechanism.

Test with fixed data:

```powershell
pytest tests/test_calculations.py tests/test_hosted_agent.py -q
```

## 9. Prepare Foundry Skills

Copy the existing skills into `skills-baseline/`. Ensure every file follows the Foundry Agent Skills format:

```markdown
---
name: realestate-comps
description: Analyze comparable property sales and pricing alignment.
---

# Comparable Sales Analysis

...business-editable instructions...
```

Keep these items out of business-editable skill bodies:

- formulas and executable Python;
- credentials and endpoints;
- Pydantic schemas;
- source allowlists and security controls;
- mandatory fair-housing and citation controls.

Set the active Foundry project:

```powershell
azd ai project set "https://<account>.services.ai.azure.com/api/projects/<project>"
```

Upload each skill. Example:

```powershell
azd ai skill create realestate-comps --file .\skills-baseline\realestate-comps\SKILL.md --no-prompt
azd ai skill create realestate-rental --file .\skills-baseline\realestate-rental\SKILL.md --no-prompt
```

Repeat for the remaining command skills, then verify:

```powershell
azd ai skill list -o table
```

## 10. Create the Foundry Toolbox

Create `toolbox.yaml` with the skills and the first available tools:

```yaml
description: Real-estate analysis skills and data tools
skills:
  - name: realestate-analyze
  - name: realestate-comps
  - name: realestate-rental
  - name: realestate-neighborhood
  - name: realestate-invest
  - name: realestate-market
tools:
  - type: web_search
    name: web-search
    description: Search for current cited public information
    require_approval: never
```

Add the other skills after the first end-to-end test. Add the project-owned `realestate-public-data` MCP server when it is deployed.

Create the Toolbox:

```powershell
azd ai toolbox create realestate-data --from-file .\toolbox.yaml --no-prompt
azd ai toolbox show realestate-data --output json
```

Use the unversioned consumer endpoint so promoted skill and Toolbox defaults can be adopted without rebuilding the hosted agent:

```text
https://<account>.services.ai.azure.com/api/projects/<project>/toolboxes/realestate-data/mcp?api-version=v1
```

Store it in the local azd environment:

```powershell
azd env set TOOLBOX_ENDPOINT "<consumer-endpoint>"
```

## 11. Implement the Agent Framework workflow

In `skills.py`:

1. Connect to `TOOLBOX_ENDPOINT` with Foundry credentials.
2. Call MCP `resources/list` to discover skills.
3. Call `resources/read` for the selected command and specialist skills.
4. Validate the skill and retain its resolved version.
5. Cache only for the configured short TTL.

In `agent.py`:

1. Parse and validate the command.
2. Load the relevant Foundry Skills.
3. Collect one shared `EvidenceBundle` through Toolbox tools.
4. Create five specialist agents from one factory.
5. Run them using `ConcurrentBuilder`.
6. Validate each result with Pydantic.
7. Run deterministic calculations and scoring.
8. Use one synthesis agent for narrative text.
9. Render the requested report formats.

In `main.py`, follow the maintained sample pattern:

```python
import asyncio
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import FoundryToolbox, ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(override=False)


async def main() -> None:
    credential = DefaultAzureCredential()
    toolbox = FoundryToolbox(credential)
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=credential,
    )
    agent = build_realestate_agent(client=client, toolbox=toolbox)
    await ResponsesHostServer(agent).run_async()


if __name__ == "__main__":
    asyncio.run(main())
```

Import `build_realestate_agent` from `realestate_agent.agent` in the finished file.

## 12. Configure local execution

Create `.env` from `.env.example`:

```text
FOUNDRY_PROJECT_ENDPOINT=https://<account>.services.ai.azure.com/api/projects/<project>
AZURE_AI_MODEL_DEPLOYMENT_NAME=<deployment-name>
TOOLBOX_ENDPOINT=https://<account>.services.ai.azure.com/api/projects/<project>/toolboxes/realestate-data/mcp?api-version=v1
```

`FOUNDRY_PROJECT_ENDPOINT` is used locally but injected by the platform when hosted. Do not redeclare reserved `FOUNDRY_*` variables in the hosted-agent environment configuration.

Run the service:

```powershell
python .\src\realestate_agent\main.py
```

In another terminal, verify readiness and invoke it:

```powershell
Invoke-WebRequest http://localhost:8088/readiness
azd ai agent invoke --local "Analyze the supplied test property data"
```

Then run all tests:

```powershell
pytest -q
```

Checkpoint: the same fixture returns valid JSON, Markdown, and PDF; specialist failures produce a partial result rather than fabricated data.

## 13. Configure hosted-agent deployment

Base `azure.yaml`, `agent.yaml`, and Dockerfile on the generated sample. Required settings:

- hosted agent kind;
- Responses protocol version from the current sample;
- source entry point `main.py`;
- Linux AMD64 image;
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` and `TOOLBOX_ENDPOINT` as non-reserved configuration;
- initial allocation of 1 vCPU and 2 GiB memory;
- project connections for external API credentials.

Do not add platform-owned variables such as `FOUNDRY_PROJECT_ENDPOINT`, `PORT`, `HOME`, or `APPLICATIONINSIGHTS_CONNECTION_STRING` to `azure.yaml`.

Validate configuration without deploying where the current CLI supports it, then provision and deploy:

```powershell
azd provision
azd deploy
azd ai agent show
```

Wait until the version is `active`, then invoke:

```powershell
azd ai agent invoke "Analyze the supplied test property data"
```

Verify:

- Responses streaming completes;
- the selected model and skill versions appear in the result;
- the PDF is available through the session files API;
- Application Insights contains the workflow trace;
- an idle session can resume with its files restored.

## 14. Enable business-user skill updates

Grant authorized users the minimum suitable Foundry project role. The documented requirement for managing Skills is the **Foundry User** role.

Business update procedure in Foundry Toolkit:

1. Open **Foundry Toolkit** in VS Code.
2. Open the selected project under **My Resources**.
3. Open **Tools**, then the **Skills** tab.
4. Select the skill's **...** menu and choose **Replace**.
5. Upload or edit the revised `SKILL.md` to create an immutable version.
6. Run the evaluation cases against that candidate.
7. Use **Default Version** to promote the approved version.
8. Start a new analysis and verify the returned skill version.
9. Roll back by selecting the previous default version if metrics regress.

An analysis resolves skill versions once at startup and keeps them fixed until it completes. New analyses receive the newly published defaults.

If browser-only Foundry portal editing is mandatory, confirm that the target tenant exposes the Skills authoring experience. Otherwise, use the documented Foundry Toolkit UI or build a small internal editor over the Foundry Skills API.

## 15. Add the free public-data MCP service

Implement this only after the manual-data workflow works. Expose a small MCP server with:

```text
resolve_us_address
get_acs_profile
map_zip_geographies
get_fair_market_rent
get_labor_market
get_mortgage_rate_series
get_house_price_index
get_disaster_history
get_public_schools
get_nearby_amenities
```

Back these tools with the free APIs listed in `MIGRATION_PLAN.md`. Return structured values with source URL, source tier, dates, units, and warnings. Add the MCP endpoint to a new Toolbox version, test that version, then publish it as default.

Do not block the initial release on live listings or nationwide sold comps. Use manual property facts and uploads until a suitable free, community, or licensed source is configured.

## 16. Complete feature parity

Add commands in this order:

1. `comps`, `rental`, `neighborhood`, `invest`, and `market` as single-specialist modes.
2. `compare` by running the same analysis pipeline twice.
3. `listing`, using only verified facts.
4. `flip` and `commercial`, reusing deterministic calculations.
5. `screen`, only after a structured property-search source is available.

For each command, add one request fixture, one expected structured result, one failure case, and one report assertion.

## 17. Publish to the personal GitHub profile

Use the repository name:

```text
foundry-realestate-agent
```

Before committing, ensure `.gitignore` contains at least:

```gitignore
.venv/
.env
.azure/
__pycache__/
.pytest_cache/
*.pyc
PROPERTY-*.md
PROPERTY-*.pdf
```

Review the working tree and configured remotes:

```powershell
git status --short
git remote -v
```

If the original repository is configured as `origin`, preserve it as `upstream`:

```powershell
git remote rename origin upstream
```

Commit the converted project:

```powershell
git add .
git commit -m "Build Microsoft Foundry real estate agent"
```

Create a private personal repository and push it:

```powershell
gh repo create tanmoycuat/foundry-realestate-agent --private --source . --remote origin --push
```

Use `--public` instead only after confirming that no proprietary skill content, generated reports, customer addresses, `.env` files, or credentials are committed.

Verify publication:

```powershell
gh repo view tanmoycuat/foundry-realestate-agent --web
```

## 18. Final acceptance checklist

- All deterministic tests pass.
- Local `/readiness` and `/responses` work.
- The deployed Foundry agent version is active.
- At least two configured model deployments pass contract tests.
- The Toolbox exposes expected tools and Skills.
- A business user can publish and roll back a Skill without agent redeployment.
- Each report contains source, freshness, confidence, model, agent, Toolbox, and Skill versions.
- Missing data lowers confidence instead of producing invented values.
- PDF reports are downloadable from the session.
- Application Insights receives traces without credentials or sensitive payloads.
- The GitHub repository is published without secrets or generated customer reports.