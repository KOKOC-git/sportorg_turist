from typing import Callable, Dict, List, Tuple

from sportorg.models.memory import Person


def _person_sort_key(person: Person):
    start_time = person.start_time.to_msec() if person.start_time else 0
    return (
        start_time,
        str(person.surname or ''),
        str(person.name or ''),
        int(getattr(person, 'bib', 0) or 0),
    )


def _group_sort_key(name: str):
    # Чтобы порядок был стабильный и понятный.
    return str(name or '').lower()


def _assign_by_key(obj, key_func: Callable[[Person], str], first_number: int, range_step: int) -> List[Tuple[str, int, int, int]]:
    persons = list(getattr(obj, 'persons', []))
    persons.sort(key=_person_sort_key)

    grouped: Dict[str, List[Person]] = {}

    for person in persons:
        key = key_func(person)
        if not key:
            key = 'Без группы'
        grouped.setdefault(key, []).append(person)

    keys = sorted(grouped.keys(), key=_group_sort_key)

    first_number = int(first_number or 1)
    range_step = int(range_step or 1)

    # Если в какой-то группе участников больше, чем шаг диапазона,
    # увеличиваем шаг, чтобы диапазоны не пересекались.
    max_group_size = max((len(grouped[key]) for key in keys), default=0)
    safe_range_step = max(range_step, max_group_size + 1)

    # Важно: сначала очищаем все номера, чтобы при массовой перенумерации
    # не было временных конфликтов со старыми номерами.
    for person in persons:
        person.set_bib(0)

    ranges = []

    for index, key in enumerate(keys):
        start_number = first_number + index * safe_range_step
        current_number = start_number

        for person in grouped[key]:
            person.set_bib(current_number)
            current_number += 1

        end_number = current_number - 1
        ranges.append((key, start_number, end_number, len(grouped[key])))

    return ranges


def assign_start_numbers_by_group(obj, first_number: int = 1, range_step: int = 100):
    return _assign_by_key(
        obj,
        lambda person: person.group.name if person.group else '',
        first_number,
        range_step,
    )


def assign_start_numbers_by_organization(obj, first_number: int = 1, range_step: int = 100):
    return _assign_by_key(
        obj,
        lambda person: person.organization.name if person.organization else '',
        first_number,
        range_step,
    )
