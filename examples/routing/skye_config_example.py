"""Configure a ModelRouter from a ``.skye`` file.

``router_config.skye`` declares routes, targets, strategies, fallbacks and policies; API keys are
read from the environment (``env.NAME``). ``ModelRouter.from_file`` builds the router, and keyword
arguments override what the file says or add to it (a ``storage`` for the health and the limits, for
instance); an unknown keyword is an error. No request is made.
"""

import os
import re
from pathlib import Path

import skye.store
from skye.router import ModelRouter

path = Path(__file__).parent / "router_config.skye"

# In production the variables are set outside. Here each one that is not set gets a placeholder,
# so the file loads without real keys.
for name in re.findall(r"env\.(\w+)", path.read_text(encoding="utf-8")):
    os.environ.setdefault(name, "your-api-key-here")

router = ModelRouter.from_file(path, name="main")
print(f"Router loaded with {len(router.list_aliases())} aliases:")
for alias in router.list_aliases():
    route = router.aliases[alias]
    strategy = route.strategy or router.strategy  # a route with no strategy uses the router's
    print(f"  {alias}: {strategy.value}, {len(route.targets)} target(s)")

# Keyword arguments override the file.
custom = ModelRouter.from_file(path, name="main", cooldown_seconds=120.0, strategy="least_busy")
print(f"Overridden: strategy {custom.strategy.value}, cooldown {custom.cooldown_seconds}s")

# The state (health, cooldown, limits) lives in the store you pass; in memory when you pass none. In pure
# serverless pass a shared one, for example skye.store.backend("dynamodb", table_name="skye-router").
shared = ModelRouter.from_file(path, name="main", storage=skye.store.backend("memory"))
print(f"Store: {type(shared.storage_backend).__name__}")

# The router can be written back as text: keys stay as env.NAME, never in clear.
print(f"Written back: {len(router.to_skye('main').splitlines())} lines of .skye")
