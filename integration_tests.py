# pylint: disable=missing-class-docstring     # чтобы не быть Капитаном Очевидностью
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=line-too-long               # строки с ожидаемым выводом

"""Интеграционные тесты транслятора и машины
"""

import contextlib
import io
import logging
import os
import tempfile
import pytest
import machine
import translator


#
# Если вы меняете логику работы приложения, то запускаете тесты с ключём:
# `cd src/brainfuck && true && pytest . -v --update-goldens`

#
# - source -- исходный код на вход
# - input -- данные на ввод процессора
# - code -- машинный код на выходе из транслятора
# - output -- стандартный вывод программ
# - log -- журнал программы
@pytest.mark.golden_test("golden/*.yml")
def test_whole_by_golden(golden, caplog):
    # Установим уровень отладочного вывода на DEBUG
    caplog.set_level(logging.DEBUG)

    # Создаём временную папку для тестирования приложения.
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Готовим имена файлов для входных и выходных данных.
        source = os.path.join(tmpdirname, "source.lsp")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.json")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["input"])

        # Запускаем транслятор и собираем весь стандартный вывод в переменную
        # stdout
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target])
            print("============================================================")
            machine.main([target, input_stream])

        # Выходные данные также считываем в переменные.
        with open(target, encoding="utf-8") as file:
            code = file.read()

        # Проверяем, что ожидания соответствуют реальности.
        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        assert golden.out["log"] == caplog.text
