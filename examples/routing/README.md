# routing

What you learn: routing. Read in this order:

1. `basic_routing.py`: Routing: one alias, one or several models, round-robin balancing
2. `fallbacks_and_health.py`: Fallbacks, retry policies, health, usage and cooldown of a router
3. `yaml_config_example.py`: Example: Using YAML Configuration for ModelRouter

Run: `python examples/routing/basic_routing.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
Configuration files: `router_config.yaml` and `router_config_simple.yaml` are read by `yaml_config_example.py`; reading YAML needs `pip install skyeai[yaml]`.
