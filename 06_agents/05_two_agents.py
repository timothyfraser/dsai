#!/usr/bin/env python
# 05_two_agents.py
# Two-agent workflow using functions.agent_run
# Agent 1: Takes raw data and produces a summary
# Agent 2: Takes the summary and produces a formatted output (data table)

from functions import agent_run

# 1. CONFIGURATION ###################################

MODEL = "smollm2:135m"

# 2. RAW DATA ###################################

raw_data = """
Daily service tickets for the last week:
- Monday: 42 tickets (15 high priority, 10 medium, 17 low)
- Tuesday: 35 tickets (8 high, 12 medium, 15 low)
- Wednesday: 55 tickets (20 high, 18 medium, 17 low)
- Thursday: 30 tickets (5 high, 10 medium, 15 low)
- Friday: 60 tickets (25 high, 20 medium, 15 low)

Average resolution times:
- High priority: 2.5 hours
- Medium priority: 5.0 hours
- Low priority: 8.0 hours

Additional notes:
- Two major outages on Wednesday and Friday.
- Customers reported longer wait times on Friday afternoon.
"""

# 3. TASK 1 — Agent 1: Summarizer ###################################
# Takes raw data and produces a structured summary

role1 = (
    "You are Agent 1. You receive raw operational data and produce a concise, "
    "structured summary that is easy for another agent to turn into a table.\n"
    "- Focus on ticket volume trends, spikes/drops, average resolution times, "
    "and notable incidents (outages, long waits).\n"
    "- Output 4–8 short lines.\n"
    "- Each line MUST be in the form 'Aspect: detail'. For example:\n"
    "  'Ticket volume trend: peaked on Wednesday and Friday',\n"
    "  'Average resolution (high priority): 2.5 hours'.\n"
    "- Do NOT reprint the raw data; only output these 'Aspect: detail' lines."
)

summary = agent_run(
    role=role1,
    task=raw_data,
    model=MODEL,
    output="text",
)

# 4. TASK 2 — Agent 2: Table Formatter ###################################
# Takes the summary and produces a markdown data table

role2 = (
    "You are Agent 2. You receive a summary written by Agent 1 consisting of lines "
    "in the form 'Aspect: detail'.\n"
    "- Keep the original meaning of each line.\n"
    "- Produce ONLY a markdown table, with no extra prose.\n"
    "- The table must have two columns: 'Aspect' and 'Detail'.\n"
    "- Each line from the summary should become one row in the table.\n"
    "- Do not invent new aspects; just reorganize what you are given."
)

formatted_table = agent_run(
    role=role2,
    task=summary,
    model=MODEL,
    output="text",
)

# 5. VIEW RESULTS ###################################

#print("=== Agent 1 Input (Raw Data) ===")
#print(raw_data.strip())
#print()

print("=== Agent 1 Output (Summary) ===")
print(summary.strip())
print()

#print("=== Agent 2 Input (Summary from Agent 1) ===")
# print(summary.strip())
#print()

print("=== Agent 2 Output (Formatted Table) ===")
print(formatted_table.strip())
print()

