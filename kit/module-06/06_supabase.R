#' @name 06_supabase.R
#' @title Put the cleaned inventory in Postgres on Supabase, behind a row-level security policy
#' @description
#' Pairs with 06_supabase.py
#' Course kit, module 6
#'
#' Topic: Postgres on Supabase
#'
#' This script takes the cleaned table that repair_table.py stored in SQLite and puts it in a
#' hosted Postgres database on Supabase. It writes the SQL that creates the table and its one
#' access rule, inserts the 30 rows with the secret key, then reads the table twice: once with
#' the secret key and once with the publishable key a web page would use. It talks to
#' Supabase's web API (the REST endpoint at /rest/v1) directly with httr2.
#'
#' If you haven't already, install these packages...
#' install.packages(c("DBI", "RSQLite", "httr2", "jsonlite"))
#'
#' Run it from the folder that holds this file, after the repair:
#'   LLM_STUB=1 python3 repair_table.py
#'   Rscript 06_supabase.R
#'
#' It reads three settings from the environment, never from this file:
#'   SUPABASE_URL   your project's address, from the project's Connect dialog
#'   SUPABASE_KEY   the project's SECRET key (sb_secret_...). Server-side only.
#'   SUPABASE_PUBLISHABLE_KEY  optional: the publishable key (sb_publishable_...), for section 4
#' No project yet? Leave SUPABASE_URL and SUPABASE_KEY unset and the script runs in STUB mode:
#' it prints the SQL and every request it would make, sends nothing, and exits 0.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

library(DBI) # for talking to databases
library(RSQLite) # for reading the cleaned table repair_table.py wrote
library(httr2) # for HTTP requests to Supabase
library(jsonlite) # for turning rows into JSON

## 0.2 Configuration #################################

# Work inside the module-06 folder, so data/ and output/ resolve: the script's own folder,
# the folder you are in, or module-06/ under it, whichever holds data/inventory_raw.csv.
script_arg = grep("^--file=", commandArgs(FALSE), value = TRUE)
here = if (length(script_arg) == 1) dirname(normalizePath(sub("^--file=", "", script_arg))) else getwd()
for (dir in c(here, getwd(), "module-06")) {
  if (file.exists(file.path(dir, "data", "inventory_raw.csv"))) { setwd(dir); break }
}

DB_PATH = file.path("output", "inventory.db")
SQL_PATH = file.path("output", "06_inventory.sql")
TABLE = "inventory"

SUPABASE_URL = Sys.getenv("SUPABASE_URL")
SUPABASE_KEY = Sys.getenv("SUPABASE_KEY")
SUPABASE_PUBLISHABLE_KEY = Sys.getenv("SUPABASE_PUBLISHABLE_KEY")

# No address or no key means STUB mode: say so loudly, and send nothing.
STUB = SUPABASE_URL == "" || SUPABASE_KEY == ""
if (STUB) {
  cat(strrep("=", 60), "\n")
  cat("STUB MODE: SUPABASE_URL and SUPABASE_KEY are not set.\n")
  cat("Nothing is sent to Supabase. This prints what the script would do.\n")
  cat(strrep("=", 60), "\n")
}

# The secret key skips every access rule, so it must never sit in a page.
# Anything named VITE_ is printed into the page's public JavaScript; a secret key never may be.
if (startsWith(SUPABASE_KEY, "sb_publishable_")) {
  stop("SUPABASE_KEY holds a publishable key. Section 3 writes rows, so it needs the secret key.")
}

# Every request carries the key on the apikey header only. Supabase's docs say to "Send
# publishable and secret keys on the apikey header only": these keys are not JWTs, so
# Supabase rejects them as a Bearer token on the Authorization header.
supabase_request = function(path, key){
  request(paste0(SUPABASE_URL, path)) %>%
    req_headers("apikey" = key)
}

# 1. WRITE THE TABLE AND ITS POLICY AS SQL ###################################

# The same rules as the SQLite table in repair_table.py, now enforced by Postgres.
# The web API cannot create tables, so you run this once in the project's SQL editor.
SQL = "create table if not exists public.inventory (
  row_id integer primary key,
  sku text not null,
  qty_on_hand integer check (qty_on_hand is null or qty_on_hand > 0),
  last_restock date,
  category text check (category is null or category in ('Electronics', 'Food'))
);

