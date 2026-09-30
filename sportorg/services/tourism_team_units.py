from dataclasses import dataclass
from typing import List, Optional

from sportorg.models.memory import Person, Result, race


TOURISM_TEAM_TYPES = {
    'tourism_pair',
    'tourism_group',
}


@dataclass
class TourismTeamUnit:
    number: int
    persons: List[Person]
    result: Optional[Result]
    result_count: int = 0

    @property
    def members_text(self) -> str:
        parts = []
        for person in self.persons:
            bib = getattr(person, 'bib', '') or ''
            parts.append(f'{bib} {person.full_name}'.strip())
        return '; '.join(parts)

    @property
    def bibs_text(self) -> str:
        return ', '.join(
            str(getattr(person, 'bib', '') or '')
            for person in self.persons
            if getattr(person, 'bib', 0)
        )

    @property
    def group_name(self) -> str:
        for person in self.persons:
            if person.group:
                return person.group.name
        return ''

    @property
    def team_name(self) -> str:
        for person in self.persons:
            if person.organization:
                return person.organization.name
        return ''

    @property
    def result_bib(self) -> str:
        if self.result and self.result.person:
            return str(getattr(self.result.person, 'bib', '') or '')
        return ''

    @property
    def result_text(self) -> str:
        if self.result:
            return self.result.get_result()
        return ''

    @property
    def status_text(self) -> str:
        if self.result:
            return self.result.status.get_title()
        return ''

    @property
    def warning_text(self) -> str:
        if self.result_count > 1:
            return 'Several finishes in one tourism team'
        return ''

    @property
    def scores(self) -> int:
        if self.result:
            return int(getattr(self.result, 'scores', 0) or 0)
        return 0


def is_tourism_team_mode(obj=None) -> bool:
    obj = obj or race()
    return getattr(obj, 'competition_type', '') in TOURISM_TEAM_TYPES


def _result_by_person_id(obj=None):
    obj = obj or race()
    result_map = {}

    for result in obj.results:
        person = getattr(result, 'person', None)
        if person:
            result_map[str(person.id)] = result

    return result_map


def build_tourism_team_units(obj=None) -> List[TourismTeamUnit]:
    obj = obj or race()

    result_map = _result_by_person_id(obj)
    grouped = {}
    unassigned_persons = []

    for person in obj.persons:
        number = int(getattr(person, 'tourism_team_number', 0) or 0)
        if number <= 0:
            unassigned_persons.append(person)
            continue
        grouped.setdefault(number, []).append(person)

    units = []

    for number, persons in grouped.items():
        persons.sort(
            key=lambda p: (
                int(getattr(p, 'tourism_team_leg', 0) or 0),
                int(getattr(p, 'bib', 0) or 0),
                p.full_name,
            )
        )

        # Для связки/группы финиш должен быть один.
        # Это НЕ эстафета: участники бегут вместе и финишируют вместе.
        # Поэтому ищем любой один результат среди участников состава.
        # Если результатов несколько — показываем предупреждение в окне просмотра.
        team_results = []
        for person in persons:
            result = result_map.get(str(person.id))
            if result:
                team_results.append(result)

        result = None
        if team_results:
            # Связка/группа финиширует по последнему участнику.
            # Если система записала несколько финишей на разных членов
            # состава, в зачёт берём самый поздний.
            def finish_msec(item):
                finish = item.get_finish_time()
                return finish.to_msec() if finish else -1

            result = max(team_results, key=finish_msec)

        units.append(
            TourismTeamUnit(
                number=number,
                persons=persons,
                result=result,
                result_count=len(team_results),
            )
        )

    # Compatibility with files created before explicit tourism team numbers
    # were introduced. In pair/group modes each old participant record was a
    # complete start unit, so keep it visible using its bib as the unit number.
    if is_tourism_team_mode(obj):
        used_numbers = {unit.number for unit in units}
        next_fallback_number = max(used_numbers or {0}) + 1

        for person in unassigned_persons:
            result = result_map.get(str(person.id))
            if result is None:
                continue

            number = int(getattr(person, 'bib', 0) or 0)
            if number <= 0 or number in used_numbers:
                while next_fallback_number in used_numbers:
                    next_fallback_number += 1
                number = next_fallback_number
                next_fallback_number += 1

            used_numbers.add(number)
            units.append(
                TourismTeamUnit(
                    number=number,
                    persons=[person],
                    result=result,
                    result_count=1,
                )
            )

    units.sort(key=lambda unit: unit.number)
    return units
