# models

What you learn: model utilities. Read in this order:

1. `cohere.py`: Cohere embeddings through `skye.provider("cohere")` (Live)
2. `cost_tracking.py`: Estimating request cost with CostCalculator (Live)
3. `decision_model.py`: The DecisionModel Port (proposed-interface, guarded)
4. `retry_and_errors.py`: Provider errors and the client's own retries (Live)
5. `token_counting.py`: Counting tokens with TokenCounter (Live)

Run: `python examples/models/cohere.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
