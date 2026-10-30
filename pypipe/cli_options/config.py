from pathlib import Path

import click
import yaml
from schema import And, Optional, Or, Schema, SchemaError

from run_helpers import config as runtime_config

from .click_support import GroupedOption

SCHEMA_PATH = Path(__file__).with_name("config.schema.yaml")
CONFIG_SCHEMA = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
COMMAND_SCHEMAS = CONFIG_SCHEMA["commands"]
CONFIG_OPTIONS = {
    command_name: frozenset(command_schema["properties"])
    for command_name, command_schema in COMMAND_SCHEMAS.items()
}
DEFAULT_MACHINE = runtime_config.MACHINE


def _type_schema(type_name):
    if isinstance(type_name, list):
        return Or(*(_type_schema(item) for item in type_name))
    if type_name == "string":
        return str
    if type_name == "integer":
        return And(int, lambda value: not isinstance(value, bool))
    if type_name == "boolean":
        return bool
    if type_name == "null":
        return None
    if type_name == "array":
        return [object]
    raise ValueError(f"Unsupported config schema type: {type_name}")


def _property_schema(property_definition):
    validator = _type_schema(property_definition["type"])
    if "items" in property_definition:
        validator = [_type_schema(property_definition["items"])]
    if "enum" in property_definition:
        validator = And(validator, lambda value: value in property_definition["enum"])
    return validator


COMMAND_VALIDATORS = {
    command_name: Schema(
        {
            Optional(option_name): _property_schema(property_definition)
            for option_name, property_definition in command_schema["properties"].items()
        }
    )
    for command_name, command_schema in COMMAND_SCHEMAS.items()
}


def load_config(ctx, param, config_path):
    if config_path is None:
        runtime_config.MACHINE = runtime_config.DEFAULT_MACHINE
        return None

    try:
        config_values = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    except OSError as error:
        raise click.BadParameter(f"cannot read config file: {error}", param=param)
    except yaml.YAMLError as error:
        raise click.BadParameter(f"invalid YAML: {error}", param=param)

    if config_values is None:
        config_values = {}
    if not isinstance(config_values, dict):
        raise click.BadParameter("the YAML document must be a mapping", param=param)
    if any(not isinstance(key, str) for key in config_values):
        raise click.BadParameter("all YAML option names must be strings", param=param)

    command_name = ctx.command.name.lower()
    allowed_options = CONFIG_OPTIONS[command_name]
    command_options = {
        option.name for option in ctx.command.params if option.name != "config_path"
    }
    if allowed_options != command_options:
        missing = sorted(command_options - allowed_options)
        stale = sorted(allowed_options - command_options)
        raise click.ClickException(
            f"Config option registry for {command_name} is out of sync "
            f"(unlisted: {missing}; unknown: {stale})"
        )

    unknown_options = sorted(set(config_values) - allowed_options)
    if unknown_options:
        raise click.BadParameter(
            f"unknown option(s) for {command_name}: {', '.join(unknown_options)}",
            param=param,
        )

    try:
        COMMAND_VALIDATORS[command_name].validate(config_values)
    except SchemaError as error:
        raise click.BadParameter(
            f"invalid {command_name} config: {error.code}", param=param
        ) from error

    runtime_config.MACHINE = config_values.get("machine", DEFAULT_MACHINE)
    ctx.default_map = {**(ctx.default_map or {}), **config_values}
    return config_path


def config_option(function):
    """Add eager YAML config loading to a subcommand."""
    return click.option(
        "--config",
        "config_path",
        cls=GroupedOption,
        help_group="Configuration",
        type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
        is_eager=True,
        expose_value=False,
        callback=load_config,
        help="Read option defaults from a YAML file; command-line options take precedence.",
    )(function)
