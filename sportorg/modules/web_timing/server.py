from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from aiohttp import web

from sportorg import config
from sportorg.models.memory import ResultManual, race
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.live.live import live_client
from sportorg.modules.teamwork.teamwork import Teamwork


class WebTimingServer:
    _instance: Optional['WebTimingServer'] = None

    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 8088
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.started = False

    @classmethod
    def instance(cls) -> 'WebTimingServer':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def ensure_storage(self):
        r = race()
        if not hasattr(r, 'web_stage_passages'):
            r.web_stage_passages = []
        if not hasattr(r, 'web_timing_stage_token'):
            r.web_timing_stage_token = ''
        if not hasattr(r, 'web_timing_finish_token'):
            r.web_timing_finish_token = ''
        if not r.web_timing_stage_token:
            r.web_timing_stage_token = uuid.uuid4().hex[:12]
        if not r.web_timing_finish_token:
            r.web_timing_finish_token = uuid.uuid4().hex[:12]

    def get_local_ip(self) -> str:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'

    def get_stage_url(self) -> str:
        self.ensure_storage()
        return f'http://{self.get_local_ip()}:{self.port}/timing/stage?token={race().web_timing_stage_token}'

    def get_finish_url(self) -> str:
        self.ensure_storage()
        return f'http://{self.get_local_ip()}:{self.port}/timing/finish?token={race().web_timing_finish_token}'

    def get_viewer_summary_url(self) -> str:
        return f'http://{self.get_local_ip()}:{self.port}/viewer/summary'

    def get_viewer_group_url(self) -> str:
        return f'http://{self.get_local_ip()}:{self.port}/viewer/group'

    def start(self, port: int = 8088):
        if self.started:
            return
        self.port = int(port)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        time.sleep(0.4)

    def stop(self):
        if not self.started or not self.loop:
            return
        future = asyncio.run_coroutine_threadsafe(self._stop_async(), self.loop)
        future.result(timeout=5)
        self.started = False

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._start_async())
        self.started = True
        self.loop.run_forever()

    async def _start_async(self):
        app = web.Application()
        app.add_routes(
            [
                web.get('/timing/stage', self.handle_stage_page),
                web.get('/timing/finish', self.handle_finish_page),
                web.get('/viewer/summary', self.handle_viewer_summary_page),
                web.get('/viewer/group', self.handle_viewer_group_page),
                web.get('/manifest.webmanifest', self.handle_manifest),
                web.get('/sw.js', self.handle_sw),
                web.get('/pwa-icon.svg', self.handle_pwa_icon),
                web.get('/api/participants', self.handle_participants),
                web.get('/api/stages', self.handle_stages),
                web.get('/api/groups', self.handle_groups),
                web.get('/api/event-info', self.handle_event_info),
                web.get('/api/stage-log', self.handle_stage_log),
                web.get('/api/finish-log', self.handle_finish_log),
                web.get('/api/viewer/summary', self.handle_viewer_summary),
                web.get('/api/viewer/group', self.handle_viewer_group),
                web.post('/api/stage-pass', self.handle_stage_pass),
                web.post('/api/finish', self.handle_finish),
            ]
        )
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

    async def _stop_async(self):
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

    def _check_token(self, request: web.Request, token_type: str) -> bool:
        self.ensure_storage()
        token = request.query.get('token', '')
        if token_type == 'stage':
            return token == race().web_timing_stage_token
        if token_type == 'finish':
            return token == race().web_timing_finish_token
        return True

    async def handle_manifest(self, request: web.Request):
        return web.Response(text=self._read_template('pwa_manifest.webmanifest'), content_type='application/manifest+json')

    async def handle_sw(self, request: web.Request):
        return web.Response(text=self._read_template('pwa_sw.js'), content_type='application/javascript')

    async def handle_pwa_icon(self, request: web.Request):
        path = Path(config.icon_dir('sportorg.svg'))
        return web.Response(text=path.read_text(encoding='utf-8'), content_type='image/svg+xml')

    async def handle_stage_page(self, request: web.Request):
        if not self._check_token(request, 'stage'):
            return web.Response(text='Forbidden', status=403)
        return web.Response(text=self._read_template('web_timing_stage.html'), content_type='text/html')

    async def handle_finish_page(self, request: web.Request):
        if not self._check_token(request, 'finish'):
            return web.Response(text='Forbidden', status=403)
        return web.Response(text=self._read_template('web_timing_finish.html'), content_type='text/html')

    async def handle_viewer_summary_page(self, request: web.Request):
        return web.Response(text=self._read_template('web_viewer_summary.html'), content_type='text/html')

    async def handle_viewer_group_page(self, request: web.Request):
        return web.Response(text=self._read_template('web_viewer_group.html'), content_type='text/html')

    async def handle_participants(self, request: web.Request):
        data = []
        for p in race().persons:
            data.append(
                {
                    'id': str(p.id),
                    'bib': p.bib,
                    'name': f'{p.surname} {p.name}'.strip(),
                    'group': p.group.name if p.group else '',
                    'group_id': str(p.group.id) if p.group else '',
                    'organization': p.organization.name if p.organization else '',
                }
            )
        return web.json_response(data)

    async def handle_stages(self, request: web.Request):
        stages = []
        for stage in getattr(race(), 'tourism_stages', []):
            stages.append(
                {
                    'id': stage.id,
                    'group_id': getattr(stage, 'group_id', ''),
                    'order_num': stage.order_num,
                    'name': stage.name,
                }
            )
        return web.json_response(stages)

    async def handle_event_info(self, request: web.Request):
        data = {
            'title': race().data.title,
            'location': race().data.location,
            'date': str(race().data.get_start_datetime().date()) if race().data.get_start_datetime() else '',
        }
        return web.json_response(data)

    async def handle_groups(self, request: web.Request):
        data = []
        for g in race().groups:
            data.append({'id': str(g.id), 'name': g.name})
        return web.json_response(data)

    async def handle_stage_log(self, request: web.Request):
        self.ensure_storage()
        return web.json_response(getattr(race(), 'web_stage_passages', [])[-30:])

    async def handle_finish_log(self, request: web.Request):
        log = []
        for result in race().results[-30:]:
            if result.person:
                log.append(
                    {
                        'bib': result.person.bib,
                        'name': f'{result.person.surname} {result.person.name}'.strip(),
                        'time': result.get_finish_time().to_str(),
                    }
                )
        return web.json_response(log)

    async def handle_stage_pass(self, request: web.Request):
        self.ensure_storage()
        if not self._check_token(request, 'stage'):
            return web.json_response({'ok': False, 'error': 'forbidden'}, status=403)
        data = await request.json()
        person_id = str(data.get('person_id', ''))
        stage_id = str(data.get('stage_id', ''))

        person = self._find_person(person_id)
        stage = self._find_stage(stage_id)
        if not person or not stage:
            return web.json_response({'ok': False, 'error': 'person or stage not found'}, status=400)

        item = {
            'id': str(uuid.uuid4()),
            'person_id': person_id,
            'person_name': f'{person.surname} {person.name}'.strip(),
            'bib': person.bib,
            'group': person.group.name if person.group else '',
            'stage_id': stage_id,
            'stage_name': stage.name,
            'timestamp_msec': int(time.time() * 1000),
            'timestamp_text': time.strftime('%H:%M:%S'),
            'is_valid_for_group': bool(person.group and getattr(stage, 'group_id', '') == str(person.group.id)),
        }
        race().web_stage_passages.append(item)
        return web.json_response({'ok': True, 'item': item})

    async def handle_finish(self, request: web.Request):
        if not self._check_token(request, 'finish'):
            return web.json_response({'ok': False, 'error': 'forbidden'}, status=403)
        data = await request.json()
        person_id = str(data.get('person_id', ''))
        person = self._find_person(person_id)
        if not person:
            return web.json_response({'ok': False, 'error': 'person not found'}, status=400)

        existing = race().find_person_result(person)
        if existing:
            return web.json_response({'ok': False, 'error': 'participant already has result'}, status=409)

        result = race().new_result(ResultManual)
        result.person = person
        result.bib = person.bib
        race().add_new_result(result)
        Teamwork().send(result.to_dict())
        live_client.send(result)
        ResultCalculation(race()).process_results()

        return web.json_response(
            {
                'ok': True,
                'item': {
                    'bib': person.bib,
                    'name': f'{person.surname} {person.name}'.strip(),
                    'time': result.get_finish_time().to_str(),
                },
            }
        )

    async def handle_viewer_summary(self, request: web.Request):
        data = []
        for group in race().groups:
            results = [r for r in race().results if r.person and r.person.group is group]
            try:
                results = sorted(results)
            except Exception:
                pass
            rows = []
            for result in results[:6]:
                rows.append({
                    'place': result.get_place(),
                    'name': f'{result.person.surname} {result.person.name}'.strip(),
                    'organization': result.person.organization.name if result.person.organization else '',
                    'result': result.get_result(),
                })
            data.append({'group': group.name, 'rows': rows})
        return web.json_response(data)

    async def handle_viewer_group(self, request: web.Request):
        group_id = request.query.get('group_id', '')
        group = None
        for g in race().groups:
            if str(g.id) == group_id:
                group = g
                break
        if group is None and race().groups:
            group = race().groups[0]
        if group is None:
            return web.json_response({'group': '', 'rows': []})

        results = [r for r in race().results if r.person and r.person.group is group]
        try:
            results = sorted(results)
        except Exception:
            pass
        group_stages = [s for s in getattr(race(), 'tourism_stages', []) if getattr(s, 'group_id', '') == str(group.id)]
        group_stages = sorted(group_stages, key=lambda s: s.order_num)
        passages = getattr(race(), 'web_stage_passages', [])

        rows = []
        for result in results:
            stage_marks = []
            for stage in group_stages:
                marks = [p for p in passages if p.get('person_id') == str(result.person.id) and p.get('stage_id') == stage.id]
                if marks:
                    marks = sorted(marks, key=lambda p: p.get('timestamp_msec', 0))
                    stage_marks.append(f"{stage.order_num}. {marks[-1].get('timestamp_text', '')}")
            rows.append({
                'place': result.get_place(),
                'bib': result.person.bib,
                'name': f'{result.person.surname} {result.person.name}'.strip(),
                'organization': result.person.organization.name if result.person.organization else '',
                'result': result.get_result(),
                'stage_marks': ' | '.join(stage_marks),
            })
        return web.json_response({'group': group.name, 'rows': rows})

    def _read_template(self, name: str) -> str:
        path = Path(config.template_dir(name))
        return path.read_text(encoding='utf-8')

    def _find_person(self, person_id: str):
        for person in race().persons:
            if str(person.id) == person_id:
                return person
        return None

    def _find_stage(self, stage_id: str):
        for stage in getattr(race(), 'tourism_stages', []):
            if stage.id == stage_id:
                return stage
        return None
