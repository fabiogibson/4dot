# -*- coding: utf-8 -*-
from datetime import date
import asyncio

from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.widgets import Dialog, Button, Label, TextArea, ProgressBar, Box
from prompt_toolkit.layout.dimension import Dimension as D

from gui.toolkit_extras.widgets import DateCheck


class BaseDialog:
    def __init__(self, state_control, focusable=True):
        self.state_control = state_control
        self.focusable = focusable

    @property
    def key_bindings(self):
        pass

    def __call__(self):
        return self.draw()

    def draw_complete(self):
        pass

    def draw(self):
        pass


class ListDialog(BaseDialog):
    def __init__(self, text, title, state_control):
        super().__init__(state_control)
        self.checks = None
        self.title = title
        self.text = text

    def select_all(self, *args, **kwargs):
        for c in self.checks:
            c.checked = True

    def deselect_all(self, *args, **kwargs):
        for c in self.checks:
            c.checked = False

    def switch_to_justify(self, *args, **kwargs):
        if not self.checks:
            return

        for c in self.checks:
            if c.checked:
                self.state_control.select_mark(c.mark)

        if self.state_control.marks:
            self.state_control('justify')

    @property
    def key_bindings(self):
        return {
            'down, j': focus_next,
            'up, k': focus_previous,
            'a': self.select_all,
            'x': self.deselect_all,
            'o': self.switch_to_justify,
        }

    def draw(self):
        self.checks = [
            DateCheck(mark=m) for m in self.state_control.marks
            if not m.justification or not m.synced
        ]

        if not self.checks:
            self.focusable = False
            self.text = 'Não existem justificativas pendentes.\n\nPressione Ctrl-c para sair.'

        return Dialog(
            title=self.title,
            body=HSplit([
                Label(text=self.text, dont_extend_height=True),
                *self.checks,
            ], padding=1),
            with_background=True)


class SyncDialog(BaseDialog):
    def __init__(self, forponto_session, state_control):
        super().__init__(state_control, focusable=False)
        self.percentage = 0
        self.forponto_session = forponto_session

    def set_percentage(self, step):
        self.percentage = min(self.percentage + int(step), 100)
        self.progressbar.percentage = self.percentage

    def log_text(self, text):
        self.text_area.buffer.insert_text(text)

    async def worker(self, mark):
        """
        """
        self.log_text('Inserindo justificativa para o dia: {}\n'.format(mark.date))
        mark.synced = self.forponto_session.justify(mark)
        return mark

    async def do_tasks(self, loop):
        step = 100 // len(self.state_control.selected_marks)
        tasks = []

        for mark in self.state_control.selected_marks:
            future = asyncio.ensure_future(self.worker(mark), loop=loop)
            future.add_done_callback(lambda r: self.justify_done(r, step))
            tasks.append(future)

        await asyncio.gather(*tasks)
        self.set_percentage(100)
        self.state_control.clear_selection()
        self.state_control('list')

    def justify_done(self, ret, step):
        mark = ret.result()

        if mark.synced:
            self.log_text(f'{mark.date} justificado com sucesso.\n')
        else:
            self.log_text(f'Erro ao justificar o dia {mark.date}.\n')

        self.set_percentage(step)

    def draw(self):
        self.progressbar = ProgressBar()
        self.text_area = TextArea(
            focusable=False,
            height=D(preferred=10))

        return Dialog(
            body=HSplit([
                Box(Label(text="Sincronizando justificativas..."), height=D.exact(2)),
                Box(self.text_area, padding=D.exact(1)),
                self.progressbar,
            ]),
            title="4Dot",
            with_background=True)

    def draw_complete(self):
        self.percentage = 0
        self.set_percentage(0)
        loop = asyncio.get_event_loop()
        ts = loop.create_task(self.do_tasks(loop))


class InputDialog(BaseDialog):
    def __init__(self, title, text, state_control):
        super().__init__(state_control)
        self.title = title
        self.text = text
        self.textfield = None

    def justify(self):
        for m in self.state_control.selected_marks:
            m.justification = self.textfield.text
        self.state_control('sync')

    def draw(self):
        self.textfield = TextArea(
            multiline=False,
            style='class:dialog.textarea',
            password=False,
            completer=None,
            accept_handler=None)

        return Dialog(
            title=self.title,
            body=HSplit([
                Label(text=self.text, dont_extend_height=True),
                self.textfield,
            ], padding=D(preferred=1, max=1)),
            buttons=[
                Button(text='Salvar', handler=self.justify),
                Button(text='Voltar'),
                Button(text='Cancelar', handler=self.state_control),
            ],
            with_background=True)

