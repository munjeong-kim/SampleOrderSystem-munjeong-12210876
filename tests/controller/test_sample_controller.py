from src.domain.models import Sample
from src.controller.sample_controller import SampleController
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage


def _make_repository(tmp_path):
    storage = JsonStorage(str(tmp_path / "samples.json"))
    return SampleRepository(storage)


def _create_samples(repository, count):
    for i in range(1, count + 1):
        repository.create(
            Sample(
                sample_id=f"S-{i:03d}",
                name=f"시료-{i}",
                avg_production_time=1.0,
                yield_rate=0.9,
            )
        )


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


def test_시료가_5개_이하면_1페이지에_모두_표시되고_총_페이지는_1이다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    _create_samples(repository, 3)
    controller = SampleController(view, repository)

    controller.list_samples(page=1)

    view.show_sample_list.assert_called_once()
    args, kwargs = view.show_sample_list.call_args
    samples, page, total_pages = args
    assert [s.sample_id for s in samples] == ["S-001", "S-002", "S-003"]
    assert page == 1
    assert total_pages == 1


def test_시료가_7개면_1페이지에_5개_2페이지에_2개가_표시되고_총_페이지는_2다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    _create_samples(repository, 7)
    controller = SampleController(view, repository)

    controller.list_samples(page=1)
    samples, page, total_pages = view.show_sample_list.call_args[0]
    assert [s.sample_id for s in samples] == [f"S-{i:03d}" for i in range(1, 6)]
    assert page == 1
    assert total_pages == 2

    controller.list_samples(page=2)
    samples, page, total_pages = view.show_sample_list.call_args[0]
    assert [s.sample_id for s in samples] == ["S-006", "S-007"]
    assert page == 2
    assert total_pages == 2


def test_등록된_시료가_없으면_안내_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)

    controller.list_samples(page=1)

    view.show_sample_list.assert_not_called()
    view.show_message.assert_called_once()
    assert "등록된 시료가 없습니다" in view.show_message.call_args[0][0]


def test_존재하지_않는_페이지_요청_시_안내_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    _create_samples(repository, 3)
    controller = SampleController(view, repository)

    controller.list_samples(page=2)

    view.show_sample_list.assert_not_called()
    view.show_message.assert_called_once()
    assert "존재하지 않는 페이지입니다" in view.show_message.call_args[0][0]
