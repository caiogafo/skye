# Routers

A router gives one name (an alias) to one or more model targets and says what to do when a call fails.

```skye
router "main" {
  route "fast" = ["openai/gpt-4o-mini", "anthropic/claude-haiku"]   # first = primary, the rest = fallbacks in order

  route "smart" {
    strategy = "rate_limit_aware"
    fallback = ["fast"]                    # if THIS route fails, try these routes in order (there is no global fallback)
    target { model = "gpt-4", provider = "openai", api_key = env.OPENAI_API_KEY, rpm = 1000, tpm = 100000 }
  }

  cooldown = "60s"
  retry_policy "RateLimitError" { max_retries = 3, retry_after = "5s", exponential_backoff = true }
  allowed_fails_policy "RateLimitError" { allowed_fails_per_minute = 100 }
}
```

## Choose the form

- **Shorthand** `route "x" = ["provider/model", ...]` for the common case. The key comes from the provider's standard variable
  (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, ...), and the rest of the list are fallbacks.
- **Full form** (`route "x" { target { ... } }`) when a target needs limits, a region, an API version, tags or metadata. A shorthand
  entry may also be a map: `{ model = "openai/gpt-4o-mini", rpm = 60 }`.
- Targets inside one route are alternatives chosen by the strategy, not fallbacks. `fallback = [...]` is what falls back, and it is per route.

## Fields

- Router: `strategy`, `cooldown`, `enable_pre_call_checks`.
- Route: `strategy`, `fallback_on_error`, `fallback`.
- Strategies: `round_robin`, `rate_limit_aware`, `latency_based`, `weighted`, `cost_based`, `least_busy`, `priority_based`, `simple_shuffle`.
- Target: `model`, `provider`, `api_key`, `api_base`, `api_version`, `region`, `timeout`, `max_retries`, `weight`, `tpm`, `rpm`, `tags`, `metadata`.
- `retry_policy "ErrorType" { max_retries, retry_after, exponential_backoff }` and `allowed_fails_policy "ErrorType" { allowed_fails_per_minute }`.
- A field that used to end in `_seconds` drops the suffix and takes a duration string (`cooldown`, `retry_after`).
- **Read but not applied yet:** `retry_after` and `exponential_backoff` are accepted, and the router does not wait or back off (only `max_retries` works).
  The strategy `cost_based` is accepted and has no implementation yet (it behaves as "first available"). `priority` and `cost_per_1k_*` are not
  target fields (they were never read); do not write them.

## Keys

Never write a key in the file. Use `env.NAME` for an explicit key, or leave it out and let the standard variable of the provider supply it.
There is no YAML: a `.yaml` configuration must be rewritten as `.skye` (or JSON for the library's own configuration).
