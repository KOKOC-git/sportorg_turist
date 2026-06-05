import configparser
import gettext
import sys
import logging
import os
from pathlib import Path
from typing import Callable, List

from sportorg import config

logger = logging.getLogger(__name__)


def _get_conf_locale() -> str:
    conf = configparser.ConfigParser()
    try:
        conf.read(config.CONFIG_INI)
    except Exception as e:
        logger.exception(e)
        # remove incorrect config
        os.remove(config.CONFIG_INI)
    return conf.get('locale', 'current', fallback='ru_RU')


locale_current = _get_conf_locale()


def generate_mo() -> None:
    import polib

    name = config.NAME.lower()
    path = config.base_dir(config.LOCALE_DIR, locale_current, 'LC_MESSAGES', name)
    try:
        po = polib.pofile(path + '.po')
        po.save_as_mofile(path + '.mo')
    except Exception as e:
        logger.error(str(e))


if __name__ == '__main__':
    # FIXME move to another file
    logger.info('Generate mo files')
    generate_mo()



def get_languages():
    language_dirs = []

    try:
        language_dirs.append(Path(config.LOCALE_DIR))
    except Exception:
        pass

    if getattr(sys, 'frozen', False):
        base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
        language_dirs.append(base_dir / 'languages')
        language_dirs.append(Path(sys.executable).parent / 'languages')
        language_dirs.append(Path(sys.executable).parent / '_internal' / 'languages')

    language_dirs.append(Path.cwd() / 'languages')
    language_dirs.append(Path(__file__).resolve().parents[1] / 'languages')

    languages = []
    seen = set()

    for language_dir in language_dirs:
        if not language_dir.exists():
            continue

        for item in language_dir.iterdir():
            if not item.is_dir():
                continue

            mo_file = item / 'LC_MESSAGES' / 'sportorg.mo'
            po_file = item / 'LC_MESSAGES' / 'sportorg.po'

            if not mo_file.exists() and not po_file.exists():
                continue

            code = item.name
            if code in seen:
                continue

            seen.add(code)
            languages.append(code)

    if not languages:
        languages = ['en_US', 'ru_RU']

    return sorted(languages)



def locale():
    import locale as _system_locale

    def normalize_locale_code(locale_code):
        locale_code = str(locale_code or '').strip()
        locale_code = locale_code.replace('-', '_')

        if '.' in locale_code:
            locale_code = locale_code.split('.', 1)[0]

        aliases = {
            'ru': 'ru_RU',
            'ru_RU': 'ru_RU',
            'Russian_Russia': 'ru_RU',
            'rus': 'ru_RU',

            'en': 'en_US',
            'en_US': 'en_US',
            'en_GB': 'en_US',
            'English_United States': 'en_US',
            'eng': 'en_US',
        }

        return aliases.get(locale_code, locale_code)

    forced_locale = os.environ.get('SPORTORG_LANG', '').strip()

    if forced_locale:
        locale_current = forced_locale
    else:
        # First use SportOrg settings, then fallback to system locale.
        locale_current = _get_conf_locale()
        if not locale_current:
            try:
                locale_current = _system_locale.getdefaultlocale()[0]
            except Exception:
                locale_current = ''

    locale_current = normalize_locale_code(locale_current)

    locale_dirs = []

    # Обычный запуск из исходников
    locale_dirs.append(config.LOCALE_DIR)

    # Запуск из PyInstaller exe
    if getattr(sys, 'frozen', False):
        base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
        locale_dirs.append(str(base_dir / 'languages'))
        locale_dirs.append(str(Path(sys.executable).parent / 'languages'))
        locale_dirs.append(str(Path(sys.executable).parent / '_internal' / 'languages'))

    # Запуск из папки проекта
    locale_dirs.append(str(Path.cwd() / 'languages'))
    locale_dirs.append(str(Path(__file__).resolve().parents[1] / 'languages'))

    gettext_loader = getattr(gettext, 'Catalog', gettext.translation)

    for locale_dir in locale_dirs:
        try:
            cat = gettext_loader(
                config.NAME.lower(),
                locale_dir,
                languages=[locale_current],
            )
            return cat.gettext
        except FileNotFoundError:
            continue

    return gettext.NullTranslations().gettext


translate = locale()
