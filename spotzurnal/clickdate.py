import datetime

import click


class ClickDate(click.ParamType):
    """
    A date object parsed via datetime.strptime.
    """

    name = "date"

    def __init__(self, fmt):
        self.fmt = fmt

    def get_metavar(self, param):
        return self.fmt

    def convert(self, value, param, ctx):
        if isinstance(value, datetime.date):
            return value
        try:
            return datetime.datetime.strptime(value, self.fmt).date()
        except ValueError as ex:
            self.fail(
                'Could not parse datetime string "{datetime_str}"'
                'formatted as {format} ({ex})'.format(
                    datetime_str=value,
                    format=self.fmt,
                    ex=ex,
                ),
                param,
                ctx,
            )
