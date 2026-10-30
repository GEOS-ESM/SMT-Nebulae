import click


class GroupedOption(click.Option):
    """Click option that stores a help-group name."""

    def __init__(self, *args, **kwargs):
        self.help_group = kwargs.pop("help_group", "Options")
        super().__init__(*args, **kwargs)


class CaseInsensitiveGroup(click.Group):
    """Allow command names to be typed in any case."""

    def get_command(self, ctx, cmd_name):
        command = click.Group.get_command(self, ctx, cmd_name)
        if command is not None:
            return command
        for name in self.list_commands(ctx):
            if name.lower() == cmd_name.lower():
                return click.Group.get_command(self, ctx, name)
        return None


class AllErrorsCommand(click.Command):
    """Report all missing and invalid options in one pass."""

    def parse_args(self, ctx, args):
        parser = self.make_parser(ctx)
        opts, args, param_order = parser.parse_args(args=args)

        errors = []
        for param in click.core.iter_params_for_processing(
            param_order, self.get_params(ctx)
        ):
            try:
                _value, args = param.handle_parse_result(ctx, opts, args)
            except click.exceptions.MissingParameter:
                errors.append(self._format_missing(param, ctx))
            except click.exceptions.UsageError as error:
                errors.append(str(error))

        if errors:
            ctx.fail("\n".join(errors))

        if args and not ctx.allow_extra_args and not ctx.resilient_parsing:
            ctx.fail(
                f"Got unexpected extra argument{'s' if len(args) != 1 else ''} ({' '.join(map(str, args))})"
            )

        ctx.args = args
        return args

    @staticmethod
    def _format_missing(param, ctx):
        hint = param.get_error_hint(ctx)
        message = f"Missing option {hint}."
        if isinstance(param.type, click.Choice):
            choices = ",\n\t".join(param.type.choices)
            message += f" Choose from:\n\t{choices}"
        return message

    def format_options(self, ctx, formatter):
        options = {}
        for param in self.get_params(ctx):
            record = param.get_help_record(ctx)
            if record is not None:
                group_name = getattr(param, "help_group", "Options")
                options.setdefault(group_name, []).append(record)

        for group_name, group_options in options.items():
            with formatter.section(group_name):
                formatter.write_dl(group_options)
