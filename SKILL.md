
---
name: thinking-pattern-memory
description: Helps Claude recognize, save, and retrieve recurring thinking patterns using my memory MCP server.
---

# Thinking Pattern Memory

Use my memory MCP server to help me recognize and reflect on recurring thinking patterns.

## When to use the tools

- When I explicitly ask you to remember a thinking pattern, use `record_pattern`.
- When I ask about thinking patterns I have previously saved, use `list_patterns`.
- When I describe a possible recurring thinking pattern, ask whether I want to save it.
- Avoid recording duplicate patterns.

## When not to use the tools

- Do not save every thought or conversation.
- Do not record personal information without asking.
- Do not use the memory tool for unrelated questions.

## Example

User: "Remember that I sometimes worry about being judged when speaking in class."

Claude: Use `record_pattern` to save the pattern.

User: "What thinking patterns have I recorded?"

Claude: Use `list_patterns` to retrieve them.
