from pathlib import Path

from click.testing import CliRunner

from video_ocr import config
from video_ocr.cli import cli
from video_ocr.execute import (
    func_to_frames_if_not_exists,
    run_ocr_if_not_exists,
)
from video_ocr.video import Video


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


def set_data_dir():
    config.DATA_DIR = Path(__file__).parent / "data_dir"


def test_run_ocr_sync():
    runner = CliRunner()
    with runner.isolated_filesystem() as td:
        video_ids = ["_nmWquZTOMI"]
        config.DATA_DIR = Path(td)

        func_to_frames_if_not_exists(load=False)(video_ids[0])
        run_ocr_if_not_exists(video_ids[0])

        video = Video.from_json(video_ids[0])

        assert video.video_id == "_nmWquZTOMI"
        results = [frame.results for frame in video.frames]
        assert any(results)
