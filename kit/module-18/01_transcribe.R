#' @name 01_transcribe.R
#' @title Speech-to-Text (STT): turn a recording into text, on your own laptop
#' @description
#' Course kit, module 18
#' Topic: Speech-to-Text
#'
#' This script transcribes a .wav file with faster-whisper, a fast local version
#' of OpenAI's open Whisper model. Nothing leaves your computer.
#' faster-whisper is a Python library, so R calls it through reticulate.
#' The last section shows the same job done by a cloud API, for comparison.

# If you haven't already, install these packages...
# install.packages(c("reticulate", "httr2", "jsonlite"))
# reticulate::py_install(c("faster-whisper", "av<19"))  # av 19 breaks faster-whisper 1.2.1
# The first run downloads the model (about 150 MB for "base.en"). After that it works offline.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

library(reticulate) # for calling a Python library from R
library(httr2) # for HTTP requests (the cloud option)

## 0.2 Settings ###################################

# Run this script from the top of the course repo, so the audio path resolves.
AUDIO_PATH = Sys.getenv("AUDIO_PATH", "06_agents/06_jfk.wav")

# Whisper comes in sizes: tiny, base, small, medium, large.
# Bigger is more accurate and slower. ".en" models only know English, and are a bit better at it.
# Start with "base.en" on a laptop; try "tiny.en" if it feels slow.
WHISPER_MODEL = Sys.getenv("WHISPER_MODEL", "base.en")


# 1. TRANSCRIBE LOCALLY #####################################

transcribe = function(audio_path, model_size = WHISPER_MODEL) {

  # Testing values
  # audio_path = "06_agents/06_jfk.wav"
  # model_size = "base.en"

  if (!file.exists(audio_path)) { stop(paste0("Audio file not found: ", audio_path)) }

  # Import the Python library (it must be installed in reticulate's Python).
  fw = import("faster_whisper")

  # device = "cpu" and compute_type = "int8" are the settings for a laptop with no graphics card.
  # int8 stores the model's numbers in a smaller format: faster, almost as accurate.
  model = fw$WhisperModel(model_size, device = "cpu", compute_type = "int8")

  # Whisper cuts the audio into segments (stretches of speech) and transcribes each one.
  result = model$transcribe(audio_path, beam_size = 5L)

  # result[[1]] is a Python generator of segments; iterate() turns it into an R list.
  segments = iterate(result[[1]])

  # Join the segments back into one string.
  text = paste(trimws(sapply(segments, function(s) s$text)), collapse = " ")
  return(text)
}


# 2. EXAMPLE: JOHN F KENNEDY SPEECH CLIP #################################

# Same clip as 06_agents/06_alms_cloud.R, Example 3.
time = system.time({
  transcript = transcribe(AUDIO_PATH)
})
cat("\nTime taken: ", round(time[3], 2), " seconds\n")
cat("\nTranscript:\n")
transcript

# Compare with the ALM in 06_alms_cloud.R:
# The ALM was asked to transcribe; Whisper can do nothing BUT transcribe.
# A narrow model is often the more predictable tool for a narrow job.


# 3. THE SAME JOB IN THE CLOUD (OPTIONAL) #################################

# A cloud STT model is usually more accurate on hard audio (noise, accents, jargon),
# but your recording leaves your computer, and every minute costs a little money.
# Needs OPENAI_API_KEY in .env. Uncomment to try.

# readRenviron(".env")
# OPENAI_API_KEY = Sys.getenv("OPENAI_API_KEY")
# resp = request("https://api.openai.com/v1/audio/transcriptions") |>
#   req_headers("Authorization" = paste0("Bearer ", OPENAI_API_KEY)) |>
#   req_body_multipart(
#     file = curl::form_file(AUDIO_PATH),
#     model = "gpt-4o-mini-transcribe" # model names change over time
#   ) |>
#   req_perform()
# resp_body_json(resp)$text
