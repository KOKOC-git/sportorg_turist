import sys
from multiprocessing import freeze_support
from pathlib import Path

from PySide6.QtWidgets import QApplication

from sportorg import config
from sportorg.common.singleton import Singleton
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.main_window import MainWindow
from sportorg.language import generate_mo
from sportorg.models.constant import (
    PersonNames,
    RankingTable,
    Regions,
    RentCards,
    StatusComments,
)
from sportorg.services.tourism_result_calculation import patch_result_calculation


def read_optional_lines(file_path, encoding='utf-8'):
    path = Path(file_path)

    if not path.exists():
        return []

    try:
        with open(path, encoding=encoding) as f:
            return f.readlines()
    except Exception as e:
        print(str(e))
        return []


class Application(metaclass=Singleton):
    def __init__(self):
        self.argv = sys.argv
        self.app = QApplication(self.argv)
        patch_result_calculation()
        self.main_window = MainWindow(self.argv)
        GlobalAccess().set_app(self)

    def get_main_window(self):
        return self.main_window

    def run(self):
        if config.DEBUG:
            generate_mo()
        freeze_support()
        self.set_status_comments()
        self.set_names()
        self.set_regions()
        self.set_ranking()
        self.set_rent_cards()
        self.main_window.show_window()
        sys.exit(self.app.exec_())

    @staticmethod
    def set_status_comments():
        content = read_optional_lines(config.STATUS_COMMENTS_FILE)
        if content:
            StatusComments().set([x.strip() for x in content])

        default_content = read_optional_lines(config.STATUS_DEFAULT_COMMENTS_FILE)
        if default_content:
            StatusComments().set_default_statuses(default_content)

    @staticmethod
    def set_names():
        content = read_optional_lines(config.NAMES_FILE)
        if content:
            PersonNames().set([x.strip() for x in content])

    @staticmethod
    def set_regions():
        content = read_optional_lines(config.REGIONS_FILE)
        if content:
            Regions().set([x.strip() for x in content])

    @staticmethod
    def set_ranking():
        content = read_optional_lines(config.RANKING_SCORE_FILE)
        if content:
            RankingTable().set([x.strip().split(';') for x in content])

    @staticmethod
    def set_rent_cards():
        try:
            with open(config.data_dir('rent_cards.txt'), encoding='utf-8') as f:
                content = f.read()
                RentCards().set_from_text(content)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(str(e))
