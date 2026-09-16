# Foundry Real Estate Agent

A Python hosted agent for Microsoft Foundry that combines five specialist analyses with deterministic real-estate calculations.

## Capabilities

- Runs comparable-sales, rental, neighborhood, investment, and market specialists concurrently.
- Calculates mortgage payments and weighted property scores in Python.
- Produces validated JSON, Markdown, and PDF reports.
- Uses source-controlled business instructions from `skills/` during local development.
- Connects to a Foundry Toolbox for external data and tools.
- Exposes the Foundry Responses protocol on port `8088`.

## Project Structure

```text
src/realestate_agent/   Application code
skills/                 Local business-instruction baselines
tests/                  Unit and workflow tests
agent.yaml              Hosted-agent definition
azure.yaml              Azure Developer CLI configuration
toolbox.yaml             Toolbox definition
Dockerfile              Container image
```

## Local Setup

Requirements:

- Python 3.11 or newer
- Azure credentials available to `DefaultAzureCredential`
- Access to a Microsoft Foundry project and model deployment

Create an environment and install the project:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set these values in `.env`:

```text
FOUNDRY_PROJECT_ENDPOINT=https://your-account.services.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=your-model-deployment
TOOLBOX_ENDPOINT=https://your-account.services.ai.azure.com/api/projects/your-project/toolboxes/realestate-data/mcp?api-version=v1
```

`TOOLBOX_ENDPOINT` is optional when no external Toolbox is configured.

Start the agent:

```powershell
python .\src\realestate_agent\main.py
```

The service listens on `http://localhost:8088`.

## Tests

```powershell
pytest -q
```

## Deploy

Install Azure Developer CLI 1.27.1 or newer and the Microsoft Foundry extension, then authenticate and deploy:

```powershell
azd extension install microsoft.foundry
azd auth login
azd provision
azd deploy
```

## Configuration

| Variable | Required | Purpose |
|---|---:|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Yes | Foundry project endpoint used by the local host |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Yes | Model deployment used by specialist agents |
| `TOOLBOX_ENDPOINT` | No | MCP endpoint for the project Toolbox |
| `TOOLBOX_NAME` | No | Toolbox name; defaults to `realestate-data` |
| `DEFAULT_MODEL_PROFILE` | No | Logical model profile recorded in results |
| `SKILL_CACHE_TTL_SECONDS` | No | Skill cache lifetime; defaults to 60 seconds |

## Disclaimer

This project provides educational and research output only. It is not an appraisal, inspection, legal opinion, or financial or investment advice. Verify property data and decisions with qualified professionals.
