# Example Trace: Error Recovery

## Scenario
[Description: A tool call fails due to a temporary error or missing parameter, triggering the escalation protocol.]

## Trace
**User**: [Original Request]

**Thought**:
<thinking>
The user wants [Goal]. I will call [Tool A] to retrieve necessary data.
</thinking>

**Action**: `tool_a(param="value")`
**Result**: `ERROR: 403 - Permission Denied or Resource Unavailable`

**Thought**:
<thinking>
[Tool A] failed with a 403 error. According to the **Escalation Protocol** in `SKILL.md`, I must check if [Tool B] is an authorized alternative or ask the user for specific credentials. I will try [Tool B] first as it is listed in the dependencies.
</thinking>

**Action**: `tool_b(param="fallback_value")`
**Result**: `SUCCESS: [Data retrieved]`

**Thought**:
<thinking>
[Tool B] succeeded. I can now complete the task by generating the artifact.
</thinking>

**Response**: [Final Outcome with a brief note on the recovery action taken]
