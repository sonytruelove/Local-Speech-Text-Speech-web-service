"""espeak-ng (внутри Piper) не открывает файлы данных по не-ASCII пути на
Windows — регрессия, пойманная реальным smoke-тестом (Stage 5: этот проект
сам лежит под кириллическим путём). Живой прогон через настоящий HTTP-сервер
поймал и ВТОРУЮ, более коварную регрессию: на машине уже была посторонняя
директория `LOCALAPPDATA/espeak-ng-data` (от другого espeak-ng), и функция
приняла её за свой кэш по имени файла — синтез молча падал на 0 фонемах,
без исключения. ascii_safe_espeak_data_dir теперь (а) кэширует под своей
подпапкой, (б) метит копию собственным маркер-файлом, чтобы не спутать её
с чужой директорией. Тесты проверяют оба свойства без реального piper.
"""

from pathlib import Path

from app.tts import ascii_safe_espeak_data_dir


def _make_bundled_dir(root: Path) -> Path:
    bundled = root / "bundled"
    bundled.mkdir(parents=True)
    (bundled / "phontab").write_bytes(b"fake-phontab-data")
    return bundled


def test_ascii_path_is_returned_unchanged(tmp_path):
    ascii_bundled = _make_bundled_dir(tmp_path / "ascii_dir")
    result = ascii_safe_espeak_data_dir(ascii_bundled, cache_root=tmp_path / "cache")

    assert result == ascii_bundled
    assert not (tmp_path / "cache").exists()


def test_non_ascii_path_is_copied_into_own_app_subfolder(tmp_path):
    non_ascii_root = tmp_path / "Малые ИИ"
    bundled = _make_bundled_dir(non_ascii_root)
    cache_root = tmp_path / "cache"

    result = ascii_safe_espeak_data_dir(bundled, cache_root=cache_root)

    # Не голое cache_root/espeak-ng-data — своя подпапка, чтобы не столкнуться
    # с посторонней директорией с тем же общим именем (см. docstring модуля).
    assert result == cache_root / "voice-echo-service" / "espeak-ng-data"
    assert (result / "phontab").read_bytes() == b"fake-phontab-data"


def test_copy_happens_only_once_cache_is_reused(tmp_path):
    non_ascii_root = tmp_path / "Малые ИИ"
    bundled = _make_bundled_dir(non_ascii_root)
    cache_root = tmp_path / "cache"

    first_result = ascii_safe_espeak_data_dir(bundled, cache_root=cache_root)

    # Меняем бандл после первого копирования — если бы функция копировала
    # повторно, это отразилось бы во втором результате.
    (bundled / "phontab").write_bytes(b"changed-after-first-copy")

    second_result = ascii_safe_espeak_data_dir(bundled, cache_root=cache_root)

    assert second_result == first_result
    assert (second_result / "phontab").read_bytes() == b"fake-phontab-data"


def test_pre_existing_unrelated_directory_at_cache_path_is_not_treated_as_valid(
    tmp_path,
):
    """Регрессия из реального прогона: на диске уже мог существовать каталог
    с тем же именем (от другого espeak-ng), но БЕЗ нашего маркера и с другими
    (неполными) данными. Функция обязана распознать, что это не наша копия,
    и перезаписать её полным bundled-набором, а не молча довериться чужому
    файлу с совпадающим именем "phontab"."""
    non_ascii_root = tmp_path / "Малые ИИ"
    bundled = _make_bundled_dir(non_ascii_root)
    cache_root = tmp_path / "cache"

    foreign_dir = cache_root / "voice-echo-service" / "espeak-ng-data"
    foreign_dir.mkdir(parents=True)
    (foreign_dir / "phontab").write_bytes(b"unrelated-foreign-data-not-ours")

    result = ascii_safe_espeak_data_dir(bundled, cache_root=cache_root)

    assert (result / "phontab").read_bytes() == b"fake-phontab-data"
