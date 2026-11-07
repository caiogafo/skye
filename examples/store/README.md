# store

What you learn: a storage backend. Read in this order:

1. `backends.py`: Durable-state backends behind the StorageBackend Port (Live)
2. `custom_backend.py`: Your own durable-state backend behind the StorageBackend Port (Live)

Run: `python examples/store/backends.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
