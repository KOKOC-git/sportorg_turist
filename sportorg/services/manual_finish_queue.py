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
    arrival_order = max(
        (
            int(existing.get('arrival_order', 0) or 0)
            for existing in race_obj.pending_manual_finishes
        ),
        default=0,
    ) + 1
    item = {
        'id': str(uuid.uuid4()),
        'arrival_order': arrival_order,
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
        if item.get('id') == item_id and item.get('status') == 'pending':
            race_obj.pending_manual_finishes.pop(index)
            return True
    return False


def assign_bib_to_oldest(race_obj, bib: int):
    ensure_manual_finish_queue(race_obj)

    for item in race_obj.pending_manual_finishes:
        if item.get('status') == 'pending':
            return assign_bib_to_finish(race_obj, item.get('id'), bib)

    raise ValueError('No pending manual finishes')


def assign_bib_to_finish(race_obj, item_id: str, bib: int):
    ensure_manual_finish_queue(race_obj)

    pending_item = next(
        (
            item
            for item in race_obj.pending_manual_finishes
            if item.get('id') == item_id
        ),
        None,
    )
    if pending_item is None:
        raise ValueError('Finish mark not found')

    person = race_obj.find_person_by_bib(int(bib))
    if not person:
        raise ValueError('Competitor not found')

    existing_result = race_obj.find_person_result(person)
    assigned_result = next(
        (
            result
            for result in race_obj.results
            if getattr(result, 'finish_event_id', '') == pending_item.get('id')
        ),
        None,
    )

    if pending_item.get('status') == 'assigned':
        if assigned_result is None:
            raise ValueError('Assigned finish result not found')
        if existing_result and existing_result is not assigned_result:
            raise ValueError('Competitor already has a result')

        assigned_result.person = person
        assigned_result.bib = person.bib
        pending_item['bib'] = int(bib)
        return assigned_result

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
    return result
