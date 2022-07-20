from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from asyncio import sleep
import re
import time


class CoordAgent(Agent):
    class OperBeha(OneShotBehaviour):
        agents = {
            "*": "agent_mult@yax.im",
            "/": "agent_div@yax.im",
            "+": "agent_add@yax.im",
            "-": "agent_sub@yax.im",
        }

        def scrapping(self, expression):
            numbers = []
            operators = []
            child_expression = ""
            has_brackets = False
            brackets = 0
            expression = [
                element
                for element in re.split(r"([\*\-\+\/\(\)\^])", expression)
                if element not in ("", " ")
            ]

            for char in expression:
                if has_brackets:
                    if char == ")" and brackets == 0:
                        has_brackets = False
                        numbers.append(self.calc(child_expression[:-1]))
                        child_expression = ""
                    else:
                        child_expression += char
                        if char == "(":
                            brackets += 1
                        elif char == ")":
                            brackets -= 1
                else:
                    if char == "(":
                        has_brackets = True
                    elif char in ("*", "+", "-", "/", "^"):
                        operators.append(char)
                    else:
                        numbers.append(float(char))

            return numbers, operators

        async def calc(self, expression):
            numbers, operators = self.scrapping(expression)
            index = 0
            # Prioriza exponenciação
            while "^" in operators:
                if operators[index] == "^":
                    await self.send_expression(index, operators, numbers)
                else:
                    index += 1

            index = 0
            # Solucina multiplicação e divisão
            while "*" in operators or "/" in operators:
                if operators[index] in ("*", "/"):
                    await self.send_expression(index, operators, numbers)
                else:
                    index += 1
            # Soluciona as demais operações
            while len(operators) > 0:
                await self.send_expression(0, operators, numbers)

            return numbers[0]

        async def send_expression(self, index, operators, numbers):
            msg = Message(to=self.agents[operators[index]])
            msg.body = f"{numbers[index]}{operators[index]}{numbers[index+1]}"
            await self.send(msg)

            response = await self.receive(timeout=5)
            while not response:
                await self.send(msg)
                response = await self.receive(timeout=5)
            numbers.pop(index + 1)
            operators.pop(index)
            numbers[index] = float(response.body)

        async def run(self):
            resultado = await self.calc(expression)
            print(f"O resultado da {expression} é {resultado}")
            await sleep(10)

    async def setup(self):
        print("Agente coordenador iniciado.")
        op_beha = self.OperBeha()
        self.add_behaviour(op_beha)


class ResponseAgent(Agent):
    class RecvBeha(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if msg:
                response = Message(to="agent_coord@yax.im")
                response.body = f"{eval(msg.body)}"
                await self.send(response)
                print(f"Recebida: {msg.body}\t Respondida: {response.body}")
                print("Expressão respondida")

            else:
                self.kill()

    async def setup(self):
        print("Agente response iniciado")
        recv_beha = self.RecvBeha()
        self.add_behaviour(recv_beha)


if __name__ == "__main__":
    expression = input("Digite a expressão:\n~ ")
    add_agent = ResponseAgent("agent_add@yax.im", "123456")
    add_agent.start()
    mult_agent = ResponseAgent("agent_mult@yax.im", "123456")
    mult_agent.start()
    div_agent = ResponseAgent("agent_div@yax.im", "123456")
    div_agent.start()
    sub_agent = ResponseAgent("agent_sub@yax.im", "123456")
    sub_agent.start()
    coord_agent = CoordAgent("agent_coord@yax.im", "123456")
    coord_agent.start()
    coord_agent.web.start(hostname="127.0.0.1", port=10000)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando...")
