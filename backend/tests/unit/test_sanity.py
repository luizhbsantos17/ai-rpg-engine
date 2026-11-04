"""Teste mínimo: confirma que o pytest roda e que o pacote `app` é importável."""

import sys

import app


def test_python_version_is_supported():
    assert sys.version_info >= (3, 12)


def test_app_package_is_importable():
    assert app.__version__ == "0.1.0"
