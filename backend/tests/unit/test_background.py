"""Tarefas pós-turno: fora dos testes rodam em outra linha de execução; um erro só vai para o log."""

import logging
import threading

from app.config import load_settings
from app.services.background import run_in_background


def settings_for(app_env, tmp_path):
    return load_settings(environ={"APP_ENV": app_env, "DATA_DIR": str(tmp_path)}, env_file=None)


def test_runs_in_another_thread_outside_tests(tmp_path):
    done = threading.Event()
    seen = []

    def task():
        seen.append(threading.current_thread().name)
        done.set()

    run_in_background(settings_for("development", tmp_path), task, "tarefa-teste", "falhou")
    assert done.wait(5)
    assert seen == ["tarefa-teste"]


def test_failure_is_logged_not_raised(tmp_path, caplog):
    finished = threading.Event()

    def task():
        try:
            raise OSError("disco cheio")
        finally:
            finished.set()

    with caplog.at_level(logging.ERROR, logger="app.services.background"):
        run_in_background(settings_for("development", tmp_path), task, "tarefa-falha", "Cópia falhou.")
        assert finished.wait(5)
        for thread in threading.enumerate():
            if thread.name == "tarefa-falha":
                thread.join(5)
    assert "Cópia falhou." in caplog.text


def test_runs_immediately_in_tests(tmp_path):
    seen = []
    run_in_background(settings_for("test", tmp_path), lambda: seen.append(threading.current_thread().name), "x", "y")
    assert seen == [threading.current_thread().name]
