from pathlib import Path

from worldcup_api.services.fixtures import _live_fixture_snapshot_path


def test_live_fixture_snapshot_path_uses_nearest_data_directory(tmp_path: Path, monkeypatch) -> None:
    app_root = tmp_path / "app"
    service_file = app_root / "apps/api/src/worldcup_api/services/fixtures.py"
    service_file.parent.mkdir(parents=True)
    service_file.write_text("")
    (app_root / "data").mkdir()

    monkeypatch.delenv("LIVE_FIXTURE_SNAPSHOT", raising=False)
    monkeypatch.delenv("WORLDCUPQUANT_ROOT", raising=False)

    assert _live_fixture_snapshot_path(service_file) == app_root / "data/processed/live_fixtures.json"


def test_live_fixture_snapshot_path_honors_explicit_snapshot(monkeypatch, tmp_path: Path) -> None:
    snapshot_path = tmp_path / "live_fixtures.json"

    monkeypatch.setenv("LIVE_FIXTURE_SNAPSHOT", str(snapshot_path))

    assert _live_fixture_snapshot_path(Path(__file__)) == snapshot_path
