from sportorg.modules.tourism import (
    ResultStatus,
    StageResult,
    TourismResult,
    TourismSettings,
    calculate_team_scores,
    calculate_tourism_result,
    rank_tourism_results,
)


def test_cutoff_and_penalty_formula():
    settings = TourismSettings(penalty_unit_seconds=30)
    result = TourismResult(
        identifier="101",
        name="Иванов",
        start_seconds=10 * 3600,
        finish_seconds=10 * 3600 + 35 * 60,
        stages=[StageResult(1, penalty_points=10, cutoff_seconds=180)],
    )
    calculate_tourism_result(result, settings)
    assert result.pure_time_seconds == 35 * 60
    assert result.penalty_time_seconds == 5 * 60
    assert result.cutoff_sum_seconds == 3 * 60
    assert result.final_time_seconds == 37 * 60


def test_stage_dq_is_not_distance_dq():
    settings = TourismSettings(stage_dq_gets_place=False)
    result = TourismResult(
        identifier="102",
        name="Петров",
        start_seconds=0,
        finish_seconds=1000,
        stages=[StageResult(1, is_stage_dq=True)],
    )
    calculate_tourism_result(result, settings)
    assert result.status == ResultStatus.STAGE_DQ
    assert result.stage_dq_count == 1


def test_zero_point_team_shown_without_place():
    settings = TourismSettings(team_best_count=4, show_zero_point_teams=True, zero_point_teams_get_place=False)
    r1 = TourismResult(identifier="1", name="A", team="Команда 1", group="м_мал-дев", points=100)
    r1.place = 1
    r2 = TourismResult(identifier="2", name="B", team="Команда 2", group="м_мал-дев", points=0)
    r2.place = None
    rows = calculate_team_scores([r1, r2], settings)
    assert len(rows) == 2
    assert rows[0].place == 1
    assert rows[1].place is None
