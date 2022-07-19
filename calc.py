#!/usr/bin/python3.10
import re


def mult(index, operators, numbers):
    operators.pop(index)
    numbers[index] = numbers[index] * numbers[index + 1]
    numbers.pop(index + 1)


def div(index, operators, numbers):
    operators.pop(index)
    numbers[index] = numbers[index] / numbers[index + 1]
    numbers.pop(index + 1)


def add(index, operators, numbers):
    operators.pop(index)
    numbers[index] = numbers[index] + numbers[index + 1]
    numbers.pop(index + 1)


def sub(index, operators, numbers):
    operators.pop(index)
    numbers[index] = numbers[index] - numbers[index + 1]
    numbers.pop(index + 1)


def scrapping(expression):
    numbers = []
    operators = []
    child_expression = ""
    has_brackets = False
    brackets = 0
    expression = [
        element
        for element in re.split(r"([\*\-\+\/\(\)])", expression)
        if element not in ("", " ")
    ]

    for char in expression:
        if has_brackets:
            if char == ")" and brackets == 0:
                has_brackets = False
                numbers.append(calc(child_expression[:-1]))
                child_expression = ""
            else:
                child_expression += char + " "
                if char == "(":
                    brackets += 1
                elif char == ")":
                    brackets -= 1
        else:
            if char == "(":
                has_brackets = True
            elif char in ("*", "+", "-", "/"):
                operators.append(char)
            else:
                numbers.append(float(char))
    return numbers, operators


def calc(expression):
    numbers, operators = scrapping(expression)
    index = 0
    # Prioriza primeiro multiplicação e divisão
    while "*" in operators or "/" in operators:
        if operators[index] in ("*", "/"):
            funcs[operators[index]](index, operators, numbers)
        else:
            index += 1

    # Soluciona as demais operações
    while len(operators) > 0:
        funcs[operators[0]](0, operators, numbers)

    return numbers[0]


def main():
    expression = input(
        "Digite a expressão separada por espaço pq to com preguiça de separar:\n~ "
    )
    print(f"{expression} = {calc(expression):.2f}")


funcs = {"*": mult, "/": div, "+": add, "-": sub}
if __name__ == "__main__":
    main()
