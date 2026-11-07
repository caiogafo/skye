# Flows

A flow is steps. A step runs one thing (`run`) and says where to go next with attributes. **Every step has `next`**
(`next = "Name"` or `next = end`); a forgotten `next` is an error, not a silent end.

```skye
flow "triage" {
  context { ticket = string, priority = number(0) }

  step "Classify" {
    run      = registry.classifier
    input    = { text = context.ticket }
    retry    = { max = 2, after = "1s" }
    next     = "Route"
    on_error = "General"
  }

  choice "Route" {
    when step.Classify.output.label == "bug" and context.priority >= 3 { next = "Escalate" }
    else                                                                { next = "General" }
  }

  step "Escalate" { run = registry.oncall_agent, next = end }
  step "General"  { run = registry.support_agent, next = end }
}
```

## The pieces

- `context { name = type(default) }` declares typed fields (`string`, `number`, `bool`, `list`, `map`). A field without a default is required.
- `step "Name" { run, input, next, on_error, on_timeout, timeout, retry, max_visits, foreach, set, emit }`. `run` is `registry.NAME`,
  `flow.NAME` or `router.NAME`. `retry = 3` is short for `retry = { max = 3 }`; the map is `{ max = 3, after = "2s", backoff = true }`
  (`backoff` makes the wait grow after each failure); `timeout` is a duration string.
- A step that fails and has no `on_error` stops the flow and raises the error with the step name.
- `choice "Name" { when EXPR { ... } ... else { ... } }`: the branches are checked in order and **`else` is required**. A branch holds
  `next`, and may hold `set` and `emit`.
- `set field = value` and `emit "event"` run inside a step after it succeeds; `set` only changes declared fields, with the declared type.
- `parallel "Name" { join = "all", on_branch_error = "cancel", step ..., next = ..., on_error = ... }` runs its steps at the same time.
  `join` is `all` or `any`; `on_branch_error` is `cancel` or `continue`. The block has no timeout of its own: put `timeout` on each step.
- `foreach = context.list` runs a step (or a sub-flow) once per element, in parallel; the element is `item`. The result is a list.
- A step with no `run` is allowed if it has `set`, `emit` or `foreach`.

## Loops

A loop is a path that returns to an earlier step. One step in each loop needs `max_visits = N`: the checker rejects a loop without one, and a
run that re-enters a step more often than that stops with an error instead of looping for ever.

```skye
flow "write_and_review" {
  context { brief = string, revisions = number(0), quality = number(0) }

  step "Write" {
    run        = registry.writer
    input      = { brief = context.brief, round = context.revisions }
    max_visits = 4
    next       = "Review"
  }
  step "Review" {
    run   = registry.reviewer
    input = { draft = step.Write.output }
    set quality = step.Review.output.score
    next  = "Decide"
  }
  choice "Decide" {
    when context.quality >= 0.8 { next = end }
    else {
      set revisions = context.revisions + 1
      next = "Write"
    }
  }
}
```

## Composition

Depth comes from running another flow: `run = flow.inner`, also inside a `parallel` and together with `foreach`. A flow cannot contain itself.
A `parallel` cannot hold another `parallel` or a `choice`; move the inner part into its own flow and run it from a branch.

## Waiting for a person or an event

Not available yet: `wait` and `on_event` need persistence and are version 2. When a user asks for an approval step, say so, and offer what
exists today: split the process in two flows (before and after the approval), and let the Python program start the second one when the
approval arrives.
