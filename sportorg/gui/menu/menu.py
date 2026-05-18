from sportorg import config
from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.models.tourism import CompetitionType, ensure_tourism_defaults


def _default_menu_list():
    return [
        {
            'title': translate('File'),
            'actions': [
                {
                    'title': translate('New'),
                    'shortcut': 'Ctrl+N',
                    'icon': config.icon_dir('file.svg'),
                    'action': 'NewAction',
                },
                {
                    'title': translate('Save'),
                    'shortcut': 'Ctrl+S',
                    'icon': config.icon_dir('save.svg'),
                    'action': 'SaveAction',
                },
                {
                    'title': translate('Open'),
                    'shortcut': 'Ctrl+O',
                    'icon': config.icon_dir('folder.svg'),
                    'action': 'OpenAction',
                },
                {
                    'title': translate('Save As'),
                    'shortcut': 'Ctrl+Shift+S',
                    'icon': config.icon_dir('save.svg'),
                    'action': 'SaveAsAction',
                },
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Settings'),
                    'shortcut': 'Ctrl+Alt+S',
                    'icon': config.icon_dir('settings.svg'),
                    'action': 'SettingsAction',
                },
                {
                    'title': translate('Event Settings'),
                    'icon': config.icon_dir('form.svg'),
                    'action': 'EventSettingsAction',
                },
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Import'),
                    'actions': [
                        {
                            'title': translate('Import from SportOrg file'),
                            'action': 'ImportSportOrgAction',
                        },
                        {
                            'title': translate('CSV Winorient'),
                            'icon': config.icon_dir('csv.svg'),
                            'action': 'CSVWinorientImportAction',
                        },
                        {
                            'title': translate('WDB Winorient'),
                            'action': 'WDBWinorientImportAction',
                        },
                        {
                            'title': translate('Ocad txt v8'),
                            'action': 'OcadTXTv8ImportAction',
                        },
                        {
                            'title': translate('IOF xml'),
                            'action': 'IOFEntryListImportAction',
                        },
                        {
                            'title': translate('SPORTident master station CSV'),
                            'action': 'RecoverySportidentMasterCsvAction',
                        },
                        {
                            'title': translate('SportOrg SI log'),
                            'action': 'RecoverySportorgSiLogAction',
                        },
                        {
                            'title': translate('Orgeo.ru CSV'),
                            'action': 'RecoveryOrgeoFinishCsvAction',
                        },
                        {
                            'title': translate('SportOrg HTML'),
                            'action': 'RecoverySportorgHtmlAction',
                        },
                    ],
                },
                {
                    'title': translate('Export'),
                    'actions': [
                        {
                            'title': translate('WDB Winorient'),
                            'action': 'WDBWinorientExportAction',
                        },
                        {
                            'title': translate('IOF xml'),
                            'actions': [
                                {
                                    'title': translate('ResultList'),
                                    'action': 'IOFResultListExportAction',
                                },
                                {
                                    'title': translate('ResultListAllSplits'),
                                    'action': 'IOFResultListAllSplitsExportAction',
                                },
                                {
                                    'title': translate('EntrytList'),
                                    'action': 'IOFEntryListExportAction',
                                },
                                {
                                    'title': translate('CompetitorList'),
                                    'action': 'IOFCompetitorListExportAction',
                                },
                                {
                                    'title': translate('StartList'),
                                    'action': 'IOFStartListExportAction',
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            'title': translate('Edit'),
            'actions': [
                {
                    'title': translate('Add object'),
                    'tabs': list(range(5)),
                    'shortcut': ['insert', 'i'],
                    'icon': config.icon_dir('add.svg'),
                    'action': 'AddObjectAction',
                },
                {
                    'title': translate('Delete'),
                    'shortcut': 'Del',
                    'tabs': list(range(5)),
                    'icon': config.icon_dir('delete.svg'),
                    'action': 'DeleteAction',
                },
                {
                    'title': translate('Copy'),
                    'shortcut': 'Ctrl+C',
                    'tabs': list(range(5)),
                    'action': 'CopyAction',
                },
                {
                    'title': translate('Duplicate'),
                    'shortcut': 'Ctrl+D',
                    'tabs': list(range(5)),
                    'action': 'DuplicateAction',
                },
                {'title': translate('Text exchange'), 'action': 'TextExchangeAction'},
                {
                    'title': translate('Mass edit'),
                    'tabs': [0, 2, 4],
                    'action': 'MassEditAction',
                },
            ],
        },
        {
            'title': translate('View'),
            'actions': [
                {
                    'title': translate('Refresh'),
                    'icon': config.icon_dir('refresh.svg'),
                    'shortcut': 'F5',
                    'action': 'RefreshAction',
                },
                {
                    'title': translate('Filter'),
                    'shortcut': 'F2',
                    'tabs': list(range(5)),
                    'icon': config.icon_dir('filter.svg'),
                    'action': 'FilterAction',
                },
                {
                    'title': translate('Filter reset'),
                    'shortcut': 'Ctrl+F2',
                    'tabs': list(range(5)),
                    'icon': config.icon_dir('filter_reset.svg'),
                    'action': 'FilterResetAction',
                },
                {
                    'title': translate('Search'),
                    'shortcut': 'Ctrl+F',
                    'tabs': list(range(5)),
                    'icon': config.icon_dir('search.svg'),
                    'action': 'SearchAction',
                },
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Start Preparation'),
                    'shortcut': 'Ctrl+1',
                    'action': 'ToStartPreparationAction',
                },
                {
                    'title': translate('Race Results'),
                    'shortcut': 'Ctrl+2',
                    'action': 'ToRaceResultsAction',
                },
                {
                    'title': translate('Groups'),
                    'shortcut': 'Ctrl+3',
                    'action': 'ToGroupsAction',
                },
                {
                    'title': translate('Courses'),
                    'shortcut': 'Ctrl+4',
                    'action': 'ToCoursesAction',
                },
                {
                    'title': translate('Teams'),
                    'shortcut': 'Ctrl+5',
                    'action': 'ToTeamsAction',
                },
            ],
        },
        {
            'title': translate('Start Preparation'),
            'actions': [
                {
                    'title': translate('Start Preparation'),
                    'action': 'StartPreparationAction',
                },
                {'title': translate('Guess courses'), 'action': 'GuessCoursesAction'},
                {
                    'title': translate('Guess corridors'),
                    'action': 'GuessCorridorsAction',
                },
                {
                    'title': translate('Relay number assign mode'),
                    'tabs': [0],
                    'action': 'RelayNumberAction',
                },
                {
                    'title': translate('Start time change'),
                    'action': 'StartTimeChangeAction',
                },
                {
                    'title': translate('Handicap start time'),
                    'action': 'StartHandicapAction',
                },
                {'title': translate('Clone relay legs'), 'action': 'RelayCloneAction'},
                {
                    'title': translate('Use bib as card number'),
                    'action': 'CopyBibToCardNumber',
                },
                {
                    'title': translate('Use card number as bib'),
                    'action': 'CopyCardNumberToBib',
                },
                {
                    'title': translate('Marked route course generation'),
                    'action': 'MarkedRouteCourseGeneration',
                },
            ],
        },
        {
            'title': translate('Race'),
            'actions': [
                {
                    'title': translate('Manual finish'),
                    'shortcut': 'F3',
                    'icon': config.icon_dir('flag.svg'),
                    'action': 'ManualFinishAction',
                },
                {
                    'title': translate('Add SPORTident result'),
                    'action': 'AddSPORTidentResultAction',
                },
            ],
        },
        {
            'title': translate('Results'),
            'actions': [
                {
                    'title': translate('Create report'),
                    'shortcut': 'Ctrl+P',
                    'action': 'CreateReportAction',
                },
                {
                    'title': translate('Split printout'),
                    'shortcut': 'Ctrl+L',
                    'action': 'SplitPrintoutAction',
                },
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Rechecking'),
                    'shortcut': 'Ctrl+R',
                    'action': 'RecheckingAction',
                },
                {
                    'title': translate('Find group by punches'),
                    'tabs': [1],
                    'action': 'GroupFinderAction',
                },
                {
                    'title': translate('Penalty calculation'),
                    'action': 'PenaltyCalculationAction',
                },
                {
                    'title': translate('Penalty removing'),
                    'action': 'PenaltyRemovingAction',
                },
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Assign penalties / cutoff'),
                    'action': 'TourismPenaltiesAction',
                },
                {
                    'title': 'Штрафы / отсечки по этапу',
                    'action': 'TourismStagePenaltiesAction',
                },
                {
                    'title': translate('Change status'),
                    'shortcut': 'F4',
                    'tabs': [1],
                    'action': 'ChangeStatusAction',
                },
                {
                    'title': translate('Set DNS numbers'),
                    'action': 'SetDNSNumbersAction',
                },
                {'title': translate('Delete CP'), 'action': 'CPDeleteAction'},
                {'title': translate('Delete Split'), 'action': 'SplitDeleteAction'},
                {'title': translate('Merge results'), 'action': 'MergeResultsAction'},
                {
                    'title': translate('Assign result by bib'),
                    'action': 'AssignResultByBibAction',
                },
                {
                    'title': translate('Assign result by card number'),
                    'action': 'AssignResultByCardNumberAction',
                },
            ],
        },
        {
            'title': translate('Service'),
            'actions': [
                {
                    'title': translate('on/off SPORTident readout'),
                    'icon': config.icon_dir('sportident.png'),
                    'shortcut': 'F8',
                    'action': 'SPORTidentReadoutAction',
                },
                {
                    'title': translate('on/off Sportiduino readout'),
                    'icon': config.icon_dir('sportiduino.png'),
                    'action': 'SportiduinoReadoutAction',
                },
                {
                    'title': translate('on/off SFR readout'),
                    'icon': config.icon_dir('sfr.png'),
                    'action': 'SFRReadoutAction',
                },
                {
                    'title': translate('on/off RFID Impinj readout'),
                    'icon': config.icon_dir('rfid_impinj.png'),
                    'action': 'ImpinjReadoutAction',
                },
                {
                    'title': translate('on/off SRPid readout'),
                    'icon': config.icon_dir('srpid.png'),
                    'action': 'SrpidReadoutAction',
                },
                {
                    'title': translate('Teamwork'),
                    'icon': config.icon_dir('network.svg'),
                    'actions': [
                        {
                            'title': translate('Send selected'),
                            'shortcut': 'Ctrl+Shift+K',
                            'tabs': list(range(5)),
                            'action': 'TeamworkSendAction',
                        },
                        {
                            'type': 'separator',
                        },
                        {
                            'title': translate('On/Off'),
                            'action': 'TeamworkEnableAction',
                        },
                    ],
                },
                {
                    'title': translate('Telegram'),
                    'actions': [
                        {
                            'title': translate('Send results'),
                            'tabs': [1],
                            'action': 'TelegramSendAction',
                        },
                    ],
                },
                {
                    'title': translate('Online'),
                    'actions': [
                        {
                            'title': translate('Send selected'),
                            'shortcut': 'Ctrl+K',
                            'tabs': [0, 1, 2, 3, 4],
                            'action': 'OnlineSendAction',
                        },
                    ],
                },
            ],
        },
        {
            'title': translate('Options'),
            'actions': [
                {
                    'title': translate('Timekeeping settings'),
                    'icon': config.icon_dir('stopwatch.svg'),
                    'action': 'TimekeepingSettingsAction',
                },
                {
                    'title': translate('Teamwork'),
                    'icon': config.icon_dir('network.svg'),
                    'action': 'TeamworkSettingsAction',
                },
                {
                    'title': translate('Printer settings'),
                    'icon': config.icon_dir('printer.svg'),
                    'action': 'PrinterSettingsAction',
                },
                {
                    'title': translate('Live'),
                    'icon': config.icon_dir('live.svg'),
                    'action': 'LiveSettingsAction',
                },
                {
                    'title': translate('Web timing'),
                    'action': 'WebTimingAction',
                },
                {
                    'title': translate('Telegram'),
                    'action': 'TelegramSettingsAction',
                },
                {
                    'title': translate('Rent cards'),
                    'action': 'RentCardsAction',
                },
            ],
        },
        {
            'title': translate('Help'),
            'actions': [
                {
                    'title': translate('About'),
                    'shortcut': 'F1',
                    'action': 'AboutAction',
                },
                {'title': translate('Check updates'), 'action': 'CheckUpdatesAction'},
            ],
        },
    ]



def _is_tourism_mode():
    try:
        obj = race()
        ensure_tourism_defaults(obj)
        return getattr(obj, 'competition_type', CompetitionType.INDIVIDUAL.value) == CompetitionType.TOURISM.value
    except Exception:
        return False


def _filter_actions(actions, allowed_titles):
    result = []

    for action in actions:
        if action.get('type') == 'separator':
            # Разделители добавим аккуратно: только если до него уже есть пункт.
            if result and result[-1].get('type') != 'separator':
                result.append(action)
            continue

        title = action.get('title')

        if 'actions' in action:
            nested = _filter_actions(action.get('actions', []), allowed_titles)
            if nested:
                new_action = dict(action)
                new_action['actions'] = nested
                result.append(new_action)
            continue

        if title in allowed_titles:
            result.append(action)

    # Убрать хвостовой separator.
    while result and result[-1].get('type') == 'separator':
        result.pop()

    return result


def _tourism_menu_list():
    menu = _default_menu_list()

    # В туризме оставляем только пункты, которые реально нужны.
    # Всё, что относится к КП, сплитам, SPORTident-курсам, подготовке стартов
    # и проверке отметки ориентирования — скрываем.
    allowed_by_menu = {
        translate('File'): {
            translate('New'),
            translate('Save'),
            translate('Open'),
            translate('Save As'),
            translate('Settings'),
            translate('Event Settings'),
            translate('Import'),
            translate('Export'),
            translate('Import from SportOrg file'),
            translate('CSV Winorient'),
            translate('WDB Winorient'),
            translate('IOF xml'),
            translate('ResultList'),
            translate('EntrytList'),
            translate('CompetitorList'),
            translate('StartList'),
        },
        translate('Edit'): {
            translate('Add object'),
            translate('Delete'),
            translate('Copy'),
            translate('Duplicate'),
            translate('Text exchange'),
            translate('Mass edit'),
        },
        translate('View'): {
            translate('Refresh'),
            translate('Filter'),
            translate('Filter reset'),
            translate('Search'),
            translate('Start Preparation'),
            translate('Race Results'),
            translate('Groups'),
            translate('Courses'),
            translate('Teams'),
        },
        translate('Race'): {
            translate('Manual finish'),
            translate('Add SPORTident result'),
        },
        translate('Results'): {
            translate('Create report'),
            translate('Penalty calculation'),
            translate('Penalty removing'),
            translate('Assign penalties / cutoff'),
            translate('Assign penalties by stage'),
            translate('Assign stage penalties'),
            translate('Change status'),
            translate('Set DNS numbers'),
            translate('Assign result by bib'),
            translate('Assign result by card number'),
        },
        translate('Service'): {
            translate('on/off SPORTident readout'),
            translate('on/off Sportiduino readout'),
            translate('on/off SFR readout'),
            translate('on/off RFID Impinj readout'),
            translate('on/off SRPid readout'),
            translate('Teamwork'),
            translate('Send selected'),
            translate('On/Off'),
            translate('Telegram'),
            translate('Send results'),
            translate('Online'),
        },
        translate('Options'): {
            translate('Timekeeping settings'),
            translate('Teamwork'),
            translate('Printer settings'),
            translate('Live'),
            translate('Web timing'),
            translate('Telegram'),
            translate('Rent cards'),
        },
        translate('Help'): {
            translate('About'),
            translate('Check updates'),
        },
    }

    # Эти верхние меню в режиме Туризм полностью скрываем.
    hidden_top_menus = {
        translate('Start Preparation'),
    }

    filtered_menu = []

    for top in menu:
        title = top.get('title')

        if title in hidden_top_menus:
            continue

        allowed_titles = allowed_by_menu.get(title)
        if allowed_titles is None:
            continue

        new_top = dict(top)
        new_top['actions'] = _filter_actions(top.get('actions', []), allowed_titles)

        # В режиме Туризм пункт назначения штрафов по одному этапу
        # должен быть доступен в меню Результаты независимо от фильтрации по названию.
        if title == translate('Results'):
            has_stage_penalties = any(
                action.get('action') == 'TourismStagePenaltiesAction'
                for action in new_top.get('actions', [])
                if isinstance(action, dict)
            )

            if not has_stage_penalties:
                insert_index = len(new_top['actions'])
                for i, action in enumerate(new_top['actions']):
                    if (
                        isinstance(action, dict)
                        and action.get('action') == 'TourismPenaltiesAction'
                    ):
                        insert_index = i + 1
                        break

                new_top['actions'].insert(
                    insert_index,
                    {
                        'title': translate('Assign penalties by stage'),
                        'action': 'TourismStagePenaltiesAction',
                    },
                )

        if new_top['actions']:
            filtered_menu.append(new_top)

    return filtered_menu


def menu_list():
    if _is_tourism_mode():
        return _tourism_menu_list()
    return _default_menu_list()
