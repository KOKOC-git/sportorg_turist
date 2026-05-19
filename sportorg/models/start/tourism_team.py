from sportorg.models.memory import race


TOURISM_INDIVIDUAL = 'tourism_individual'
TOURISM_PAIR = 'tourism_pair'
TOURISM_GROUP = 'tourism_group'


def is_tourism_type(value):
    return value in ('tourism', TOURISM_INDIVIDUAL, TOURISM_PAIR, TOURISM_GROUP)


def get_tourism_unit_size():
    obj = race()
    competition_type = getattr(obj, 'competition_type', '') or getattr(obj.data, 'competition_type', '')

    if competition_type == TOURISM_GROUP:
        return 4

    if competition_type == TOURISM_PAIR:
        return 2

    if competition_type == TOURISM_INDIVIDUAL:
        return 1

    # Старый tourism оставляем совместимым как личную дистанцию.
    return int(obj.get_setting('tourism_team_unit_size', 1) or 1)


def get_next_tourism_team_number_protocol():
    obj = race()
    max_num = 0

    for person in obj.persons:
        cur_num = int(getattr(person, 'tourism_team_number', 0) or 0)
        if cur_num > max_num:
            max_num = cur_num

    return max_num + 1 if max_num else 1


def get_next_tourism_team_number_setting():
    obj = race()
    return int(obj.get_setting('tourism_next_team_number', get_next_tourism_team_number_protocol()) or 1)


def set_next_tourism_team_number(number):
    race().set_setting('tourism_next_team_number', int(number))


def get_current_tourism_team_fill(number):
    obj = race()
    return [
        person for person in obj.persons
        if int(getattr(person, 'tourism_team_number', 0) or 0) == int(number)
    ]


def set_next_tourism_team_number_to_person(person):
    obj = race()
    unit_size = get_tourism_unit_size()
    number = get_next_tourism_team_number_setting()

    current_members = get_current_tourism_team_fill(number)

    if len(current_members) >= unit_size:
        number += 1
        current_members = []

    leg = len(current_members) + 1

    person.tourism_team_number = int(number)
    person.tourism_team_leg = int(leg)

    if leg >= unit_size:
        set_next_tourism_team_number(number + 1)
    else:
        set_next_tourism_team_number(number)