-- New tables may get no grants by default (Supabase is making access opt-in), so grant it here.
-- Grants decide which roles reach the table at all; the policy below decides which rows.
grant select, insert, update on public.inventory to service_role;
grant select on public.inventory to anon;

-- Row-level security: with it on, a key that does not skip the rules sees no rows
-- and may write none, until a policy allows something.
alter table public.inventory enable row level security;

-- One policy: the public page may read rows whose count is known. No policy allows writes.
create policy \"page reads counted rows\"
  on public.inventory for select
  to anon
  using (qty_on_hand is not null);
"

dir.create("output", showWarnings = FALSE)
writeLines(SQL, SQL_PATH)
cat("Wrote 06_inventory.sql. Paste it into the SQL editor of your Supabase project once.\n")

# 2. LOAD THE CLEANED ROWS ###################################

if (!file.exists(DB_PATH)) {
  stop("No output/inventory.db yet. Run  LLM_STUB=1 python3 repair_table.py  first.")
}

con = dbConnect(SQLite(), DB_PATH)
rows = dbGetQuery(con, "SELECT * FROM inventory ORDER BY row_id")
dbDisconnect(con)
cat("Loaded", nrow(rows), "cleaned rows from inventory.db.\n")
counted = sum(!is.na(rows$qty_on_hand))

# 3. INSERT WITH THE SECRET KEY ###################################

# Upsert, not insert: run the script twice and you still have 30 rows, not 60.
if (STUB) {
  cat("STUB: would POST", nrow(rows), "rows to /rest/v1/inventory with the secret key,\n")
  cat("      Prefer: resolution=merge-duplicates, so a second run changes nothing.\n")
  cat("STUB: first row would be row_id ", rows$row_id[1], ", sku ", rows$sku[1], ", qty_on_hand ",
      rows$qty_on_hand[1], ", category ", rows$category[1], "\n", sep = "")
} else {
  supabase_request(paste0("/rest/v1/", TABLE), SUPABASE_KEY) %>%
    req_headers(Prefer = "resolution=merge-duplicates,return=minimal") %>%
    req_body_raw(toJSON(rows, na = "null"), type = "application/json") %>%
    req_perform()
  cat("Upserted", nrow(rows), "rows into inventory with the secret key.\n")
}

# 4. READ WITH EACH KEY ###################################

# The secret key skips row-level security, so it sees every row.
# The publishable key is the one a page may hold, so it sees only what the policy allows.
read_rows = function(key){
  supabase_request(paste0("/rest/v1/", TABLE, "?select=row_id"), key) %>%
    req_perform() %>%
    resp_body_json()
}

if (STUB) {
  cat("STUB: a read with the secret key would return", nrow(rows), "rows (it skips the policy).\n")
  cat("STUB: a read with the publishable key would return", counted, "rows (rows with a count).\n")
  cat("STUB: a write with the publishable key would be refused: no policy allows it.\n")
} else {
  cat("Secret key reads", length(read_rows(SUPABASE_KEY)), "rows.\n")
  if (SUPABASE_PUBLISHABLE_KEY == "") {
    cat("SKIP: set SUPABASE_PUBLISHABLE_KEY to compare the read a page would make.\n")
  } else {
    seen = read_rows(SUPABASE_PUBLISHABLE_KEY)
    cat("Publishable key reads", length(seen), "rows. The policy expects", counted, ".\n")
    # A refused write comes back as an HTTP error, so we look at the status instead of stopping.
    resp = supabase_request(paste0("/rest/v1/", TABLE), SUPABASE_PUBLISHABLE_KEY) %>%
      req_body_raw('{"row_id": 999, "sku": "TEST"}', type = "application/json") %>%
      req_error(is_error = function(resp) FALSE) %>%
      req_perform()
    if (resp_status(resp) < 300) {
      cat("WARNING: the publishable key could write a row. Check the policies.\n")
    } else {
      cat("Publishable key write refused, as it should be: HTTP", resp_status(resp), "\n")
    }
  }
}
