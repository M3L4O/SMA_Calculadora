from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from asyncio import sleep
import re
from rich.console import Console


class CoordAgent(Agent):
    class OperBeha(OneShotBehaviour):
        async def scrapping(self, expression):
            numbers = []
            operators = []
            child_expression = ""
            has_brackets = False
            brackets = 0
            pattern = "([" + r"\+\-\*\/\(\)\^" + "])"
            expression = [
                element
                for element in re.split(pattern, expression.replace(" ", ""))
                if element not in ("", " ")
            ]
            for char in expression:
                if has_brackets:
                    if char == ")" and brackets == 0:
                        has_brackets = False
                        numbers.append(await self.calc(child_expression))
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

            numbers, operators = await self.scrapping(expression)
            index = 0
            # Prioriza exponenciação
            while "^" in operators:
                if operators[index] == "^":
                    await self.send_request(index, operators, numbers)
                else:
                    index += 1

            index = 0
            # Solucina multiplicação e divisão
            while "*" in operators or "/" in operators:
                if operators[index] in ("*", "/"):
                    await self.send_request(index, operators, numbers)
                else:
                    index += 1
            # Soluciona as demais operações
            while len(operators) > 0:
                await self.send_request(0, operators, numbers)

            return numbers[0]

        async def send_request(self, index, operators, numbers):
            operator = operators[index]

            msg = Message(to=AGENTS[operator])

            msg.body = f"{numbers[index]}{operator}{numbers[index+1]}"
            msg.metadata = {"performative": "request"}
            await self.send(msg)

            response = await self.receive(timeout=5)
            # Tenta novamente caso não receba alguma resposta
            while not response:
                await self.send(msg)
                response = await self.receive(timeout=5)
            numbers.pop(index + 1)
            operators.pop(index)
            numbers[index] = float(response.body)

        async def run(self):
            resultado = await self.calc(expression)
            console.print(f"O resultado da {expression} é {resultado}")
            await sleep(10)
            self.kill()

    async def setup(self):
        console.print(
            f"[blue]Agente [bold green]{self.name}[/bold green] iniciado...[/blue]"
        )
        op_beha = self.OperBeha()
        self.add_behaviour(op_beha)
        self.presence.set_available()
        for agent in AGENTS.values():
            self.presence.subscribe(agent)


class ResponseAgent(Agent):
    class RecvBeha(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=30)
            if msg:
                response = Message(to="agent_coord@yax.im")
                expr = msg.body.replace("^", "**")
                response.body = f"{eval(expr)}"
                response.metadata = {"performative": "inform"}
                await self.send(response)
                console.print(f"Recebida: {msg.body}\t Respondida: {response.body}")

            else:
                self.kill()

    async def setup(self):
        console.print(
            f"[green]Agente [bold red]{self.name}[/bold red] iniciado...[/green]"
        )
        recv_beha = self.RecvBeha()
        self.add_behaviour(recv_beha)


if __name__ == "__main__":
    AGENTS = {
        "*": "agent_mult@yax.im",
        "/": "agent_div@yax.im",
        "+": "agent_add@yax.im",
        "-": "agent_sub@yax.im",
        "^": "agent_exp@yax.im",
    }
    console = Console()
    expression = input("Digite a expressão:\n~ ")
    add_agent = ResponseAgent(AGENTS["+"], "123456")
    add_agent.start()
    mult_agent = ResponseAgent(AGENTS["*"], "123456")
    mult_agent.start()
    div_agent = ResponseAgent(AGENTS["/"], "123456")
    div_agent.start()
    sub_agent = ResponseAgent(AGENTS["-"], "123456")
    sub_agent.start()
    exp_agent = ResponseAgent(AGENTS["^"], "123456")
    exp_agent.start()

    coord_agent = CoordAgent("agent_coord@yax.im", "123456")
    coord_agent.start()
    coord_agent.web.start(hostname="127.0.0.1", port=10000)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        console.print("\n\n[red]Encerrando...[/red]")
