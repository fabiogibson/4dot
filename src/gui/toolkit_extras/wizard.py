# -*- coding: utf-8 -*-
import asyncio
from collections import deque

from prompt_toolkit.layout import Layout
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.key_binding.key_bindings import KeyBindings


class Wizard:
    def __init__(self, steps, status_text_handler, style=None):
        self.steps = steps
        self.current_step = 0
        self.app = None
        self.style = style
        self.status_bar = Window(content=FormattedTextControl(
            status_text_handler),
            height=D.exact(1),
            style='class:status')

    def render(self):
        self._bind_keys()
        step_control = self.step.draw()
        layout = HSplit([step_control, self.status_bar, ])
        self.app.layout = Layout(layout, focused_element=step_control)
        self.app.layout.reset()

    def _unbind_keys(self):
        kb = self.app.key_bindings
        for k in self.step._key_bindings():
            kb.remove(k)

    def _bind_keys(self):
        kb = self.app.key_bindings
        for k, v in self.step._key_bindings().items():
            kb.add(k)(v)

    @property
    def step(self):
        return self.steps[self.current_step]

    def next(self, *args, **kwargs):
        if self.current_step < len(self.steps) - 1:
            self._unbind_keys()
            self.current_step += 1
            self.render()

    def previous(self, *args, **kwargs):
        if self.current_step > 0:
            self._unbind_keys()
            self.current_step -= 1
            self.render()

    def cancel(self, *args, **kwargs):
        self.app.exit(),

    def start(self):
        bindings = KeyBindings()
        bindings.add('c-n')(self.next)
        bindings.add('c-left')(self.previous)
        bindings.add('c-p')(self.previous)
        bindings.add('c-right')(self.next)
        bindings.add('c-c')(self.cancel)

        layout = HSplit([
            self.step.draw(),
            self.status_bar,
        ])

        self.app = Application(
            layout=Layout(layout),
            key_bindings=bindings,
            enable_page_navigation_bindings=True,
            mouse_support=True,
            style=self.style,
            full_screen=True)

        self._bind_keys()
        self.app.run()


class MODES:
    mode_list = 0
    mode_input = 1


class MultiModeWindow:
    def __init__(self, modes, status_text_handler, style=None):
        self.app = None
        self.modes = modes
        self.style = style
        self.current_control = None
        self.status_bar = Window(content=FormattedTextControl(
            status_text_handler),
            height=D.exact(1),
            style='class:status')

    def state_changed(self, state):
        if not self.app:
            self.current_control = self.modes[state]
            self.create_app()
        else:
            self._unbind_keys()
            self.current_control = self.modes[state]
            self._bind_keys()
            self.app.layout = self.build_layout()
            self.app.layout.reset()
            self.current_control.draw_complete()

    def build_layout(self):
        drawed_state_control = self.current_control()

        container = HSplit([
            drawed_state_control,
            self.status_bar,
        ])

        if self.current_control.focusable:
            return Layout(container, focused_element=drawed_state_control)

        return Layout(container)

    def quit(self, *args, **kwargs):
        self.app.exit(result=None, exception=None, style='')

    def create_app(self):
        bindings = KeyBindings()
        bindings.add('c-c')(self.quit)

        self.app = Application(
            layout=self.build_layout(),
            key_bindings=bindings,
            enable_page_navigation_bindings=True,
            mouse_support=True,
            style=self.style,
            full_screen=True)

        self._bind_keys()
        self.app.run()

    def _unbind_keys(self):
        state_kb = self.current_control.key_bindings
        if not state_kb:
            return

        kb = self.app.key_bindings
        for k in state_kb:
            for _k in k.split(','):
                kb.remove(_k.strip())

    def _bind_keys(self):
        state_kb = self.current_control.key_bindings
        if not state_kb:
            return

        kb = self.app.key_bindings
        for k, v in state_kb.items():
            for _k in k.split(','):
                kb.add(_k.strip())(v)
