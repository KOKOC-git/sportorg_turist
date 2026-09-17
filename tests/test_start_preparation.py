from sportorg.models.memory import Person
from sportorg.models.start.start_preparation import DrawManager


def test_draw_accepts_persons_without_group():
    persons = [Person() for _ in range(3)]
    for number, person in enumerate(persons, start=1):
        person.set_bib(number)

    result = DrawManager(None).process_array(
        persons, split_start_groups=False, split_teams=False, split_regions=False
    )

    assert len(result) == len(persons)
    assert {person.bib for person in result} == {1, 2, 3}
