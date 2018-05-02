import os
from datetime import datetime, date, timedelta, time as _time

import click
from babel.dates import format_date, format_time, format_timedelta, format_datetime
from colorama import Fore

from forponto import ForPonto
from gui import justification_window

class ListMarksCommand:
    """
    This is a command class
    """
    formatters = {
        date: lambda m: format_date(m, format='EEE, dd/MM/yy', locale='pt_BR'),
        _time: lambda m: format_time(m, format='short', locale='pt_BR'),
        datetime: lambda m: format_datetime(m, format='HH:mm', locale='pt_BR'),
        timedelta: lambda m: format_timedelta(m, locale='pt_BR'),
    }

    def format(self, value, width=0, empty=''):
        fmt = self.formatters.get(type(value))
        val = fmt(value) if value and fmt else empty
        return val.ljust(width)

    def _filter(self, mark):
        return True

    def _print(self, mark):
        pass

    def _no_print(self):
        pass

    def _print_headers(self):
        return []

    def __init__(self, user, password):
        self.user = user
        self.password = password
        forponto = ForPonto()

        with forponto.Session(user=self.user, password=self.password) as fp:
            if not fp.authenticate():
                return click.echo(
                    Fore.RED + '** Matrícula não cadastrada ou senha inválida.')

        marks = [m for m in fp.read_marks() if self._filter(m)]

        if not marks:
            for s in self._no_print():
                click.echo(s)
            return

        for h in self._print_headers():
            click.echo(h)

        for mark in marks:
            for s in self._print(mark):
                click.echo(s)



@click.command()
#  @click.option('--mes', default=datetime.now().month, help='Mês.')
#  @click.option('--ano', default=datetime.now().year, help='Ano.')
@click.option('--user', prompt='Matrícula', envvar='FORPONTO_USER')
@click.option('--password', prompt='Senha', envvar='FORPONTO_PASSWORD')
class ListErrorsCommand(ListMarksCommand):
    """
    Lista os dias onde houve erros de  marcação.
    """
    def _filter(self, mark):
        return mark.has_missing

    def _print(self, mark):
        yield f"{self.format(mark.date)}\t{len(mark.marks)} marcações"

    def _no_print(self):
        yield '** Não foram encontrados erros de marcação no período selecionado.'


@click.command()
#  @click.option('--mes', default=datetime.now().month, help='Mês.')
#  @click.option('--ano', default=datetime.now().year, help='Ano.')
@click.option('--user', prompt='Matrícula', envvar='FORPONTO_USER')
@click.option('--password', prompt='Senha', envvar='FORPONTO_PASSWORD')
class ListExtrasCommand(ListMarksCommand):
    """
    Lista os dias com marcação de hora extra.

    """
    def _filter(self, mark):
        return mark.has_day_extras or mark.has_night_extras or mark.has_credit

    def _print_headers(self):
        yield Fore.GREEN + ''.join(h.ljust(w) for h,w in (
            ('DATA', 20),
            ('HORAS TRABALHADAS', 20),
            ('H.E. DIURNAS', 20),
            ('H.E. NOTURNAS', 20),
            ('BANCO DE HORAS', 20),
            ('JUSTIFICATIVA', 0),
        ))

    def _print(self, mark):
        color = Fore.YELLOW if not mark.justification else Fore.BLUE

        yield color + (
            f'{self.format(mark.date, 20)}'
            f'{self.format(mark.business, 20)}'
            f'{self.format(mark.day_extras, 20)}'
            f'{self.format(mark.night_extras, 20)}'
            f'{self.format(mark.credit, 20)}'
            f'{mark.justification or ""}'
        )
    def _no_print(self):
        yield '** Não foram encontradas marcações além da jornada no período selecionado.'


@click.command()
#  @click.option('-m', '--mes', default=datetime.now().month, type=click.IntRange(1, 12), help='Exibir marcações referente ao mês. (1 a 12)')
#  @click.option('-a', '--ano', default=datetime.now().year, help='Exibir marcações refente ao ano.')
@click.option('--user', prompt='Matrícula', envvar='FORPONTO_USER')
@click.option('--password', prompt='Senha', envvar='FORPONTO_PASSWORD')
class ListBreaksCommand(ListMarksCommand):
    """
    Lista de intervalos registrados no último mês.
    """
    def _filter(self, mark):
        return not mark.date.weekday() in (5, 6)

    def _print_headers(self):
        yield Fore.GREEN + ''.join(h.ljust(w) for h,w in (
            ('DATA', 20),
            ('INTERVALOS', 0),
        ))

    def _print(self, mark):
        line = Fore.WHITE + f'{self.format(mark.date, 20)}'

        if mark.is_empty:
            yield line + 'Sem marcações'
        else:
            yield line + f'{self.format(mark.breaks)}'



