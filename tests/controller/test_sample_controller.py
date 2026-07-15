from src.controller.sample_controller import SampleController
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage


def _make_repository(tmp_path):
    storage = JsonStorage(str(tmp_path / "samples.json"))
    return SampleRepository(storage)


def test_정상_입력_시_시료가_등록되고_성공_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    view.get_sample_registration_input.return_value = {
        "sample_id": "S-001",
        "name": "실리콘 웨이퍼-8인치",
        "avg_production_time": 10.5,
        "yield_rate": 0.9,
    }
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)

    controller.register()

    registered = repository.read_one("S-001")
    assert registered is not None
    assert registered.name == "실리콘 웨이퍼-8인치"
    assert registered.stock_quantity == 0
    view.show_message.assert_called_once()
    assert "등록" in view.show_message.call_args[0][0]


def test_중복된_시료_ID로_등록_시도하면_오류_메시지가_출력되고_계속_진행된다(tmp_path, mocker):
    view = mocker.MagicMock()
    view.get_sample_registration_input.return_value = {
        "sample_id": "S-001",
        "name": "실리콘 웨이퍼-8인치",
        "avg_production_time": 10.5,
        "yield_rate": 0.9,
    }
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)
    controller.register()
    view.show_message.reset_mock()

    controller.register()

    assert len(repository.read_all()) == 1
    view.show_message.assert_called_once()
    message = view.show_message.call_args[0][0]
    assert "이미 존재" in message or "중복" in message
