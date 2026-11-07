"""Skeletons: small ``.skye`` texts to start from (``skye new router|flow|prompt``).

Each function returns text only (no file is read or written). Every skeleton passes
:func:`skye.base.dsl.check_text` as it is; the lines to edit are marked ``# CHANGE ME``.
Version 2 syntax (``wait``, ``on_event``) is never used.
"""

from __future__ import annotations

import re

#: The templates of each block kind; the first one is the default.
TEMPLATES: dict[str, tuple[str, ...]] = {
    "router": ("shorthand", "full"),
    "flow": ("sequence", "branch", "parallel", "loop", "full"),
    "prompt": ("basic", "chat"),
}

_DEFAULT_NAMES = {"router": "main", "flow": "my_flow", "prompt": "my_prompt"}
_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\- ]*$")

_ROUTER_SHORTHAND = """\
router "__NAME__" {
  # CHANGE ME: the alias, then "provider/model" first (primary) and its fallbacks in order.
  # The key comes from the provider's variable (OPENAI_API_KEY, ANTHROPIC_API_KEY).
  route "fast" = ["openai/gpt-4o-mini", "anthropic/claude-haiku"]
}
"""

_ROUTER_FULL = """\
router "__NAME__" {
  strategy               = "rate_limit_aware"
  cooldown               = "60s"
  enable_pre_call_checks = true

  route "primary" {
    strategy          = "round_robin"
    fallback_on_error = true
    fallback = ["backup"] # CHANGE ME: routes to try, in order, if this one fails

    target {
      model    = "gpt-4o-mini"                   # CHANGE ME
      provider = "openai"                        # CHANGE ME
      api_key  = env.OPENAI_API_KEY              # CHANGE ME: the variable that holds the key
      rpm      = 1000
      tpm      = 100000
      timeout  = "30s"
    }
  }

  route "backup" {
    target {
      model    = "claude-3-5-haiku-latest"       # CHANGE ME
      provider = "anthropic"                     # CHANGE ME
      api_key  = env.ANTHROPIC_API_KEY           # CHANGE ME
    }
  }

  retry_policy "RateLimitError" { max_retries = 3, retry_after = "5s", exponential_backoff = true }
  retry_policy "AuthenticationError" { max_retries = 0 }
  allowed_fails_policy "RateLimitError" { allowed_fails_per_minute = 100 }
}
"""

_FLOW_SEQUENCE = """\
flow "__NAME__" {
  context { url = string } # CHANGE ME: the inputs of the flow, with their types

  step "Fetch" {
    run   = registry.my_fetch_step               # CHANGE ME: a name from the registry you pass
    input = { url = context.url }
    next  = "Summarize"
  }
  step "Summarize" {
    run   = registry.my_summary_step             # CHANGE ME
    input = { text = step.Fetch.output }
    next  = end
  }
}
"""

_FLOW_BRANCH = """\
flow "__NAME__" {
  context { ticket = string, priority = number(0) }   # CHANGE ME

  step "Classify" {
    run   = registry.my_classifier               # CHANGE ME
    input = { text = context.ticket }
    next  = "Route"
  }

  choice "Route" {
    when step.Classify.output.label == "billing" { next = "Billing" } # CHANGE ME
    when step.Classify.output.label == "bug" and context.priority >= 3  { next = "Escalate" }
    else                                                                 { next = "General" }
  }

  step "Billing"  { run = registry.my_billing_step,  next = end }   # CHANGE ME
  step "Escalate" { run = registry.my_escalate_step, next = end }   # CHANGE ME
  step "General"  { run = registry.my_general_step,  next = end }   # CHANGE ME
}
"""

_FLOW_PARALLEL = """\
flow "__NAME__" {
  context { topic = string }                     # CHANGE ME

  parallel "Fan" {
    join            = "all"                      # all | any
    on_branch_error = "cancel"                   # cancel | continue

    step "Web"  { run = registry.my_web_step,  input = { query = context.topic } }   # CHANGE ME
    step "Docs" { run = registry.my_docs_step, input = { topic = context.topic } }   # CHANGE ME

    next     = "Merge"
    on_error = "Failed"
  }

  step "Merge" {
    run   = registry.my_merge_step               # CHANGE ME
    input = { parts = [step.Web.output, step.Docs.output] }
    next  = end
  }
  step "Failed" { run = registry.my_failure_step, next = end }   # CHANGE ME
}
"""

_FLOW_LOOP = """\
flow "__NAME__" {
  context { brief = string, revisions = number(0), quality = number(0) }   # CHANGE ME

  step "Write" {
    run        = registry.my_writer              # CHANGE ME
    input      = { brief = context.brief, round = context.revisions }
    max_visits = 4                               # the bound: a fifth entry is a run error
    next       = "Review"
  }

  step "Review" {
    run   = registry.my_reviewer                 # CHANGE ME
    input = { draft = step.Write.output }
    set quality = step.Review.output.score       # CHANGE ME: what the reviewer returns
    next  = "Decide"
  }

  choice "Decide" {
    when context.quality >= 0.8 { next = end }   # CHANGE ME: when to stop
    when context.revisions >= 3 { next = "GiveUp" }
    else { set revisions = context.revisions + 1
           next = "Write" }
  }

  step "GiveUp" { run = registry.my_escalation_step, next = end }   # CHANGE ME
}
"""

