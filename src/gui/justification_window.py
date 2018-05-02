# -*- coding: utf-8 -*-
from datetime import date as _date
from collections import deque
import asyncio

from prompt_toolkit.styles import Style
from prompt_toolkit.application.current import get_app
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop

from gui.toolkit_extras.wizard import MultiModeWindow
from gui.toolkit_extras.dialogs import InputDialog, ListDialog, SyncDialog
from gui.toolkit_extras.widgets import DateCheck


class StateControl:
    def __init__(self, marks):
        self.marks = marks
        self.selected_marks = set()
        self.state = deque()
        self.control = None
        self.subscribers = set()

    def subscribe(self, handler):
        self.subscribers.add(handler)

    def change_state(self, state=None):
        if state:
            self.state.append(state)
        else:
            if len(self.state) > 0:
                self.state.pop()

        for s in self.subscribers:
            s(self.state[-1])

    def select_mark(self, mark):
        self.selected_marks.add(mark)

    def clear_selection(self):
        self.selected_marks.clear()

    def __call__(self, state=None):
        self.change_state(state)


def show(marks, forponto_session):
    def get_statusbar_text():
        return [
            ('class:status', '4dot - '),
            ('class:status', ' Pressione '),
            ('class:status.key', '[a]'),
            ('class:status', ' para selecionar todas | '),
            ('class:status.key', '[x]'),
            ('class:status', ' para desmarcar todas | '),
            ('class:status.key', '[o]'),
            ('class:status', ' para justificar | '),
            ('class:status.key', 'Ctrl - c'),
            ('class:status', ' para sair.'),
        ]

    dialog_style = Style.from_dict({
        'dialog frame-label': 'bg:#ffffff #000000',
        'dialog.body shadow': 'bg:#00aa00',
        'dialog.textarea':    '#000000',
        'status':             'reverse',
        'status.key':         '#ffaa00',
    })

    state_control = StateControl(marks)

    list_dialog = ListDialog(
        text='Selecione as datas que deseja justificar:',
        title='4Dot',
        state_control=state_control,
    )

    input_dialog = InputDialog(
        title='4Dot',
        text='Informe a justificativa:',
        state_control=state_control,
    )

    sync_dialog = SyncDialog(
        state_control=state_control,
        forponto_session=forponto_session,
    )

    modes = {
        'list': list_dialog,
        'justify': input_dialog,
        'sync': sync_dialog,
    }

    win = MultiModeWindow(
        modes=modes,
        status_text_handler=get_statusbar_text,
        style=dialog_style,
    )

    loop = asyncio.new_event_loop()
    use_asyncio_event_loop()

    state_control.subscribe(win.state_changed)
    state_control('list')
