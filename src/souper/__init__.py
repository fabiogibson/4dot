from bs4 import BeautifulSoup


class SouperElement:
    def __init__(self, element):
        self.element = element

    def __getattr__(self, attr):
        return SouperQuery(attr, self.element)

    def get(self, attr):
        return self.element.get(attr, None)

    def __repr__(self):
        return repr(self.element)

    def __str__(self):
        return str(self.element)

    @property
    def text(self):
        return self.element.text


class SouperQuery:
    def __init__(self, attr, soup):
        self.attr = attr
        self.soup = soup

    def parse_filters(self, args):
        filters = {}

        for arg in args:
            if arg.startswith('.'):
                filters['class'] = arg[1:]

            elif arg.startswith('#'):
                filters['id'] = arg[1:]

            else:
                filters['name'] = arg

        return filters

    def one(self, *args, **kwargs):
        filters = self.parse_filters(args)
        el = self.soup.find(self.attr, filters)
        if not el:
            return None
        return SouperElement(el)

    def all(self, *args, **kwargs):
        filters = self.parse_filters(args)
        return [SouperElement(e) for e in self.soup.find_all(self.attr, filters)]


class Souper:
    def __init__(self, html, parser='html.parser'):
        self.soup = BeautifulSoup(html, parser)

    def __getattr__(self, attr):
        return SouperQuery(attr=attr, soup=self.soup)