_FLOW_FULL = """\
router "main" {
  route "smart" = ["openai/gpt-4o", "openai/gpt-4o-mini"]   # CHANGE ME
}

flow "__NAME__" {
  context { topic = string, loops = number(0), quality = number(0) }   # CHANGE ME

  step "Plan" {
    run      = registry.my_planner               # CHANGE ME
    input    = { topic = context.topic }
    retry    = { max = 2, after = "1s" }
    next     = "Fan"
    on_error = "Failed"
  }

  parallel "Fan" {
    join            = "all"
    on_branch_error = "continue"
    step "Web" {
      run = registry.my_web_step, input = { query = context.topic }
      timeout = "30s", retry = 3
    } # CHANGE ME
    step "Docs" { run = registry.my_docs_step, input = { topic = context.topic } } # CHANGE ME
    next     = "Write"
    on_error = "Failed"
  }

  step "Write" {
    run        = router.main                     # a model through the router above
    input = { model = "smart", notes = [step.Web.output, step.Docs.output], round = context.loops }
    max_visits = 4
    next       = "Review"
  }

  step "Review" {
    run   = registry.my_reviewer                 # CHANGE ME
    input = { draft = step.Write.output, criteria = ["accuracy", "clarity"] }
    set quality = step.Review.output.score
    next  = "Decide"
  }

  choice "Decide" {
    when context.quality >= 0.8 { next = "Publish" }
    when context.loops >= 3     { next = "Failed" }
    else { set loops = context.loops + 1
           next = "Fan" }
  }

  step "Publish" { run = registry.my_publisher, emit "research.published", next = end } # CHANGE ME
  step "Failed"  { run = registry.my_failure_step, next = end } # CHANGE ME
}
"""

_PROMPT_BASIC = """\
prompt "__NAME__" {
  variables = { text = string, max_words = number(100), style = string("neutral") } # CHANGE ME
  allow_missing = ["style"]                      # variables the caller may leave out

  message "user" {
    text = "Summarize the text in at most {{ max_words }} words."   # CHANGE ME
    when style { text = "Style: {{ style }}." }
    text = "---\\n{{ text }}"
  }
}
"""

_PROMPT_CHAT = """\
prompt "__NAME__" {
  variables = { product = string, question = string, guidelines = list }   # CHANGE ME

  message "system" {
    text = "You are the support agent of {{ product }}. Reply in the user's language."   # CHANGE ME
    when guidelines {
      text = "Please follow these guidelines:"
      each guideline in guidelines { text = "- {{ guideline }}" }
    }
  }
  placeholder "history"                          # the history is inserted here at run time
  message "user" { text = "{{ question }}" }
}
"""

_BODIES: dict[tuple[str, str], str] = {
    ("router", "shorthand"): _ROUTER_SHORTHAND,
    ("router", "full"): _ROUTER_FULL,
    ("flow", "sequence"): _FLOW_SEQUENCE,
    ("flow", "branch"): _FLOW_BRANCH,
    ("flow", "parallel"): _FLOW_PARALLEL,
    ("flow", "loop"): _FLOW_LOOP,
    ("flow", "full"): _FLOW_FULL,
    ("prompt", "basic"): _PROMPT_BASIC,
    ("prompt", "chat"): _PROMPT_CHAT,
}


def skeleton(kind: str, name: str | None = None, template: str | None = None) -> str:
    """A starting ``.skye`` text for a block.

    Args:
        kind: ``"router"``, ``"flow"`` or ``"prompt"``.
        name: The label of the block (a default per kind: ``main``, ``my_flow``, ``my_prompt``).
        template: One of ``TEMPLATES[kind]``; the first one when ``None``.

    Returns:
        The text; it passes ``check_text`` as it is, and ``# CHANGE ME`` marks what to edit.

    Raises:
        ValueError: If the kind, the template or the name is not valid.
    """
    if kind not in TEMPLATES:
        raise ValueError(f'unknown kind "{kind}"; use ' + ", ".join(TEMPLATES))
    chosen = template or TEMPLATES[kind][0]
    if chosen not in TEMPLATES[kind]:
        raise ValueError(
            f'unknown template "{chosen}" for {kind}; use ' + ", ".join(TEMPLATES[kind])
        )
    label = name or _DEFAULT_NAMES[kind]
    if not _NAME.match(label):
        raise ValueError(f'"{label}" is not a valid name; use letters, digits, "_", "-" or "."')
    return _BODIES[(kind, chosen)].replace("__NAME__", label)


def new_router(name: str = "main", template: str = "shorthand") -> str:
    """A ``router`` skeleton (templates: ``shorthand``, ``full``)."""
    return skeleton("router", name, template)


def new_flow(name: str = "my_flow", template: str = "sequence") -> str:
    """A ``flow`` skeleton (templates: ``sequence``, ``branch``,
    ``parallel``, ``loop``, ``full``).
    """
    return skeleton("flow", name, template)


def new_prompt(name: str = "my_prompt", template: str = "basic") -> str:
    """A ``prompt`` skeleton (templates: ``basic``, ``chat``)."""
    return skeleton("prompt", name, template)
