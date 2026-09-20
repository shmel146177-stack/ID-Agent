# ID-Agent Copilot Instructions

## Project

ID-Agent is a Python/FastAPI application for processing engineering documentation.

Main responsibilities include:

- PDF document analysis
- document classification
- OCR
- engineering document metadata extraction
- project document completeness checks
- hidden works acts and journals
- supporting documents registry
- DOCX and Excel generation
- ZIP project package generation
- AI-assisted document analysis
- knowledge search and source-bound context generation

## Development rules

- Use Python and follow the existing project architecture.
- Do not perform large refactors unless explicitly requested.
- Prefer small, isolated changes.
- Preserve backward compatibility unless the task explicitly requires otherwise.
- Do not rename public API endpoints, models, services, files, or fields without explicit instruction.
- Do not change existing behavior unrelated to the current task.
- Reuse existing project services and utilities before creating new abstractions.

## Testing

- Every behavioral change should have pytest coverage.
- Preserve all existing tests.
- Run focused tests for the changed component first.
- Run the full test suite before considering a task complete.

Preferred commands:

```powershell
python -m pytest tests/<relevant_test_file>.py -q
python -m pytest -q
```

- Do not modify tests merely to make failing implementation pass unless the specification itself has changed.
## FastAPI
- Preserve existing HTTP status code conventions.
- Map domain exceptions to appropriate HTTP responses.
- Keep API validation explicit.
- Avoid breaking existing endpoints or request/response models.
## File handling
For uploaded files:
- prefer streaming writes
- enforce configured file size limits
- prevent accidental overwrite where required
- remove partial files after failed uploads
- close file streams reliably
- validate paths and filenames
## Project data
When updating persisted project JSON data:
- preserve fields that were not explicitly changed
- avoid replacing whole records when a partial update is intended
- keep generated paths portable where applicable
- prefer POSIX-style paths inside manifests and ZIP metadata
## AI features
AI output must not silently replace deterministic engineering logic.
- keep AI results distinguishable from deterministic analysis
- preserve human-review requirements
- avoid inventing engineering facts
- prefer source-grounded context
- keep source references where available
- do not remove deterministic validation in favor of AI output
## Knowledge service
- preserve source-bound context behavior
- preserve result limits
- reject invalid nonpositive limits where existing APIs require this
- avoid duplicate search terms and duplicate results when existing behavior prevents them
## Code style
- follow the style already present in nearby files
- keep functions focused
- use clear names
- avoid unnecessary dependencies
- avoid speculative abstractions
- do not generate placeholder production code
## Workflow
Before proposing a code change:
1. Inspect the relevant existing implementation.
2. Inspect related tests.
3. Make the smallest reasonable change.
4. Add or update focused tests.
5. Run focused tests.
6. Run the full pytest suite.
7. Review the diff before committing.
## Git safety
- Do not run destructive Git commands.
- Do not reset, clean, force-push, rebase, or delete branches unless explicitly requested.
- Do not commit automatically unless explicitly requested.
- Do not modify unrelated files.