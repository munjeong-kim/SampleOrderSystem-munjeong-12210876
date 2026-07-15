import pytest

from src.domain.models import Sample
from src.repository.sample_repository import SampleRepository
from src.storage.json_storage import JsonStorage


def _make_repository(tmp_path):
    storage = JsonStorage(str(tmp_path / "samples.json"))
    return SampleRepository(storage)


def test_시료_생성_후_read_all로_조회된다(tmp_path):
    repository = _make_repository(tmp_path)
    sample = Sample(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=10.5,
        yield_rate=0.9,
    )

    repository.create(sample)

    assert repository.read_all() == [sample]


def test_시료_생성_후_read_one으로_조회된다(tmp_path):
    repository = _make_repository(tmp_path)
    sample = Sample(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=10.5,
        yield_rate=0.9,
    )

    repository.create(sample)

    assert repository.read_one("S-001") == sample


def test_존재하지_않는_시료_ID로_read_one하면_None을_반환한다(tmp_path):
    repository = _make_repository(tmp_path)

    assert repository.read_one("S-999") is None


def test_중복된_시료_ID로_생성하면_ValueError가_발생한다(tmp_path):
    repository = _make_repository(tmp_path)
    sample = Sample(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=10.5,
        yield_rate=0.9,
    )
    repository.create(sample)

    duplicate = Sample(
        sample_id="S-001",
        name="다른 이름",
        avg_production_time=1.0,
        yield_rate=0.5,
    )

    with pytest.raises(ValueError):
        repository.create(duplicate)


def test_저장소를_새로_생성해도_기존에_저장된_시료가_유지된다(tmp_path):
    storage = JsonStorage(str(tmp_path / "samples.json"))
    sample = Sample(
        sample_id="S-001",
        name="실리콘 웨이퍼-8인치",
        avg_production_time=10.5,
        yield_rate=0.9,
    )
    SampleRepository(storage).create(sample)

    new_repository = SampleRepository(JsonStorage(str(tmp_path / "samples.json")))

    assert new_repository.read_one("S-001") == sample
