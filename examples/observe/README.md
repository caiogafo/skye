# observe

What you learn: telemetry. Read in this order:

1. `custom_exporter.py`: Custom exporter: implement the observe event-handler Port as an exporter (Live, Port-level)
2. `telemetry.py`: Telemetry: implement the observe Port and collect events, metrics and traces (Live, Port-level)

Run: `python examples/observe/custom_exporter.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
