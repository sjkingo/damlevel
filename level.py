#!/usr/bin/env python

from bs4 import BeautifulSoup
from decimal import Decimal
import dateutil.parser
import re
import requests

URL = 'http://www.seqwater.com.au/water-supply/dam-levels'

class Dam(object):
    """
    Wrapper around a table row from the dam levels page and
    provides easy access to elements and values.
    """

    _id = None
    _id_patt = re.compile(r'[a-zA-Z]+(\d+)')

    def __init__(self, table_row):
        self._row = table_row

    def _value(self, name):
        el_id = 'dam{id}{name}'.format(id=self.id, name=name)
        return self._row.find(id=el_id).text.strip()

    @property
    def id(self):
        """Extracts the dam's ID number from the table row class
        and caches it as self._id
        """
        if not self._id:
            class_name = ' '.join(self._row.attrs.get('class'))
            self._id = int(self._id_patt.match(class_name).groups()[0])
        return self._id

    @property
    def name(self):
        return self._value('Nam').replace('*', '')

    @property
    def max_volume(self):
        return int(self._value('Max').replace(',', ''))

    @property
    def current_volume(self):
        return int(self._value('Vol').replace(',', ''))

    @property
    def percent(self):
        return Decimal(self._value('Per'))

    @property
    def updated(self):
        return dateutil.parser.parse(self._value('Read'))

    @property
    def comment(self):
        c = self._value('Comment')
        return c if len(c) > 0 else None

def parse_all_dams(html):
    all_dams = {}

    tree = BeautifulSoup(html, 'html.parser')
    dams_table = tree.find_all('table', class_='TableDataAllDams')[1]

    for dam_row in dams_table.select('tbody tr'):
        dam = Dam(dam_row)
        d = {'name': dam.name,
             'max': dam.max_volume,
             'current': dam.current_volume,
             'percent': dam.percent,
             'updated': dam.updated,
             'comment': dam.comment}
        all_dams[dam.name] = d

    return all_dams

def main():
    import sys

    html = requests.get(URL).text
    all_dams = parse_all_dams(html)

    try:
        dam = all_dams[sys.argv[1]]
    except KeyError:
        print('Error: a valid dam name must be specified, or no argument given',
                file=sys.stderr)
        exit(1)
    except IndexError:
        from pprint import pprint
        pprint(all_dams)
        return

    try:
        format_str = sys.argv[2]
    except IndexError:
        format_str = '{name} {percent}% {pretty_comment} {updated}'

    if format_str == '{all}':
        from pprint import pprint
        pprint(dam)
        return

    if dam['comment']:
        pretty_comment = '(%s)' % dam['comment']
    else:
        pretty_comment = ''

    print(format_str.format(pretty_comment=pretty_comment, **dam))


if __name__ == '__main__':
    main()
