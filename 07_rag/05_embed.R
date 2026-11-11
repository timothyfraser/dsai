# 05_embed.R
# Semantic RAG with Embeddings (Ollama embeddings + SQLite)
# Pairs with 05_embed.py
# Tim Fraser

# In this exercise, we're going to look at the first few pages of the Lower Manhattan Recovery Plan after Hurricane Sandy,
# shown in data/lower_manhattan_recovery_plan.txt.
# For more details, see: https://doi.org/10.1016/j.jenvman.2025.127089
# More plans at: https://github.com/timothyfraser/ny_committees/tree/main/text

# We're going to use semantic search RAG to answer questions about the plan.
# Why use semantic search RAG rather than 'naive' RAG (basic keyword search)?
# - can find relevant chunks even if keywords are not present
# Requirements:
# - need to encode the text into vector 'embeddings' (transform them into numbers)
# - need to store the embeddings in a database
# - need to run a similarity search on the embeddings to find the most relevant chunks
# - need to generate a response based on the relevant chunks

# Semantic RAG: embed text with Ollama (granite-embedding:30m), store in SQLite via
# sqlite-vec (vec0), and run KNN search inside the database. Pairs with 05_embed.py.
# Requires sqlite-vec extension; set VEC_EXTENSION_PATH below.

# 0. SETUP ###################################

## 0.1 Load Packages ##########################

# Install R packages
# install.packages(c("DBI", "RSQLite", "dbplyr", "dplyr", "httr2", "jsonlite", "stringr"))
# For the sqlite-vec extension, in a terminal: pip install sqlite-vec
# First time only, in a terminal: ollama pull granite-embedding:30m

# Load packages
library(DBI) # for database functions
library(RSQLite) # for SQLite db connections
library(dbplyr) # for dplyr-style database queries
library(dplyr) # for data wrangling
library(httr2)    # for HTTP requests
library(jsonlite) # for json operations
library(stringr) # for string operations
readRenviron(".env") # Read the .env file

## 0.2 Configuration ##########################

# Path to sqlite-vec extension. For example, mine was:
VEC_EXTENSION_PATH = "C:/Users/tmf77/AppData/Local/Programs/Python/Python312/Lib/site-packages/sqlite_vec/vec0"
# To find the path, in git bash run:
# python -c "import sqlite_vec; print(sqlite_vec.loadable_path())"

DB_PATH = "07_rag/data/embed.db" # path to your new vector embeddings database
if(file.exists(DB_PATH)) { unlink(DB_PATH, force = TRUE) }
DOCUMENT = "07_rag/data/lower_manhattan_recovery_plan.txt" # path to text doc
EMBED_MODEL = "granite-embedding:30m" # local model for embedding text into vectors
VEC_DIM = 384L   # granite-embedding:30m output size
MODEL = "gemini-flash-lite-latest" # cloud model (Google Gemini free tier; for RAG answer step)
# The free tier may use your prompts to improve Google's products, so send only public or made-up data.
EMBED_URL = "http://localhost:11434/api/embed" # local Ollama embeddings endpoint
CLOUD_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

# 1. FUNCTIONS ################################

# We're going to define a few helper functions to help us with the RAG workflow.

# Let's define our own custom agent_run function, using Google Gemini (free tier).
# Expects a Gemini model name
agent_run = function(role, task, model = MODEL){

  # Get API key from environment variable
  GEMINI_API_KEY = Sys.getenv("GEMINI_API_KEY")

  # Check if API key is set
  if (GEMINI_API_KEY == "") { stop("GEMINI_API_KEY not found in .env file. Please set it up first.") }

  # Construct the request body as a list
  body = list(
    model = model,
    messages = list(
      list(role = "system", content = role),
      list(role = "user", content = task)
    )
  )

  # Build and send the POST request; on a busy server (429, 500, 503), retry up to 3 tries
  res = request(CLOUD_URL) %>%
    req_headers("Authorization" = paste0("Bearer ", GEMINI_API_KEY)) %>%
    req_body_json(body, auto_unbox = TRUE) %>%   # Attach the JSON body
    req_retry(max_tries = 3, is_transient = function(r) resp_status(r) %in% c(429, 500, 503)) %>%
    req_perform()             # Execute the request

  # Extract the model's reply
  response = resp_body_json(res)
  output = response$choices[[1]]$message$content
  return(output)

}


# We want to convert a given text sentence into a vector of numbers, called an 'embedding'
# These embeddings are then stored in a database and can be used to numerically search for the most relevant chunks for a given query.
# We'll use Ollama (granite-embedding:30m) to embed the text, on your own computer.
# The /api/embed endpoint takes a list of texts and returns one vector per text, in order.

# Encode the text into a vector of numbers
embed = function(text) {
  res = request(EMBED_URL) %>%
    req_body_json(list(model = EMBED_MODEL, input = list(text)), auto_unbox = TRUE) %>%
    req_perform()
  vec = resp_body_json(res)$embeddings[[1]]
  as.numeric(unlist(vec))   # list -> R numeric
}

# Float32 blob for sqlite-vec (4 bytes per element).
vec_embedding_to_blob = function(vec) {
  writeBin(as.numeric(vec), raw(), size = 4)
}
# JSON string for the MATCH ? placeholder in KNN queries.
vec_embedding_to_json = function(vec) {
  paste0("[", paste(as.numeric(vec), collapse = ","), "]")
}


# Write a function to read in the document into meaningful text chunks.
get_text = function(DOCUMENT){
  # Split the document into chunks
  DOCUMENT %>%
    # Read the document into lines
    readLines(encoding = "UTF-8") %>% 
    # Concatenate the lines into a single string
    paste0(collapse = " ") %>% 
    # Split the document into chunks anytime there is a period
    str_split("\\.") %>% unlist() %>%
    # Trim whitespace
    str_trim() %>%
    # Return only non-empty chunks
    {.[. != ""]}
}

