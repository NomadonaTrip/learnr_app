# Question Selection Strategies

### Strategy Comparison

| Strategy             | Best For              | Complexity   | Coverage Speed |
| -------------------- | --------------------- | ------------ | -------------- |
| Max Information Gain | General use           | O(Q × C)     | Fastest        |
| Max Uncertainty      | Simple implementation | O(C)         | Fast           |
| Prerequisite-First   | Structured domains    | O(Q × C × P) | Moderate       |
| Balanced Coverage    | Initial diagnostics   | O(Q × C)     | Even           |

### Recommended Approach

1. **Initial Diagnostic (first 12-20 questions):** Balanced Coverage
   - Goal: Seed beliefs across all knowledge areas
   - Select questions that cover diverse concepts

2. **Adaptive Quiz (ongoing):** Max Information Gain
   - Goal: Efficiently reduce uncertainty
   - Prioritize questions about uncertain concepts

3. **Gap Remediation (targeted practice):** Prerequisite-First
   - Goal: Build from foundations
   - Ensure prerequisites are solid before advanced concepts

---
