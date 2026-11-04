# Prompts support: annotated requirements

Reading aid for `requirements.md`. It resolves each pointer to the steering criterion in
`.kiro/steering/10-requirements.md` (Requirements 29 to 34) and says what the spec must deliver.
It is an annotation, not a source of truth: if it disagrees with the steering file, the steering file wins.

Steering map: 29 = template registry, 30 = rendering and variables, 31 = few-shot examples,
32 = roles and multimodal content, 33 = output schema, 34 = integration and performance.

| Spec requirement | Steering criteria | What it means in practice |
|---|---|---|
| 1 Core template management | 29.1, 29.2, 29.3 | Register from string or file under name and version. `FileNotFoundError` with the path if the file is missing. Get latest or exact version, `KeyError` if absent. Invalid syntax raises a validation error carrying the engine details. |
| 2 Rendering and variable injection | 30.1 to 30.4 | Render returns `list[SkyeMessage]`. Missing required variable raises `ValueError` naming it, unless allowed-missing. Unused variables are ignored. Defaults merged under provided values; callable defaults are called at render time. |
| 3 Variable management and validation | 30.4, 30.2, 30.5, 29.6, 30.6 | Defaults and allowed-missing list. Variable extraction lists every name. Validation reports without raising. Partial builder returns a new instance with pre-bound variables. |
| 4 Few-shot learning | 31.1 to 31.4 | Store examples, format with the example template. Semantic selector by similarity, random up to max, fixed always the same. No selector: all examples up to a default limit. |
| 5 Multimodal content | 32.4, 32.6, 32.5 | Image URL, base64 and file path accepted and validated. Invalid format raises a validation error listing supported formats. Content-type metadata is preserved in the messages. |
| 6 Message roles | 32.1, 32.2, 32.3 | One System/User/Assistant message per section; default `UserMessage`. Message placeholders insert history. Invalid role raises a validation error. |
| 7 Jinja2 advanced features | 30.8, 30.9, 30.7 | Conditionals, loops, filters, custom filters, whitespace control. **Macros, inheritance, include and assignment are NOT supported (D20)**; composition is by joining parts with a separator (30.7). The user story text in `requirements.md` still says "macros and template composition", which conflicts with 30.9. |
| 8 Output schema | 33.1 to 33.4 | Schema from a dataclass (not Pydantic, D24) or a JSON-schema dict. Output instructions are an empty text without a schema. Invalid schema raises a validation error. |
| 9 Metadata and introspection | 29.5, 29.6, 29.4 | Metadata: required vs optional variables, examples, content types, roles, current settings. Validate checks syntax and variable references. List returns every name and version. |
| 10 Error handling | 30.2, 29.3, 29.1, 32.6, 29.6 | Clear errors: `ValueError`, validation error with engine details, `FileNotFoundError` with path, descriptive format error. Validation never raises. |
| 11 Skye integration | 34.1 to 34.3 | No third-party dependency (stdlib engine, D20, Requirement 13), so no `skyeai[prompts]` library is needed. Standard `SkyeMessage` plus `CapabilityMessage`. `${VAR}` config substitution, library exceptions and logging. |
| 12 Performance and caching | 34.4 to 34.6 | Compile and cache at registration. Cache variable list and formatted examples. Efficient storage for many templates. |

## Points to resolve in `requirements.md`

1. **Jinja2 vs stdlib engine.** The introduction and glossary say Jinja2 and an optional extra
   `skyeai[prompts]`; steering 34.1 and 30.9 say a stdlib engine with no dependency and no macros,
   inheritance or includes. Requirements 7 and 11 are where this shows.
2. **Requirement 8** wording about Pydantic models, if present in the design, conflicts with D24 (dataclass).
3. **Requirement 3** has 30.4 and 30.2 repeated from Requirement 2, and Requirement 10 repeats
   29.x/30.2/32.6; harmless, but traceability counts per criterion will show overlap.

## Coverage

Every steering criterion is referenced at least once except 30.7 is only reached through
Requirement 7. 29.1 to 29.6, 30.1 to 30.9, 31.1 to 31.4, 32.1 to 32.6, 33.1 to 33.4 and 34.1 to 34.6 are all covered.
