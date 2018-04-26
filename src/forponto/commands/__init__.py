import unicodedata
from datetime import datetime, timedelta, date as _date, time as _time

import click

from forponto.models import Mark


class ForPontoCommand:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, session):
        pass


class JustifyCommand(ForPontoCommand):
    def __init__(self, mark):
        self.mark = mark

    def __call__(self, session):
        codes = []
        success = True

        if self.mark.has_credit:
            codes.append(706)

        if self.mark.has_day_extras:
            codes.append(260)

        if self.mark.has_night_extras:
            codes.append(261)

        for code in codes:
            data = {
                "deEdtDataDe": self.mark.date.strftime('%d/%m/%Y'),
                "deEdtMtvCodigo": code,
                "deEdtJusJustificativa": self.mark.justification,
                "deEdtFunCracha": session.fun_cracha.encode('windows-1252'),
                "deEdtUserId": session.tmp_user,
                "UserPrr": "SSS",
                "deEdtUsuCodigo": session.user_code,
                "deEdtPerfil": "C",
                "EdtUsuPermissoes": "NNNNNNNNNNXNN",
                "deEdtEpsCodigo": "00001",
                "deEdtFormOrigem": 844,
            }

            content = session.post("PiGravaJust", data=data)

            if 'Operação efetuada com sucesso' not in content.soup.text:
                success = False

        return success


class ReadMarksCommand(ForPontoCommand):
    def _parse_date(self, value):
        day_mark = unicodedata.normalize('NFKD', value)[:10].strip()
        return datetime.strptime(day_mark, '%d/%m/%Y').date()

    def _parse_marks(self, date, value):
        marks = unicodedata.normalize('NFKD', value).strip()

        if marks.startswith('Sem'):
            return []

        for mark in marks.split():
            h, m = mark.split(':')

            if h == '--':
               continue

            clock = (datetime.min + timedelta(hours=int(h), minutes=int(m))).time()
            yield datetime.combine(date, clock)

    def _parse_justification(self, el):
        if el:
            return el[1].input.one().get('value')

    def __call__(self, session):
        start_date = _date.today()

        if start_date.day > 10:
            start_date = start_date.replace(day=1)
        else:
            start_date = start_date - timedelta(days=20)

        data = {
            "deEdtFunCrachaSel": session.user,
            "deEdtDataDe": start_date.strftime('%d/%m/%Y'),
            "deEdtDataAte": datetime.now().date().strftime('%d/%m/%Y'),
            "deEdtUserId": session.tmp_user,
            "deEdtPerfil": "C",
            "deEdtFunCracha": session.user,
            "deEdtCrUsR": "K",
        }

        content = session.post('PiConsulta', data=data)
        frame = content.frame.one(name='topFrame')

        content = session.read_content(frame.get('src'))
        table_ponto = content.table.one('.fiotabelaponto')
        lines = table_ponto.tr.all('.celulatabptomarc')

        for line in lines:
            txt_date = line.font.one('.fontetabptodata').text
            txt_marks = line.font.one('.fontetabptomarc').text

            date = self._parse_date(txt_date)
            marks = list(self._parse_marks(date, txt_marks))
            justification = self._parse_justification(table_ponto.p.all(f'#{txt_date[:10]}706'))

            if not justification:
                justification = self._parse_justification(table_ponto.p.all(f'#{txt_date[:10]}260'))

            if not justification:
                justification = self._parse_justification(table_ponto.p.all(f'#{txt_date[:10]}261'))

            yield Mark(date=date, marks=marks, justification=justification)
