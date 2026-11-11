"""Schema registry and validation (jsonschema draft 2020-12 with local $ref resolution)."""
import json
from .core import PIPELINE_DIR, STUDIO_DIR, load_json

SCHEMA_DIR = PIPELINE_DIR / "schemas"
REGISTRY = {
    "cas/asset-set/0.5": "asset-set.schema.json",
    "cas/anchor-set/0.5": "anchor-set.schema.json",
    "cas/manifest/0.5": "manifest.schema.json",
    "cas/production-brief/0.5": "production-brief.schema.json",
    "cas/qa-report/0.5": "qa-report.schema.json",
    "motion-reference/1.0": "motion-reference.schema.json",
}
BODY_SPEC_SCHEMA = STUDIO_DIR / "docs" / "BASE_BODY_SPEC.schema.json"


def detect(doc):
    """Return (schemaId, schemaPath) for a document, or (None, None)."""
    sid = doc.get("schema") if isinstance(doc, dict) else None
    if sid in REGISTRY:
        return sid, SCHEMA_DIR / REGISTRY[sid]
    if isinstance(doc, dict) and doc.get("schemaVersion") == "2.0" and "landmarks" in doc:
        return "BASE_BODY_SPEC/2.0", BODY_SPEC_SCHEMA
    if isinstance(doc, dict) and doc.get("schemaVersion") == "1.0" and "landmarks" in doc:
        return "BASE_BODY_SPEC/1.0-legacy", SCHEMA_DIR / "base-body-spec-1.0-legacy.schema.json"
    return None, None


def _registry():
    from referencing import Registry, Resource
    res = []
    for f in SCHEMA_DIR.glob("*.schema.json"):
        s = load_json(f)
        r = Resource.from_contents(s)
        res.append((s["$id"], r))
        res.append((f.name, r))
    return Registry().with_resources(res)


def validate(doc):
    """Returns dict {result, schema, errors[]}. BLOCKED if the schema is unknown or jsonschema is unavailable."""
    sid, path = detect(doc)
    if not sid:
        return {"result": "BLOCKED", "schema": None, "errors": ["unknown document type (no recognised 'schema' / 'schemaVersion')"]}
    try:
        import jsonschema
    except ImportError:
        return {"result": "BLOCKED", "schema": sid, "errors": ["python package 'jsonschema' is not installed"]}
    schema = load_json(path)
    try:
        v = jsonschema.Draft202012Validator(schema, registry=_registry())
    except Exception:  # older jsonschema without referencing
        v = jsonschema.Draft202012Validator(schema)
    errs = sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path))
    return {"result": "FAIL" if errs else "PASS", "schema": sid,
            "errors": [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}" for e in errs][:50]}


def validate_file(path):
    with open(path, encoding="utf-8") as f:
        try:
            doc = json.load(f)
        except json.JSONDecodeError as e:
            return {"result": "FAIL", "schema": None, "errors": [f"invalid JSON: {e}"]}
    return validate(doc)
