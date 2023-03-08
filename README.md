# Лабораторная работа по Архитектуре Компьютера №3
- Ситкевич Валерий Андреевич, P33121
- `lisp | acc | harv | hw | instr | struct | stream | port | prob1`

## Язык программирования

- Lisp. Синтаксис - S-expressions. Любое выражение -- expression
- В S-expressions сначала вычисляется первый аргумент, потом второй, а потом сама функция
- Переменные имеют глобальную область видимости
- Язык имеет динамическую типизацию

### Синтаксис языка lisp
Синтаксис языка Лисп в форме Бэкуса — Наура определяется следующим образом:
``` ebnf
program ::= s-expression* comment
comment ::= ";" <any symbols>
s_expression ::= atom / list
list ::= "(" function args ")"
function ::= "setq" / "read" / "print" / "loop" / "if" / "return" 
    / "+" / "-" / ">" / "<" / "=" / "mod"
args ::= s_expression s_expression s_expression
atom ::= empty / word / number / var_name

word ::= '"' [a-z A-Z 1-9 \s]+ '"'
var_name ::= [a-zA-Z1-9]+
number ::= [-]?[0-9]+
empty ::=             
```

## Организация памяти
### Память команд 
- Реализуется списком словарей, описывающих инструкции (одно слово -- одна ячейка).
### Память данных
- Машинное слово -- 32 бит, знаковое. Линейное адресное пространство. Реализуется списком чисел.
- Переменные и константы определяются через setq, разницы в хранении констант и переменных нет.
- В памяти данных сначала хранятся строки, затем буферы размером 100 ячеек, в которые сохраняется ввод, потом переменные с константами (у каждой переменной 2 ячейки, 1я - тип переменной числом, 2я - сама переменная), в конце промежуточные результаты выполнения.
- Виды адресации: прямая абсолютная, косвенная относительная, прямая загрузка.

```text
   Instruction memory
+---------------------------------------+
| 00  : load 1st char of 1st string     |
| 01  : push it                         |
| 02  : load 2nd char of 1st string     |
| 03  : push it                         |
|    ...                                |
| n   : program start                   |
|    ...                                |
+---------------------------------------+


     Data memory
+---------------------------------------+
|    Строки                             |
+---------------------------------------+
| 00        : 1st char of 1st string    |  
| 01        : 2nd char of 1st string    |
|    ...                                |
| n         : last char of 1st string   |
| n + 1     : 0                         |
| n + 2     : 1st char of 2nd string    |
|    ...                                |
| m - 2     : last char of n string     |
| m - 1     : 0                         |
+---------------------------------------+
|    Буферы ввода                       |
+---------------------------------------+
| m         : 1st read buffer           |
|    ...                                |
| m + 100   : 2nd read buffer           |
|    ...                                |
| m + 100*k : n read buffer             |
|    ...                                |
+---------------------------------------+
|    Переменные и константы             |
+---------------------------------------+
| v         : type of var1              |
| v+1       : var1                      |
| v+2       : type of var2              |
| v+3       : var2                      |
|    ...                                |
+---------------------------------------+
|    Промежуточные результаты           |
+---------------------------------------+
| t         : type of temp var1         |
| t + 1     : temp var1                 |
|    ...                                |
+---------------------------------------+
```

## ISA (instruction set architecture)
Аккумуляторная архитектура. На левый вход ALU всегда подаётся значение из аккумулятора, результат вычисления ALU сохраняется в аккумулятор.

| OPCODE            | Описание                                  | Адресация               | ТАКТЫ |
|-------------------|-------------------------------------------|-------------------------|-------|
| load              | MEM(ARG) -> ACC                           | прямая абсолютная       | 1     |
| loadc             | ARG -> ACC                                | прямая загрузка         | 1     |
| load_indir        | MEM(MEM(ARG)) -> ACC                      | косвенная относительная | 3     |
| store             | ACC -> MEM(ARG)                           | прямая абсолютная       | 1     |
| store_indir       | ACC -> MEM(MEM(ARG))                      | косвенная относительная | 2     |
| add               | ACC + MEM(ARG) -> ACC                     | прямая абсолютная       | 1     |
| addc              | ACC + ARG -> ACC                          | прямая загрузка         | 1     |
| sub               | ACC - MEM(ARG) -> ACC                     | прямая абсолютная       | 1     |
| print / print_int | ACC -> OUT                                | -                       | 1     |
| read              | IN -> ACC                                 | -                       | 1     |
| jmp               | ARG -> IP                                 | прямая загрузка         | 1     |
| je                | IF ZERO == 1 THEN ARG -> IP               | прямая загрузка         | 1     |
| jne               | IF ZERO == 0 THEN ARG -> IP               | прямая загрузка         | 1     |
| jg                | IF ZERO == 0 AND SIGN == 0 THEN ARG -> IP | прямая загрузка         | 1     |
| jl                | IF ZERO == 0 AND SIGN == 1 THEN ARG -> IP | прямая загрузка         | 1     |
| halt              | -                                         | -                       | 0     |

### Кодирование инструкций

- Машинный код сериализуется в список JSON.
- Один элемент списка, одна инструкция.
- Индекс списка -- адрес инструкции. Используется для команд перехода.

Пример:

```json
[
    {
        "opcode": "loadc",
        "arg": 1050,
        "term": 0
    }
]
```

где:

- `opcode` -- строка с кодом операции;
- `arg` -- аргумент;
- `term` -- порядковый номер инструкции

## Транслятор Lisp
Этапы трансляции:
text → [reader] → [evaluator] → opcodes

[Объединение модулей](translator.py)

### Reader
Reader принимает на вход текст программы, удаляет комментарии, преобразует loop for в loop и возвращает s-expressions.
[Реализация](translation/reader.py)

### Evaluator
Evaluator принимает s-expressions и преобразует их в машинный код.
[Реализация](translation/evaluator.py)


## Модель процессора
Реализована в [machine.py](machine.py).

### Datapath
![Scheme](/etc/Datapath.jpg)
- `ip` -- instruction pointer (счетчик команд)

### Control Unit
![Scheme](/etc/Control_Unit.jpg)
#### Регистры
- `sr` -- storage register (сюда загружается аргумент инструкции из instruction decoder)
- `dr` -- data register
- `da` -- data address
- `acc` -- accumulator
#### Дополнительно
- `sign` -- провод, передающий первый бит из MUX
- `check if zero` -- логическая схема, которая принимает на вход все сигналы из MUX, если сигналов на входе схемы нет, то выходной сигнал есть (1) иначе сигнала нет (0)

## Апробация
В качестве тестов использовано 6 алгоритмов:
### Стандартные
1. [hello](golden/hello.yml) 
2. [cat](golden/cat.yml) 
3. [prob1](golden/prob1.yml) 
### Необходимые для демонстрации адекватной трансляции программ на lisp
1. [requirements](examples/requirements.lsp) 
2. [print loop](examples/loop.lsp) 
3. [math](examples/math.lsp) 

Интеграционные тесты реализованы тут: [integration_test](integration_test.py) :

| ФИО           | алг.  | LoC | code инстр. | инстр.   | такт.    | вариант |
|---------------|-------|-----|-------------|----------|----------|---------|
| Ситкевич В.А. | hello | 3   | 60          | 117      | 141      | lisp    |
| Ситкевич В.А. | cat   | 2   | 45          | 63       | 75       | lisp    |
| Ситкевич В.А. | prob1 | 60  | 166         | 1004088  | 1004088  | lisp    |
