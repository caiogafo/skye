# routing

What you learn: routing. Read in this order:

1. `basic_routing.py`: Routing: one alias, one or several models, round-robin balancing
2. `fallbacks_and_health.py`: Fallbacks, retry policies, health, usage and cooldown of a router
3. `skye_config_example.py`: Configure a ModelRouter from a `.skye` file

Run: `python examples/routing/basic_routing.py`

What you see: printed results; with no key a scripted client answers and the example prints which mode ran.

What you need: `pip install skyeai`; a provider key only to call a real service.
Configuration files: `router_config.skye` and `router_config_simple.skye` are `router` blocks in the `.skye` language; `skye_config_example.py` reads the first. Check them with `skye check examples/routing/router_config.skye`. They replace the old YAML files: the library reads no YAML. A target holds `model`, `provider`, `api_key`, `api_base`, `api_version`, `region`, `tpm`, `rpm`, `weight`, `tags`, `metadata`; plus `cost_per_1k_prompt_tokens` / `cost_per_1k_completion_tokens`, which the `cost_based` strategy reads. The old field `priority` is dropped, because the router never read it. Each file starts with front matter (`title`, `description`, `version`, `tags` between two `---` lines), which `build(text).metadata` reads and the router ignores. `retry_after` and `exponential_backoff` of a retry policy are kept in the file, but the router does not apply them yet.
