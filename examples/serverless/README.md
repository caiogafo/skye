# serverless

What you learn: serverless use. Read in this order:

1. `lambda_handler.py`: A serverless handler: create the client once, outside the handler, so a warm invocation pays nothing
2. `serverless_router_example.py`: A router whose state survives between invocations of a serverless function

Run: `python examples/serverless/lambda_handler.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
