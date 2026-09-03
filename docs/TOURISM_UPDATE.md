# Судейство соревнований по спортивному туризму

Поддержка туризма интегрирована в основную модель SportOrg. Отдельных моделей
участников, результатов и статусов для туризма нет: расчёт работает с объектами
`Race`, `Person` и `Result`.

## Активные компоненты

- `sportorg/models/tourism.py` — дистанции, этапы и решения судей;
- `sportorg/services/tourism_result_calculation.py` — штрафы, отсечки и снятия с этапов;
- `sportorg/services/tourism_decision_updates.py` — атомарное сохранение решений судей;
- `sportorg/services/tourism_scores.py` — места и очки стартовых единиц;
- `sportorg/services/tourism_overall_standings.py` — общий командный зачёт;
- `templates/reports/tourism/` — печатные протоколы.

Расчёт результата вызывается через `TourismResultCalculator` и подключён к
штатному `ResultCalculation`. Формула для временного результата:

```text
итог = финиш - старт + штрафы + штрафные баллы × стоимость балла - отсечки
```

Снятие с этапа учитывается отдельно и не превращается автоматически в снятие
с дистанции.

## Проверка

```bash
python -m pytest tests/tourism
```

Основные сценарии расчёта проверяются в
`tests/tourism/test_tourism_result_calculation.py`, а сохранение судейских
решений — в `tests/tourism/test_tourism_decision_updates.py`.
