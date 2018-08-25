import datetime

import click
from dateparser import parse


class ClickDate(click.ParamType):
    """
    A date object parsed via dateparser
    """

    name = "date"

    def get_metavar(self, param):
        return "<date string>"

    def convert(self, value, param, ctx):
        if isinstance(value, datetime.date):
            return value
        try:
            return parse(value).date()
        except ValueError as ex:
            self.fail(
                'Could not parse datetime string "{datetime_str}"'
                ' ({ex})'.format(
                    datetime_str=value,
                    ex=ex,
                ),
                param,
                ctx,
            )
