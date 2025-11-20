# Routes Example Merged

## Summary

Successfully merged `advanced_routing.py` and `routes_usage.py` into a single comprehensive example file: `examples/routes_usage.py`

## Key Changes

### ✅ What Was Done

1. **Merged Two Files Into One**
   - Combined `advanced_routing.py` (7 examples)
   - Combined `routes_usage.py` (8 examples)
   - Created unified `examples/routes_usage.py` with 7 focused examples

2. **Removed All Setters**
   - ❌ No `router.set_fallbacks()`
   - ❌ No `router.set_retry_policy()`
   - ❌ No `router.set_allowed_fails_policy()`
   - ❌ No `router.set_routing_strategy()`
   - ✅ All configuration done in constructor only

3. **Constructor-Based Configuration**
   - All policies configured upfront
   - Clean, declarative approach
   - No dynamic changes after instantiation

4. **Consistent `from nimbus import routes as rt` Pattern**
   - All examples use `rt.ModelRouter`
   - All examples use `rt.ModelTarget`
   - All examples use `rt.RouteConfig`
   - All examples use `rt.RoutingStrategy`
   - All examples use `rt.FallbackConfig`
   - All examples use `rt.RetryPolicyConfig`
   - All examples use `rt.AllowedFailsPolicyConfig`

## Example Structure

### Example 1: Basic Route Configuration
- Single targets per alias
- Simple setup

### Example 2: Multi-Target Routes
- Multiple targets per alias
- Load balancing with weights
- Rate-limit-aware strategy

### Example 3: Complete Router Setup
- All features configured in constructor
- Multiple aliases (gpt-3.5-turbo, gpt-4, claude-3-sonnet)
- Fallback chains
- Retry policies
- Allowed fails policies
- Cooldown configuration

### Example 4: Metrics and Monitoring
- ModelHealthMetrics
- UsageStats
- CooldownInfo
- Usage examples

### Example 5: Routing Strategies
- All 8 strategies explained
- When to use each strategy

### Example 6: Alias Management
- is_alias()
- list_aliases()
- get_route()

### Example 7: Tag-Based Routing
- Tag assignment during configuration
- Tag-based routing usage

## Files Changed

- ✅ `examples/routes_usage.py` - Merged and updated
- ❌ `examples/advanced_routing.py` - Deleted (merged into routes_usage.py)

## Usage

```bash
python examples/routes_usage.py
```

Output shows all 7 examples with:
- Configuration details
- Available features
- Usage patterns
- Best practices

## Key Features Demonstrated

1. **Constructor-Only Configuration**
   - No setters used
   - All config upfront
   - Clean and declarative

2. **Multiple Providers**
   - OpenAI
   - Azure
   - Anthropic

3. **Advanced Features**
   - Multi-target load balancing
   - Fallback chains
   - Retry policies
   - Rate limiting
   - Health tracking
   - Tag-based routing

4. **Pydantic Models**
   - ModelHealthMetrics
   - UsageStats
   - CooldownInfo
   - Type-safe responses

## Best Practices Shown

✓ Use `from nimbus import routes as rt` for clean imports
✓ Configure everything in constructor
✓ Use Pydantic models for all configurations
✓ Support multiple providers
✓ Implement comprehensive health tracking
✓ Use environment variables for API keys
✓ Tag models for access control
✓ Set up fallback chains for reliability

All examples are production-ready and follow best practices!
