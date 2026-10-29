---
name: test-impact
description: Analyze impacted test cases after modifying Page Classes using AST Knowledge Graph.
trigger: /test-impact
---

# Workflow: test-impact

Execute impact analysis based on Git source code changes:

```bash
python tools/test_impact.py --git-diff
```

Outputs the exact list of directly and indirectly impacted test cases, enabling targeted re-runs instead of full suite execution.
