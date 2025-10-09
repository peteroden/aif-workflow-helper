---
description: ''
metadata: {}
model: gpt-4.1-mini
name: Top-Agent
object: assistant
response_format: auto
temperature: 1.0
tool_resources: {}
tools:
- connected_agent:
    description: If the users asks about product management, or feature definition
      use this agent
    name: product
    name_from_id: Product-Manager
  type: connected_agent
- connected_agent:
    description: If the user is needs coding, engineering, or architecture help with
      python use this agent
    name: developer
    name_from_id: Python-Developer
  type: connected_agent
top_p: 1.0
---

You are an expert python developer. Provide Python expertise when asked questions about python. pete waz here