@click.command()
#  @click.option('-m', '--mes', default=datetime.now().month, type=click.IntRange(1, 12), help='Exibir marcações referente ao mês. (1 a 12)')
#  @click.option('-a', '--ano', default=datetime.now().year, help='Exibir marcações refente ao ano.')
@click.option('--user', prompt='Matrícula', envvar='FORPONTO_USER')
@click.option('--password', prompt='Senha', envvar='FORPONTO_PASSWORD')
class ListMarkDetailsCommand(ListMarksCommand):
    """
    Lista de marcações registradas no último mês.
    """
    def _filter(self, mark):
        return not mark.date.weekday() in (5, 6)

    @property
    def separator(self):
        return Fore.CYAN + 120 * '-'

    def get_mark_format(self, mark):
        if mark.is_empty:
            return Fore.LIGHTWHITE_EX

        if mark.has_missing:
            return Fore.RED

        if mark.working_hours < _time(8, 15):
            return Fore.MAGENTA

        if mark.has_day_extras or mark.has_night_extras or mark.has_credit:
            return Fore.BLUE if mark.justification else Fore.YELLOW

        return Fore.WHITE

    def _print(self, mark):
        color = self.get_mark_format(mark)
        line = color + '\N{SPIRAL CALENDAR PAD} ' + self.format(mark.date, 20)

        if mark.is_empty:
            yield line + 'Sem marcações'
        else:
            yield line + str.join('  -  ', [self.format(m) for m in mark.marks]).ljust(60)

            item = Fore.WHITE + f' \N{BLACK FOUR POINTED STAR} '
            yield f'{item} Total de horas: {self.format(mark.working_hours)}'

            yield f'{item} Horas normais: {self.format(mark.business)}'

            if mark.has_credit:
                yield f'{item} Banco de Horas: {self.format(mark.credit)}'

            if mark.has_day_extras:
                yield f'{item} Horas extras diurnas: {self.format(mark.day_extras)}'

            if mark.has_night_extras:
                yield f'{item} Horas extras noturnas: {self.format(mark.night_extras)}'

            yield f'{item} Intervalos: {self.format(mark.breaks)}'

            if mark.has_debt:
                yield f'{item} Saldo negativo: {self.format(mark.debt)}'

            if mark.justification:
                yield f'{item} Justificativa: {mark.justification}'


            if mark.date == date.today():
                yield f'{Fore.GREEN}Saída prevista: {self.format(mark.expected_journey_end)}'

        yield self.separator

    def _no_print(self):
        yield '** Não foram encontradas marcações no período selecionado.'


@click.command()
def legenda():
    """
    Exibe a legenda referente aos dias de marcação.
    """
    click.echo(Fore.WHITE + 'Dias onde não houve marcação.')
    click.echo(Fore.RED + 'Dias onde houve erros de marcação.')
    click.echo(Fore.MAGENTA + 'Dias onde a jornada de trabalho foi inferior a 08:15h')
    click.echo(Fore.YELLOW + 'Dias onde a jornada de trabalho foi superior a 08:15h mas ainda não houve justificativa.')
    click.echo(Fore.BLUE + 'Dias onde a jornada excedente de trabalho foi justificada.')


@click.command()
@click.option('--user', prompt='Matrícula', envvar='FORPONTO_USER')
@click.option('--password', prompt='Senha', envvar='FORPONTO_PASSWORD')
def justificar(user, password):
    """
    Registra justificativas de horas excedentes a jornada de 8:15h.
    """
    forponto = ForPonto()

    with forponto.Session(user=user, password=password) as fp:
        if not fp.authenticate():
            return click.echo(
                Fore.RED + '** Matrícula não cadastrada ou senha inválida.')

        marks = [m for m in fp.read_marks() if m.has_day_extras or m.has_night_extras or m.has_credit]
        justification_window.show(marks, fp)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if not ctx.invoked_subcommand:
        ListMarkDetailsCommand()


cli.add_command(ListErrorsCommand, 'erros')
cli.add_command(ListExtrasCommand, 'extras')
cli.add_command(ListMarkDetailsCommand, 'marcacoes')
cli.add_command(ListBreaksCommand, 'intervalos')
cli.add_command(justificar)
cli.add_command(legenda)
