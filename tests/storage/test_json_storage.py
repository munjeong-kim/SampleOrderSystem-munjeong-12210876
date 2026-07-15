import glob
import json
import os

from src.storage.json_storage import JsonStorage


def test_파일이_없을_때_load는_빈_리스트를_반환한다(tmp_path):
    file_path = tmp_path / "data.json"
    storage = JsonStorage(str(file_path))

    assert storage.load() == []


def test_save_후_load하면_저장한_데이터가_그대로_반환된다(tmp_path):
    file_path = tmp_path / "data.json"
    storage = JsonStorage(str(file_path))
    data = [{"sample_id": "S-001", "name": "실리콘 웨이퍼-8인치"}]

    storage.save(data)

    assert storage.load() == data


def test_save_시_임시_파일이_남지_않고_실제_파일만_남는다(tmp_path):
    file_path = tmp_path / "data.json"
    storage = JsonStorage(str(file_path))

    storage.save([{"a": 1}])

    files = os.listdir(tmp_path)
    assert files == ["data.json"]
    assert glob.glob(str(tmp_path / "*.tmp")) == []


def test_파일_내용이_비어있으면_load는_빈_리스트를_반환한다(tmp_path):
    file_path = tmp_path / "data.json"
    file_path.write_text("", encoding="utf-8")
    storage = JsonStorage(str(file_path))

    assert storage.load() == []


def test_save는_os_replace를_사용해_원자적으로_저장한다(mocker):
    storage = JsonStorage("dummy_path.json")
    mock_replace = mocker.patch("src.storage.json_storage.os.replace")
    mocker.patch("builtins.open", mocker.mock_open())

    storage.save([{"a": 1}])

    assert mock_replace.called
    args, _ = mock_replace.call_args
    assert args[1] == "dummy_path.json"
    assert args[0].startswith("dummy_path.json.")
    assert args[0].endswith(".tmp")


def test_save_중_예외_발생_시_임시_파일을_정리한다(tmp_path, mocker):
    file_path = tmp_path / "data.json"
    storage = JsonStorage(str(file_path))
    mocker.patch("src.storage.json_storage.json.dump", side_effect=RuntimeError("boom"))

    try:
        storage.save([{"a": 1}])
    except RuntimeError:
        pass

    assert glob.glob(str(tmp_path / "*.tmp")) == []
    assert not file_path.exists()
