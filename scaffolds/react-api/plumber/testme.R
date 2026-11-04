# testme.R
#
# Run the API locally on port 5762. Run this script from the plumber folder.
# Then open http://127.0.0.1:5762/health and http://127.0.0.1:5762/__docs__/

library(plumber)
plumb("plumber.R") %>% pr_run(port = 5762)
