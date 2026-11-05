# Reporter decision: team example

## Shipped

prompt_B on the local model

## Alternatives

- prompt_A on the local model
- prompt_B on the cloud model

## Reason

Our data comes from a public API, so privacy does not bind us: nothing in the prompt is private, and the local model keeps it on our machine anyway. Cost decides between local and cloud: the local model is free per call and the cloud model bills per token, so the 10 repeat runs and every later rerun cost nothing. Latency is slower on a laptop, which we accept for a nightly report. Quality is the price: the cloud model may have a higher ceiling, but our eval shows the local model already agrees with itself on Top item in 8 of 10 runs (rate 0.8), and the Welch test says the two prompts differ (p-value 0.034), so the prompt matters more than the model for this report. We ship prompt_B.

## Evidence

- eval/agreement.csv: Top item 0.8 and Count 0.7 agreement across 10 runs
- eval/comparison.txt: Welch two-sample t-test, prompt_A against prompt_B, t = 2.31, p-value = 0.034
- Ground truth: our plain-code count matched the model's Count in 7 of the 10 runs

## Blind spots

The eval measures repeatability and one ground-truth field. It does not measure whether the report is useful to a manager, whether the tone fits, or how the model behaves on data unlike the 10 runs we saved. We did not run the cloud model, so we cannot say how much better it is.

## Key

- No key is used by the shipped setup: the model runs on our own machine
- Holder if we move to the cloud: Priya, in her own .env file, which is ignored by git
