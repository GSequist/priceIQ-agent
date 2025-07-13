from typing import Any, Dict, get_type_hints, get_origin, get_args
from pydantic import create_model, Field
import inspect
import json


def ensure_strict_json_schema(schema):
    """transform schema constructs OAI API"""
    if not isinstance(schema, dict):
        return schema
    if "anyOf" in schema:
        anyof_schemas = schema["anyOf"]
        if len(anyof_schemas) == 2 and any(
            s.get("type") == "null" for s in anyof_schemas
        ):
            non_null = next((s for s in anyof_schemas if s.get("type") != "null"), None)
            if non_null:
                result = {k: v for k, v in schema.items() if k != "anyOf"}
                result.update(non_null)
                result["nullable"] = True
                return result
    for key, value in list(schema.items()):
        if isinstance(value, dict):
            schema[key] = ensure_strict_json_schema(value)
        elif isinstance(value, list):
            schema[key] = [
                ensure_strict_json_schema(i) if isinstance(i, dict) else i
                for i in value
            ]
    return schema


def function_to_schema(func: callable) -> Dict[str, Any]:
    """Convert a function to an OpenAI-compatible function schema."""
    func_name = func.__name__
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    doc_parts = doc.split("#parameters:")
    main_description = doc_parts[0].strip()
    try:
        type_hints = get_type_hints(func)
    except:
        type_hints = {}
    INTERNAL_PARAMS = ["creds", "user_id", "stream_id"]
    param_descriptions = {}
    param_schemas = {}
    if len(doc_parts) > 1:
        param_section = doc_parts[1].strip()
        param_lines = param_section.split("\n")
        current_param = None
        current_content = []
        for line in param_lines:
            line = line.strip()
            if not line:
                continue
            if ":" in line and not line.startswith(" "):
                if current_param and current_content:
                    param_content = " ".join(current_content).strip()
                    try:
                        if param_content.startswith("{") and param_content.endswith(
                            "}"
                        ):
                            param_schemas[current_param] = json.loads(param_content)
                            if "description" in param_schemas[current_param]:
                                param_descriptions[current_param] = param_schemas[
                                    current_param
                                ]["description"]
                        else:
                            param_descriptions[current_param] = param_content
                    except json.JSONDecodeError:
                        param_descriptions[current_param] = param_content
                current_param = line.split(":", 1)[0].strip()
                current_content = [line.split(":", 1)[1].strip()]
            else:
                if current_param:
                    current_content.append(line)
        if current_param and current_content:
            param_content = " ".join(current_content).strip()
            try:
                if param_content.startswith("{") and param_content.endswith("}"):
                    param_schemas[current_param] = json.loads(param_content)
                    if "description" in param_schemas[current_param]:
                        param_descriptions[current_param] = param_schemas[
                            current_param
                        ]["description"]
                else:
                    param_descriptions[current_param] = param_content
            except json.JSONDecodeError:
                param_descriptions[current_param] = param_content
    fields = {}
    required_params = []
    for name, param in sig.parameters.items():
        if name in INTERNAL_PARAMS:
            continue
        has_default = param.default is not inspect.Parameter.empty
        ann = type_hints.get(name, param.annotation)
        default = param.default
        if ann == inspect._empty:
            ann = Any
        field_description = param_descriptions.get(
            name, f"Parameter {name} for {func_name}"
        )

        if name in param_schemas:
            if not has_default:
                required_params.append(name)
            continue

        if param.kind == param.VAR_POSITIONAL:  # *args
            if get_origin(ann) is tuple:
                args_of_tuple = get_args(ann)
                if len(args_of_tuple) == 2 and args_of_tuple[1] is Ellipsis:
                    ann = list[args_of_tuple[0]]
                else:
                    ann = list[Any]
            else:
                ann = list[ann]

            fields[name] = (
                ann,
                Field(default_factory=list, description=field_description),
            )

        elif param.kind == param.VAR_KEYWORD:  # **kwargs
            if get_origin(ann) is dict:
                dict_args = get_args(ann)
                if len(dict_args) == 2:
                    ann = dict[dict_args[0], dict_args[1]]
                else:
                    ann = dict[str, Any]
            else:
                ann = dict[str, ann]

            fields[name] = (
                ann,
                Field(default_factory=dict, description=field_description),
            )

        else:
            if has_default:
                fields[name] = (
                    ann,
                    Field(default=default, description=field_description),
                )
            else:
                fields[name] = (ann, Field(..., description=field_description))

    ParamsModel = create_model(f"{func_name}_params", **fields)
    model_schema = ParamsModel.model_json_schema()
    properties = model_schema.get("properties", {})
    model_schema = ensure_strict_json_schema(model_schema)
    required_params = list(properties.keys())

    for name, schema in param_schemas.items():
        properties[name] = schema

    return {
        "type": "function",
        "name": func_name,
        "description": main_description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required_params,
            "additionalProperties": False,
        },
    }
