#' @name 02_speak.R
#' @title Text-to-Speech (TTS): turn text into a spoken .wav file, on your own laptop
#' @description
#' Course kit, module 18
#' Topic: Text-to-Speech
#'
#' This script speaks a sentence with Piper, a small local TTS engine that runs
#' well on a laptop processor. Nothing leaves your computer.
#' Piper is a command-line program, so R runs it with system2(), the same way you would in a terminal.
#' The last section shows the same job done by a cloud API, for comparison.

# If you haven't already, install Piper and download one voice (in a terminal)...
# pip install piper-tts
# python3 -m piper.download_voices en_US-lessac-medium
# A voice is two files: en_US-lessac-medium.onnx (the model) and a matching .onnx.json (its settings).
# Each voice has a model card that says how you may use it. Read it before you publish audio.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

library(httr2) # for HTTP requests (the cloud option)
library(tuneR) # for playing the audio back

## 0.2 Settings ###################################

# The voice to use. Piper looks for <voice>.onnx in the folder you run from, or in --data-dir.
PIPER_VOICE = Sys.getenv("PIPER_VOICE", "en_US-lessac-medium")
OUTPUT_PATH = Sys.getenv("SPEAK_OUTPUT", "speak_test.wav")
# The Python that has piper-tts installed.
PYTHON = Sys.getenv("PYTHON", "python3")


# 1. SPEAK LOCALLY #####################################

speak = function(text, output_path = OUTPUT_PATH, voice = PIPER_VOICE) {

  # Testing values
  # text = "Pump three is leaking oil."
  # output_path = "speak_test.wav"
  # voice = "en_US-lessac-medium"

  # We run Piper as a command, exactly as you would type it in a terminal:
  # python3 -m piper -m <voice> -f <output.wav> -- "<text>"
  args = c("-m", "piper", "-m", voice, "-f", output_path, "--", shQuote(text))
  status = system2(PYTHON, args = args)

  # If Piper failed, stop with a clear message instead of a missing file later.
  if (status != 0 || !file.exists(output_path)) { stop("piper failed. Run the command above in a terminal to see its error.") }
  return(output_path)
}


# 2. EXAMPLE: A FIELD REPORT, SPOKEN #################################

TEXT = "Pump three at the north lift station is leaking oil. Priority high."

time = system.time({
  path = speak(TEXT)
})
cat("\nTime taken: ", round(time[3], 2), " seconds\n")
cat("Wrote: ", path, " (", file.info(path)$size, " bytes)\n")

# Play (in windows, this triggers windows media player)
path |> readWave() |> play()

# Listen for: numbers ("three" vs "3"), short codes (try "P-3"), and names.
# TTS reads what you write, so write numbers and codes the way you want them said.


# 3. THE SAME JOB IN THE CLOUD (OPTIONAL) #################################

# Cloud voices sound more natural and handle odd words better,
# but your text leaves your computer, and every character costs a little money.
# Needs OPENAI_API_KEY in .env. Uncomment to try.

# readRenviron(".env")
# OPENAI_API_KEY = Sys.getenv("OPENAI_API_KEY")
# resp = request("https://api.openai.com/v1/audio/speech") |>
#   req_headers("Authorization" = paste0("Bearer ", OPENAI_API_KEY)) |>
#   req_body_json(list(model = "gpt-4o-mini-tts", voice = "alloy", input = TEXT, response_format = "wav"), auto_unbox = TRUE) |>
#   req_perform() # model and voice names change over time
# writeBin(resp_body_raw(resp), "speak_cloud.wav")
