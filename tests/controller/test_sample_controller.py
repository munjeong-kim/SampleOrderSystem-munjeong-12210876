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


def test_이름에_검색어가_포함된_시료가_검색_결과로_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9)
    )
    repository.create(
        Sample(sample_id="S-002", name="유리 기판", avg_production_time=1.0, yield_rate=0.9)
    )
    controller = SampleController(view, repository)

    controller.search("웨이퍼")

    view.show_search_results.assert_called_once()
    results = view.show_search_results.call_args[0][0]
    assert [s.sample_id for s in results] == ["S-001"]


def test_검색어와_일치하는_시료가_없으면_안내_메시지가_출력된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9)
    )
    controller = SampleController(view, repository)

    controller.search("존재하지않는이름")

    view.show_search_results.assert_not_called()
    view.show_message.assert_called_once()
    assert "검색 결과가 없습니다" in view.show_message.call_args[0][0]


def test_검색어가_여러_시료_이름에_부분_일치하면_모두_결과에_포함된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    repository.create(
        Sample(sample_id="S-001", name="실리콘 웨이퍼-8인치", avg_production_time=1.0, yield_rate=0.9)
    )
    repository.create(
        Sample(sample_id="S-002", name="실리콘 웨이퍼-12인치", avg_production_time=1.0, yield_rate=0.9)
    )
    repository.create(
        Sample(sample_id="S-003", name="유리 기판", avg_production_time=1.0, yield_rate=0.9)
    )
    controller = SampleController(view, repository)

    controller.search("실리콘")

    results = view.show_search_results.call_args[0][0]
    assert [s.sample_id for s in results] == ["S-001", "S-002"]


def test_서브메뉴에서_1_선택시_register가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)
    mocker.patch.object(controller, "register")
    view.get_sample_menu_choice.side_effect = ["1", "0"]

    controller.run_submenu()

    controller.register.assert_called_once()


def test_서브메뉴에서_2_선택시_최초_페이지로_list_samples가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)
    mocker.patch.object(controller, "list_samples")
    view.get_sample_menu_choice.side_effect = ["2", "0"]
    view.get_page_number.return_value = 1
    view.get_list_navigation_choice.return_value = "b"

    controller.run_submenu()

    controller.list_samples.assert_called_once_with(1)


def test_목록조회_중_다음_페이지_선택시_다음_페이지로_이동한다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)
    mocker.patch.object(controller, "list_samples")
    view.get_sample_menu_choice.side_effect = ["2", "0"]
    view.get_page_number.return_value = 1
    view.get_list_navigation_choice.side_effect = ["n", "b"]

    controller.run_submenu()

    assert controller.list_samples.call_args_list == [mocker.call(1), mocker.call(2)]


def test_목록조회_중_이전_페이지_선택시_이전_페이지로_이동한다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)
    mocker.patch.object(controller, "list_samples")
    view.get_sample_menu_choice.side_effect = ["2", "0"]
    view.get_page_number.return_value = 2
    view.get_list_navigation_choice.side_effect = ["p", "b"]

    controller.run_submenu()

    assert controller.list_samples.call_args_list == [mocker.call(2), mocker.call(1)]


def test_서브메뉴에서_3_선택시_search가_호출된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)
    mocker.patch.object(controller, "search")
    view.get_sample_menu_choice.side_effect = ["3", "0"]
    view.get_search_keyword.return_value = "웨이퍼"

    controller.run_submenu()

    controller.search.assert_called_once_with("웨이퍼")


def test_서브메뉴에서_0_선택시_바로_루프가_종료된다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)
    mocker.patch.object(controller, "register")
    mocker.patch.object(controller, "list_samples")
    mocker.patch.object(controller, "search")
    view.get_sample_menu_choice.side_effect = ["0"]

    controller.run_submenu()

    controller.register.assert_not_called()
    controller.list_samples.assert_not_called()
    controller.search.assert_not_called()


def test_서브메뉴에서_잘못된_입력시_안내_메시지_출력_후_계속_진행한다(tmp_path, mocker):
    view = mocker.MagicMock()
    repository = _make_repository(tmp_path)
    controller = SampleController(view, repository)
    view.get_sample_menu_choice.side_effect = ["abc", "0"]

    controller.run_submenu()

    view.show_message.assert_called_once()
    assert "잘못된" in view.show_message.call_args[0][0]
