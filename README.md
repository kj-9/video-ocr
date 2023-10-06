# video-ocr

[![PyPI](https://img.shields.io/pypi/v/video-ocr.svg)](https://pypi.org/project/video-ocr/)
[![Changelog](https://img.shields.io/github/v/release/kj-9/video-ocr?include_prereleases&label=changelog)](https://github.com/kj-9/video-ocr/releases)
[![Tests](https://github.com/kj-9/video-ocr/workflows/Test/badge.svg)](https://github.com/kj-9/video-ocr/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/kj-9/video-ocr/blob/master/LICENSE)



## Installation

Install this tool using `pip`:

    pip install video-ocr

## Usage

For help, run:

    video-ocr --help

You can also use:

    python -m video_ocr --help

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:

    cd video-ocr
    python -m venv venv
    source venv/bin/activate

Now install the dependencies and test dependencies:

    pip install -e '.[test,dev]'

To run the tests:

    pytest
