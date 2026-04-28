# 07_starwars_agents.R
# Multi-Agent Workflow: Star Wars Characters
# Uses helper functions from 06_agents/functions.R (agent_run)

# 0. SETUP ###################################

## 0.1 Load Packages #################################

library(ollamar)   # for local Ollama chats
library(dplyr)     # for data wrangling (not strictly required, but consistent with other scripts)

## 0.2 Load Functions #################################

source("functions.R")

# 1. CONFIGURATION ###################################

# Select model of interest (same family used elsewhere)
MODEL = "smollm2:135m"

# Raw data describing popular Star Wars characters
raw_data = "
Popular Star Wars characters and key traits:

- Luke Skywalker: Jedi Knight, human, uses a blue lightsaber, aligned with the Rebellion, trained by Obi-Wan and Yoda.
- Darth Vader: Sith Lord, cyborg, uses a red lightsaber, aligned with the Galactic Empire, formerly Anakin Skywalker.
- Princess Leia Organa: Rebel leader, human, diplomat and strategist, twin sister of Luke, strong in the Force.
- Han Solo: Smuggler turned hero, human, captain of the Millennium Falcon, partnered with Chewbacca.
- Yoda: Grand Master of the Jedi Order, small green alien, legendary teacher, speaks in an unusual word order.
- Obi-Wan Kenobi: Jedi Master, human, mentor to Anakin and Luke, known for wisdom and calm.
- R2-D2: Astromech droid, brave and resourceful, communicates in beeps, often saves the heroes at critical moments.
- C-3PO: Protocol droid, fluent in over six million forms of communication, often worried but loyal to his friends.
- Chewbacca: Wookiee warrior, co-pilot of the Millennium Falcon, strong and loyal, communicates in growls and roars.
- Boba Fett: Bounty hunter, Mandalorian armor, known for tracking targets across the galaxy.
"


# 2. AGENT 1 — CHARACTER DATA SUMMARIZER ######################################

# Agent 1: Takes raw data and produces a concise, structured summary
role1 = paste(
  "You are Agent 1. You receive raw text describing popular Star Wars characters.",
  "Your job is to produce a concise, structured summary of this data.",
  "",
  "Requirements:",
  "- Output 6–10 short lines.",
  "- Each line MUST be in the form 'Character: key details'.",
  "- Focus on the most distinctive traits (role, alignment, species, and one notable fact).",
  "- Do NOT add characters that are not mentioned in the input.",
  "- Do NOT explain what you are doing; only output the 'Character: key details' lines.",
  sep = "\n"
)

summary1 = agent_run(
  role  = role1,
  task  = raw_data,
  model = MODEL,
  output = "text"
)


# 3. AGENT 2 — RANDOM CHARACTER PICKER ########################################

# Agent 2: Takes the summary lines and picks a single character at random
role2 = paste(
  "You are Agent 2. You receive summary lines of Star Wars characters in the form",
  "'Character: key details'.",
  "",
  "Your job is to pick ONE character at random from this summary.",
  "",
  "Requirements:",
  "- First, list all distinct character names you see in the summary.",
  "- Then, internally imagine rolling a fair die to choose one of them at random.",
  "- The character you choose must NOT always be the first one in the list.",
  "- Output EXACTLY two lines:",
  "  1) 'Character: <name>'",
  "  2) 'Details: <the corresponding key details from the summary or a short rephrase>'.",
  "- Do NOT explain your reasoning; only output those two lines.",
  sep = "\n"
)

summary2 = agent_run(
  role  = role2,
  task  = summary1,
  model = MODEL,
  output = "text"
)


# 4. AGENT 3 — TEXTUAL VISUAL DESCRIPTION #####################################
#
# Agent 3 now produces ONLY a textual description of how the character looks.
# It takes the chosen character summary from Agent 2 (summary2) as input and
# returns a short visual description suitable for an artist or designer.

role3 <- paste(
  "You are Agent 3. You receive the name and brief details of a Star Wars character.",
  "",
  "Your job is to describe how this character looks so that an artist could draw them.",
  "",
  "Requirements:",
  "- Output 4–7 bullet points.",
  "- Focus on: clothing or armor, main colors, posture/body language, typical",
  "  facial expression, and any iconic items (e.g., lightsaber, blaster, droid body, etc.).",
  "- Base your description ONLY on the character you were given; do not add new lore.",
  "- Do NOT mention that you are an AI or that this is a prompt; just describe the visual.",
  sep = "\n"
)

summary3 <- agent_run(
  role  = role3,
  task  = summary2,
  model = MODEL,
  output = "text"
)


# 5. VIEW RESULTS #############################################################

cat("\n=== Agent 1 Input (Raw Data) ===\n")
cat(raw_data, "\n\n")

cat("=== Agent 1 Output (Character Summary) ===\n")
cat(summary1, "\n\n")

cat("=== Agent 2 Input (Summary from Agent 1) ===\n")
cat(summary1, "\n\n")

cat("=== Agent 2 Output (Random Character Selection) ===\n")
cat(summary2, "\n\n")

cat("=== Agent 3 Output (Visual Description) ===\n")
cat(summary3, "\n\n")

