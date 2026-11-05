# check_contract.py
# Check C3: the contract is a JSON Schema with a version, and a saved API response obeys it.
# Course kit, module 22
#
# Run it from your team folder:  python3 check_contract.py
# It reads contract.schema.json and saved/api_response.json. Stdlib only, so it checks the
# parts of JSON Schema a contract here uses: type, required, properties, additionalProperties,
# const, enum, minimum, maximum, pattern and format date-time.

# 0. SETUP ###################################

import json  # for reading both files
import re    # for pattern and date-time
import sys   # for the exit code
from pathlib import Path  # for file paths

TEAM = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SCHEMA = TEAM / "contract.schema.json"
RESPONSE = TEAM / "saved" / "api_response.json"
DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")

# 1. A SMALL VALIDATOR ###################################

def type_ok(value, t):
    if t == "null":
        return value is None
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return {"string": str, "boolean": bool, "object": dict, "array": list}[t] is type(value)

def validate(value, schema, where="response"):
    errors = []
    types = schema.get("type")
    if types is not None:
        types = types if isinstance(types, list) else [types]
        if not any(type_ok(value, t) for t in types):
            return [f"{where}: {json.dumps(value)} is not {' or '.join(types)}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{where}: {json.dumps(value)} is not {json.dumps(schema['const'])}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {json.dumps(value)} is not one of {schema['enum']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{where}: {value} is below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{where}: {value} is above {schema['maximum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{where}: '{value}' does not match {schema['pattern']}")
        if schema.get("format") == "date-time" and not DATE_TIME.match(value):
            errors.append(f"{where}: '{value}' is not a date-time with a zone")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{where}: missing required field '{key}'")
        props = schema.get("properties", {})
        for key, v in value.items():
            if key in props:
                errors += validate(v, props[key], f"{where}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{where}: field '{key}' is not in the contract")
    return errors

# 2. THE CHECK ###################################

problems = []
try:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    response = json.loads(RESPONSE.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as err:
    print(f"FAIL  C3 the response obeys a versioned contract  ({err})")
    sys.exit(1)
if "$schema" not in schema:
    problems.append("contract.schema.json has no $schema line")
# The version is what lets the page and the API say which contract they each obey.
if "const" not in schema.get("properties", {}).get("contract_version", {}):
    problems.append("contract has no contract_version with a fixed value")
problems += validate(response, schema)

print(f"{'PASS' if not problems else 'FAIL'}  C3 the response obeys a versioned contract  ("
      + ("; ".join(problems) if problems else f"version {response.get('contract_version')}, "
         f"{len(schema.get('properties', {}))} fields") + ")")
sys.exit(1 if problems else 0)
