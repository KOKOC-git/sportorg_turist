from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sportorg.common.otime import OTime
from sportorg.models.memory import ResultManual


def ensure_manual_finish_queue(race_obj) -> None:
    if not hasattr(race_obj, 'pending_manual_finishes'):
        race_obj.pending_manual_finishes = []


def add_pending_finish(
    race_obj,
    finish_time: Optional[OTime] = None,
    source: str = 'manual',
    raw: str = '',
) -> Dict[str, Any]:
    ensure_manual_finish_queue(race_obj)
    finish_time = finish_time or OTime.now()
    item = {
        'id': str(uuid.uuid4()),
        'finish_time_msec': finish_time.to_msec(),
        'status': 'pending',
        'source': str(source or 'manual'),
        'raw': str(raw or ''),
    }
    race_obj.pending_manual_finishes.append(item)
    return item


def get_pending_items(race_obj) -> List[Dict[str, Any]]:
    ensure_manual_finish_queue(race_obj)
    return list(race_obj.pending_manual_finishes)


def remove_last_pending(race_obj) -> Optional[Dict[str, Any]]:
    ensure_manual_finish_queue(race_obj)
    for index in range(len(race_obj.pending_manual_finishes) - 1, -1, -1):
        item = race_obj.pending_manual_finishes[index]
        if item.get('status') == 'pending':
            return race_obj.pending_manual_finishes.pop(index)
    return None


def remove_pending_by_id(race_obj, item_id: str) -> bool:
    ensure_manual_finish_queue(race_obj)
    for index, item in enumerate(race_obj.pending_manual_finishes):
        if item.get('id') == item_id:
            race_obj.pending_manual_finishes.pop(index)
            return True
    return False


def assign_bib_to_oldest(race_obj, bib: int):
    ensure_manual_finish_queue(race_obj)

    pending_item = None
    for item in race_obj.pending_manual_finishes:
        if item.get('status') == 'pending':
            pending_item = item
            break

    if pending_item is None:
        raise ValueError('No pending manual finishes')

    person = race_obj.find_person_by_bib(int(bib))
    if not person:
        raise ValueError('Competitor not found')

    existing_result = race_obj.find_person_result(person)
    if existing_result:
        raise ValueError('Competitor already has a result')

    result = race_obj.new_result(ResultManual)
    result.person = person
    result.bib = person.bib
    result.finish_time = OTime(msec=int(pending_item['finish_time_msec']))
    result.finish_event_id = str(pending_item.get('id', ''))
    result.finish_source = str(pending_item.get('source', 'manual'))
    result.finish_raw = str(pending_item.get('raw', ''))
    race_obj.add_new_result(result)

    pending_item['status'] = 'assigned'
    pending_item['bib'] = int(bib)
    race_obj.pending_manual_finishes = [
        item
        for item in race_obj.pending_manual_finishes
        if item.get('id') != pending_item.get('id')
    ]
    return result
