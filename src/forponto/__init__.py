# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime, timedelta, time as _time, date

import requests

from souper import Souper
from forponto.commands import ReadMarksCommand, JustifyCommand



class ForPontoSession:
    def __init__(self, base_url, user, password):
        self.base_url = base_url
        self.session = None
        self.user = user
        self.password = password
        self.tmp_user = None
        self.user_code = None
        self.fun_cracha = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US);'
        }

    def post(self, action, data):
        response = self.session.post(
            f'{self.base_url}/{action}', headers=self.headers, data=data,)

        if response.status_code == 200:
            return Souper(response.content)

    def read_content(self, url):
        page = self.session.get(f'{self.base_url}/{url}', headers=self.headers)
        return Souper(page.content)

    def read_tmp_user(self):
        content = self.read_content(self.base_url)
        self.tmp_user = content.soup.find('input', {'name': 'deEdtUserId'}).get('value')

    def authenticate(self):
        data = {
            "deEdtFunCrachaSel": self.user,
            "deEdtFunConsulta": self.password,
            "deEdtDataDe": '',
            "deEdtDataAte": '',
            "deEdtUserId": self.tmp_user,
            "deEdtPerfil": "C",
            "deEdtUsuCodigo": '',
            "deEdtFunCracha": self.user,
            "deEdtCrUsR": "K",
            "deEdtValidaMsg": "N",
        }

        content = self.post('PiConexaoUsuario', data=data)

        if 'Código de Consulta Inválido' in content.soup.text:
            return False

        frame_addr = content.frame.one('topFrame').get('src')
        content = self.read_content(frame_addr)
        self.tmp_user = content.soup.find('input', {'name': 'deEdtUserId'}).get('value')
        self.user_code = content.soup.find('input', {'name': 'deEdtUsuCodigo'}).get('value')
        self.fun_cracha = content.soup.find('input', {'name': 'deEdtFunCracha'}).get('value')
        return True

    def __enter__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.read_tmp_user()
        return self

    def read_marks(self):
        read_marks = ReadMarksCommand()
        return read_marks(self)

    async def justify(self, mark):
        justify = JustifyCommand(mark)
        mark.synced = justify(self)
        return mark

    async def justify_async(self, marks, loop, done_callback=None):
        tasks = []

        for mark in marks:
            task = asyncio.ensure_future(self.justify(mark), loop=loop)
            task.add_done_callback(done_callback)
            tasks.append(task)

        await asyncio.gather(*tasks)

    def __exit__(self, *args):
        pass


class ForPonto:
    def __init__(self):
        self.base_url = 'http://forponto/forponto/FptoWeb.exe'

    def Session(self, user, password):
        return ForPontoSession(self.base_url, user, password)
