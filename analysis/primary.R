# The one primary test (pre-registration, section 5): is there a format x fault-class interaction?
# Usage:  Rscript analysis/primary.R <csv with columns exact, format, fault_class, task_id, run_id[, dataset]>  <output csv>
# With a `dataset` column the test is run once per data set (used for the power study).
suppressPackageStartupMessages(library(lme4))

args <- commandArgs(trailingOnly = TRUE)
data <- read.csv(args[1], stringsAsFactors = TRUE)
if (!"dataset" %in% names(data)) data$dataset <- 0

fit_pair <- function(d, with_run) {
  random <- if (with_run) "(1 | task_id) + (1 | run_id)" else "(1 | task_id)"
  ctrl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
  warned <- FALSE
  fit <- function(fixed) withCallingHandlers(
    glmer(as.formula(paste("exact ~", fixed, "+", random)), data = d, family = binomial, control = ctrl),
    warning = function(w) { if (grepl("converge", conditionMessage(w))) warned <<- TRUE; invokeRestart("muffleWarning") })
  full <- fit("format * fault_class")
  reduced <- fit("format + fault_class")
  list(p = anova(reduced, full)[2, "Pr(>Chisq)"], failed = warned)
}

rows <- lapply(split(data, data$dataset), function(d) {
  result <- fit_pair(d, with_run = TRUE); step <- "glmer, task and run intercepts"
  if (result$failed) { result <- fit_pair(d, with_run = FALSE); step <- "glmer, task intercept only" }   # ladder step 1
  # ladder steps 2 and 3 (glmmTMB) are only needed if this still fails; then result$failed stays TRUE and it is reported
  data.frame(dataset = d$dataset[1], p_interaction = result$p, ladder_step = step, still_failed = result$failed)
})
write.csv(do.call(rbind, rows), args[2], row.names = FALSE)
cat("data sets:", length(rows), "\n")
