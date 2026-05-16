from datetime import date

from sportorg.gui.dialogs.dialog import (
    AdvComboBoxField,
    BaseDialog,
    ButtonField,
    CheckBoxField,
    LineField,
    NumberField,
    TimeField,
)
from sportorg.gui.dialogs.group_ranking import GroupRankingDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.constant import get_race_courses
from sportorg.models.memory import Limit, RaceType, find, race
from sportorg.models.tourism import CompetitionType, ensure_tourism_defaults
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.live.live import live_client
from sportorg.modules.teamwork.teamwork import Teamwork


class GroupEditDialog(BaseDialog):
    def __init__(self, group, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.current_object = group
        self.is_new = is_new
        # Временное поле для BaseDialog: реальная привязка хранится
        # в race().tourism_courses[*].group_ids, а не в самой группе.
        self.tourism_course = None
        time_format = 'hh:mm:ss'
        self.title = translate('Group properties')
        self.size = (450, 540)
        self.form = [
            LineField(
                title=translate('Name'),
                object=group,
                key='name',
                id='name',
                select_all=True,
            ),
            LineField(
                title=translate('Full name'),
                object=group,
                key='long_name',
            ),
            AdvComboBoxField(
                title=translate('Course'),
                object=group,
                key='course',
                id='course',
                items=get_race_courses(),
            ),
            CheckBoxField(
                label=translate('Is any course'),
                object=group,
                key='is_any_course',
                id='is_any_course',
            ),
            NumberField(
                title=translate('Min year'),
                object=group,
                key='min_year',
                id='min_year',
                minimum=0,
                maximum=date.today().year,
            ),
            NumberField(
                title=translate('Max year'),
                object=group,
                key='max_year',
                id='max_year',
                minimum=0,
                maximum=date.today().year,
            ),
            TimeField(
                title=translate('Max time'),
                object=group,
                key='max_time',
                format=time_format,
            ),
            NumberField(
                title=translate('Start corridor'),
                object=group,
                key='start_corridor',
            ),
            NumberField(
                title=translate('Order in corridor'),
                object=group,
                key='order_in_corridor',
            ),
            TimeField(
                title=translate('Start interval'),
                object=group,
                key='start_interval',
                format=time_format,
            ),
            NumberField(
                title=translate('Start fee'),
                object=group,
                key='price',
                single_step=50,
                maximum=Limit.PRICE,
            ),

            AdvComboBoxField(
                title=translate('Competition type'),
                object=group,
                key='competition_type',
                id='competition_type',
                items=self.get_competition_type_titles(),
            ),
            AdvComboBoxField(
                title='Дистанция туризма',
                object=self,
                key='tourism_course',
                id='tourism_course',
                items=self.get_tourism_course_titles(),
            ),
            AdvComboBoxField(
                title=translate('Type'),
                object=group,
                key='race_type',
                id='race_type',
                items=RaceType.get_titles(),
            ),
            CheckBoxField(
                label=translate('Rank calculation'),
                object=group.ranking,
                key='is_active',
                id='is_ranking_active',
            ),
            ButtonField(text=translate('Configuration'), id='ranking'),
        ]

    def before_showing(self) -> None:
        self.update_tourism_fields_visibility()
        self.on_is_any_course_changed()
        self.on_is_ranking_active_changed()

    def _set_field_visible(self, field_id, visible: bool):
        field = self.fields.get(field_id)
        if not field:
            return

        widgets = []

        q_item = getattr(field, 'q_item', None)
        if q_item is not None:
            widgets.append(q_item)

        q_label = getattr(field, 'q_label', None)
        if q_label is not None:
            widgets.append(q_label)

        label = getattr(field, 'label', None)
        if label is not None:
            widgets.append(label)

        title_label = getattr(field, 'title_label', None)
        if title_label is not None:
            widgets.append(title_label)

        for widget in widgets:
            if hasattr(widget, 'setVisible'):
                widget.setVisible(visible)

    def _is_tourism_mode(self) -> bool:
        group = self.current_object

        try:
            return group.get_competition_type() == CompetitionType.TOURISM.value
        except Exception:
            return getattr(race(), 'competition_type', CompetitionType.INDIVIDUAL.value) == CompetitionType.TOURISM.value

    def update_tourism_fields_visibility(self):
        is_tourism = self._is_tourism_mode()

        # Скрываем поля, которые относятся к обычному ориентированию.
        classic_orienteering_fields = [
            'course',
            'is_any_course',
            'race_type',
            'is_ranking_active',
            'ranking',
        ]

        for field_id in classic_orienteering_fields:
            self._set_field_visible(field_id, not is_tourism)

        # Поле туристской дистанции показываем только в режиме Туризм.
        self._set_field_visible('tourism_course', is_tourism)

    def on_competition_type_changed(self):
        self.update_tourism_fields_visibility()


    def get_competition_type_titles(self):
        return [
            translate('Inherit from event'),
            translate('Individual'),
            translate('Relay'),
            translate('Tourism'),
        ]

    def convert_competition_type(self, value) -> str:
        if not value:
            return translate('Inherit from event')
        mapping = {
            CompetitionType.INDIVIDUAL.value: translate('Individual'),
            CompetitionType.RELAY.value: translate('Relay'),
            CompetitionType.TOURISM.value: translate('Tourism'),
        }
        return mapping.get(value, translate('Inherit from event'))

    def parse_competition_type(self, text: str):
        mapping = {
            translate('Inherit from event'): None,
            translate('Individual'): CompetitionType.INDIVIDUAL.value,
            translate('Relay'): CompetitionType.RELAY.value,
            translate('Tourism'): CompetitionType.TOURISM.value,
        }
        return mapping.get(text)

    def get_tourism_course_titles(self):
        ensure_tourism_defaults(race())
        titles = ['']
        titles.extend([course.name for course in getattr(race(), 'tourism_courses', [])])
        return titles

    def _get_group_tourism_course(self):
        ensure_tourism_defaults(race())
        group_id = str(self.current_object.id)
        for tourism_course in getattr(race(), 'tourism_courses', []):
            group_ids = [str(x) for x in getattr(tourism_course, 'group_ids', [])]
            if group_id in group_ids:
                return tourism_course
        return None

    def convert_tourism_course(self, _) -> str:
        tourism_course = self._get_group_tourism_course()
        return tourism_course.name if tourism_course else ''

    def parse_tourism_course(self, text: str):
        ensure_tourism_defaults(race())
        if not text:
            return None
        for tourism_course in getattr(race(), 'tourism_courses', []):
            if tourism_course.name == text:
                return tourism_course
        return None

    def convert_course(self, course) -> str:
        if not course:
            return ''
        return course.name

    def convert_race_type(self, _) -> str:
        return race().get_type(self.current_object).get_title()

    def parse_course(self, text: str):
        return find(race().courses, name=text)

    def parse_race_type(self, text: str):
        selected = RaceType.get_by_name(text)
        if selected != race().data.race_type:
            return selected
        return None

    def on_competition_type_changed(self):
        if 'tourism_course' not in self.fields:
            return

        current_text = self.fields['competition_type'].q_item.currentText()
        is_tourism = current_text == translate('Tourism')

        # Если группа наследует тип от события, а событие само Туризм — тоже показываем поле.
        if current_text == translate('Inherit from event'):
            is_tourism = getattr(race(), 'competition_type', CompetitionType.INDIVIDUAL.value) == CompetitionType.TOURISM.value

        self.fields['tourism_course'].q_item.setEnabled(is_tourism)

    def on_name_changed(self):
        name = self.fields['name'].q_item.text()
        self.button_ok.setDisabled(False)
        if name and name != self.current_object.name:
            group = find(race().groups, name=name)
            if group:
                self.button_ok.setDisabled(True)

    def on_ranking_clicked(self):
        self.hide()
        GroupRankingDialog(self.current_object).exec_()
        self.show()

    def on_is_any_course_changed(self):
        if 'course' not in self.fields or 'is_any_course' not in self.fields:
            return
        self.fields['course'].q_item.setDisabled(
            self.fields['is_any_course'].q_item.isChecked()
        )

    def on_is_ranking_active_changed(self):
        if 'ranking' not in self.fields or 'is_ranking_active' not in self.fields:
            return
        self.fields['ranking'].q_item.setEnabled(
            self.fields['is_ranking_active'].q_item.isChecked()
        )

    def on_min_year_finished(self):
        self.change_year()

    def on_max_year_finished(self):
        self.change_year()

    def change_year(self):
        """
        Convert 2 digits of year to 4
        2 -> 2002
        11 -> 2011
        33 -> 1933
        56 -> 1956
        98 -> 1998
        0 -> 0 exception!
        """
        widget = self.sender()
        year = widget.value()
        if 0 < year < 100:
            cur_year = date.today().year
            new_year = cur_year - cur_year % 100 + year
            if new_year > cur_year:
                new_year -= 100
            widget.setValue(new_year)

    def apply(self):
        group = self.current_object
        if self.is_new:
            race().groups.insert(0, group)

        ensure_tourism_defaults(race())

        if 'tourism_course' in self.fields:
            selected_course = self.fields['tourism_course'].q_item.currentData()
            group_id = str(group.id)

            # Убираем группу из всех туристских дистанций,
            # чтобы одна группа не оказалась случайно в нескольких дистанциях.
            for tourism_course in getattr(race(), 'tourism_courses', []):
                tourism_course.group_ids = [
                    str(x) for x in getattr(tourism_course, 'group_ids', [])
                    if str(x) != group_id
                ]

            # Добавляем группу в выбранную туристскую дистанцию.
            if selected_course:
                for tourism_course in getattr(race(), 'tourism_courses', []):
                    if str(tourism_course.id) == str(selected_course.id):
                        tourism_course.group_ids.append(group_id)
                        break

        ResultCalculation(race()).set_rank(group)
        live_client.send(group)
        Teamwork().send(group.to_dict())
