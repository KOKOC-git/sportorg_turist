from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from .models import ResultStatus, TourismResult, TourismSettings


@dataclass
class TeamScore:
    team: str
    group: str
    region: str = ""
    total_points: int = 0
    place: int | None = None
    counted_results: List[TourismResult] = field(default_factory=list)
    all_results: List[TourismResult] = field(default_factory=list)


def _team_group(result: TourismResult, settings: TourismSettings) -> str:
    return settings.group_map.get(result.group, result.group)


def _result_sort_for_team(result: TourismResult) -> tuple:
    # More points are better; then better place and better final time.
    place = result.place if result.place is not None else 10**9
    final_time = result.final_time_seconds if result.final_time_seconds is not None else 10**12
    return (-int(result.points or 0), place, final_time, result.name.lower())


def calculate_team_scores(results: Iterable[TourismResult], settings: TourismSettings) -> List[TeamScore]:
    grouped: Dict[Tuple[str, str], TeamScore] = {}

    for result in results:
        if not result.team:
            continue
        group = _team_group(result, settings)
        key = (result.team, group)
        score = grouped.setdefault(key, TeamScore(team=result.team, group=group, region=result.region))
        score.all_results.append(result)

    best_count = max(1, int(settings.team_best_count or 1))
    rows: List[TeamScore] = []
    for score in grouped.values():
        eligible = [
            r for r in score.all_results
            if r.status in (ResultStatus.OK, ResultStatus.STAGE_DQ)
            and r.points > 0
            and r.place is not None
        ]
        score.counted_results = sorted(eligible, key=_result_sort_for_team)[:best_count]
        score.total_points = sum(int(r.points or 0) for r in score.counted_results)
        if settings.show_zero_point_teams or score.total_points > 0:
            rows.append(score)

    rows.sort(key=lambda s: (-s.total_points, s.team.lower(), s.group.lower()))

    place = 1
    previous_points: int | None = None
    previous_place: int | None = None
    for row in rows:
        if row.total_points <= 0 and not settings.zero_point_teams_get_place:
            row.place = None
            continue
        if previous_points == row.total_points and previous_place is not None:
            row.place = previous_place
        else:
            row.place = place
            previous_place = place
            previous_points = row.total_points
        place += 1

    return rows
