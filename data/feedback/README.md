# Feedback Format

Example feedback file:
```json
[
  {
    "indicator": "198.51.100.1",
    "band": "P1",
    "decision": "true_positive",
    "comment": "confirmed malicious"
  },
  {
    "indicator": "192.168.1.1",
    "band": "P2", 
    "decision": "false_positive",
    "comment": "internal router"
  }
]
---

## Step 8: Create sample feedback file

**Type this command:**
```bash
cat > data/feedback/2025-10-01.json << 'EOF'
[
  {
    "indicator": "198.51.100.1",
    "band": "P1",
    "decision": "true_positive",
    "comment": "observed in attack simulation"
  }
]
