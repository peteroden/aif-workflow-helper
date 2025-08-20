# GenAI Dev Workflow

![LLMOps Workflow](images/llmops-workflow.png)

## Overview

### Inspiration

![GenAIOps](images/GenAIOps.png)

### Dev Workflow

```mermaid
graph TD
  CreateBranch[Create Branch] --> Clone[Clone branch to local]
  Clone --> HydrateProject[Create branch environment from config files in repo with script]
  HydrateProject --> Experiment
  Experiment --> Evaluate{Evaluate the changes}
  Evaluate -->|Implement| Save[Save code and AI Foundry changes to branch with script]
  Evaluate -->|Do Not Implement| DoNotSave[Handle failure case and capture learnings]
  Save --> PR 
  DoNotSave --> PR
  PR[Confirm code quality locally, then Create Pull Request] --> Merge[Merge PR into main branch]
```

Add data to life cycle - including per environment
Eval could be part of PR in Github flow or part of dev branch in git flow
People and process are needed in addition to technology/platform
Tie thread ID back to the evaluation run in the logs with the Thread ID

CD is either manual or automated

## Steps

### Serialize

```sh
aif.sh -r <resource_url> -g agent
```

### Deserialize

```sh
aif.sh -r <resource_url> -p agent
```