# Embed each chunk and insert into vec_chunks (float32 blob + text).
build_index_from_document = function(conn, chunks) {
  # Given a database connection 'conn' and a vector of text chunks 'chunks',
  # embed each chunk and insert into database table vec_chunks (float32 blob + text).
  n = length(chunks)
  message("Embedding ", n, " chunks with ", EMBED_MODEL, "...")
  for (i in seq_len(n)) {
    # Get the i-th chunk
    text = chunks[[i]]
    # Embed the chunk
    vec = embed(text)
    # Convert the vector to a float32 blob
    blob = vec_embedding_to_blob(vec)
    # Insert the chunk into the database
    dbExecute(conn, "INSERT INTO vec_chunks (id, embedding, text) VALUES (?, ?, ?)",
              params = list(i - 1L, list(blob), text))
  }
  message("Index built.\n")
}


# SEMANTIC SEARCH

# Create a function to perform semantic search on the vector embeddings database,
# using the KNN search algorithm for similarity search with sqlite-vec.
# KNN runs inside the DB: embed query, MATCH in SQL, return top k. Score = 1 - distance (higher = more similar).
search_embed_sql = function(conn, query, k = 3) {
  query_vec = embed(query)
  query_json = vec_embedding_to_json(query_vec)
  out = dbGetQuery(conn,
    "SELECT id, text, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ?",
    params = list(query_json, k))
  if (nrow(out) == 0) return(out)
  out$score = 1 - out$distance
  result = out %>% select(id, score, text)
  result = result %>% as_tibble()
  return(result)
}

# 2. WORKFLOW ################

# Finally, in this section, we'll put it all together and build the index from the document.

# Read in the document into meaningful chunks, where each chunk is a sentence.
chunks = get_text(DOCUMENT)
n = length(chunks)
message("Found ", n, " chunks in the document.")


# Connect and load sqlite-vec from VEC_EXTENSION_PATH.
conn = dbConnect(RSQLite::SQLite(), DB_PATH)

# If you need to start over, disconnect from the database and remove the database file
# dbDisconnect(conn)
# unlink(DB_PATH, force = TRUE)

# Load the SQLite-vec extension, in order to use vector search
dbExecute(conn, sprintf("SELECT load_extension(%s)", dbQuoteString(conn, VEC_EXTENSION_PATH)))

# Create the vec_chunks table
# vec0 virtual table: id, embedding (float32), +text. Cosine distance for similarity search.
dbExecute(conn, sprintf("
  CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    id INTEGER PRIMARY KEY,
    embedding float[%d] distance_metric=cosine,
    +text TEXT
  )
", VEC_DIM))

# Construct the embedding database (takes longer for larger text documents)
n_chunks = dbGetQuery(conn, "SELECT COUNT(*) AS n FROM vec_chunks")$n
if (n_chunks == 0) {
  time = system.time(build_index_from_document(conn, chunks))
  message("Time taken to build index: ", time[["elapsed"]], " seconds\n")
} else {
  message("Using existing embedding index.\n")
}

# Preview the vec_chunks table
conn %>% tbl("vec_chunks")


# Do a test search
test = search_embed_sql(conn, "vulnerability", k = 3)

print("--------------------------------")
print("🔍 TEST SEARCH:")
print("--------------------------------")

print(test)

# Disconnect from the database
dbDisconnect(conn)

# 3. RAG WORKFLOW #############################

# Reconnect to the database
conn = dbConnect(RSQLite::SQLite(), DB_PATH)
# Load the SQLite-vec extension, in order to use vector search
dbExecute(conn, sprintf("SELECT load_extension(%s)", dbQuoteString(conn, VEC_EXTENSION_PATH)))

# A real query from a user!
query = "Does the recovery plan use a community resilience approach to recovery?"
result1 = search_embed_sql(conn, query, k = 3)
context = paste(result1$text, collapse = "\n\n")
context

role = paste(
  "You are a helpful assistant that answers questions about a community recovery plan. ",
  "Answer the question provided by the user, using only the context provided by the user. ",
  "Format your response as markdown with a title and clear bullet points. ",
  "Content will be provided to the assistant in the following format: ",
  "<user original query> | <context from vector database search>"
)

result2 = agent_run(role = role, task = paste0(query, " | ", context), model = MODEL)




# Or, perhaps we rate the truthfulness of a statement..
role = paste(
   "You are an analyst tasked with performing fact-checking using content provided to you. ",
   "System will provide you with a user query and a context from a vector database search. ",
   "Your task is to: ",
   "1) reframe the user query into a TRUE or FALSE statement, then ",
   "2) answer the user query as TRUE or FALSE, then ",
   "3) provide a 1-5 likert scale score for how true it is, ",
   "where 1 = completely false, 2 = somewhat false, 3 = it's complicated, 4 = somewhat true, 5 = completely true ",
   "Return your response as a valid JSON string in this exact format, with no extra ```json or formatting. ",
   "{",
   "  \"query\": \"<user original query>\",",
   " \"reframed_query\": \"<reframed user query as a TRUE or FALSE statement>\",",
   "  \"answer\": \"TRUE\" or \"FALSE\",",
   "  \"score\": 1-5",
   "}"
)

# Execute the query...
result3 = agent_run(role = role, task = paste0(query, " | ", context), model = MODEL)
result3
result3 %>% fromJSON() # parse the JSON string!

# Disconnect from the database
dbDisconnect(conn)
