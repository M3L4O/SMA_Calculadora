import time
from math import sqrt

from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from asyncio import sleep
from aioxmpp import PresenceShow

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
            pattern = "([" + r"\+\-\*\/\(\)\^v" + "])"
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
                    elif char in ("*", "+", "-", "/", "^", "v"):
                        operators.append(char)
                    else:
                        numbers.append(float(char))

            return numbers, operators

        async def calc(self, expression):

            numbers, operators = await self.scrapping(expression)
            index = 0
            # Prioriza exponenciação
            while "^" in operators or "v" in operators:
                if operators[index] in ("^", "v"):
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

            msg = Message(to=agents[operator])

            if operator != "v":
                msg.body = f"{numbers[index]} {numbers[index+1]}"
            else:
                msg.body = f"{numbers[index]}"
            msg.metadata = {"performative": "request"}
            await self.send(msg)

            response = await self.receive(timeout=5)
            # Tenta novamente caso não receba alguma resposta
            while not response:
                await self.send(msg)
                response = await self.receive(timeout=5)
            if operator != "v":
                numbers.pop(index + 1)
            operators.pop(index)
            numbers[index] = float(response.body)

        async def run(self):
            self.presence.set_available()
            for agent in agents.values():
                self.presence.subscribe(agent)
                
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


class ResponseAgent(Agent):
    class RecvBeha(CyclicBehaviour):
        def on_subscribe(self, jid):
            self.presence.approve(jid)
            self.presence.subscribe(jid)
        
        
        async def on_start(self):
            self.operation = self.get('operation')
            
            self.presence.set_available()
            self.presence.on_subscribe = self.on_subscribe
            
        
        async def run(self):
            msg = await self.receive(timeout=30)
            if msg:
                response = Message(to=str(msg.sender))
                operands = [ float(x) for x in msg.body.split() ]
                resp = self.operation(*operands)
                response.body = str(resp)
                response.metadata = {"performative": "inform"}
                await self.send(response)
                operation = operands.copy()
                operation.insert(1, self.get('op'))
                console.print(f"[bold green]Agente de {self.get('name')} >[/bold green]\n"
                              f"Recebida: {' '.join( str(x) for x in operands)}\n"
                              f"Avaliada: {' '.join( str(x) for x in operation )}\n"
                              f"Respondida: {response.body}\n")

            else:
                self.kill()

    async def setup(self):
        console.print(
            f"[green]Agente [bold red]{self.name}[/bold red] iniciado...[/green]"
        )
        recv_beha = self.RecvBeha()
        self.presence.set_available()
        self.add_behaviour(recv_beha)


if __name__ == '__main__':
    agents = {
        "*": "agent_mult@yax.im",
        "/": "agent_div@yax.im",
        "+": "agent_add@yax.im",
        "-": "agent_sub@yax.im",
        "^": "agent_exp@yax.im",
        "v": "agent_sqr@yax.im",
    }
    
    operations = {
        '*': lambda x, y : x * y,
        '/': lambda x, y : x / y,
        '+': lambda x, y : x + y,
        '-': lambda x, y : x - y,
        '^': lambda x, y : x ** y,
        'v': lambda x : sqrt(x),
    }
    
    names = {
        '*': 'multiplicação',
        '/': 'divisão',
        '+': 'soma',
        '-': 'subtração',
        '^': 'exponenciação',
        'v': 'raiz quadrada',
    }
    
    console = Console()
    op_agents = set()
    for op, jid in agents.items():
        new_agent = ResponseAgent(jid, '123456')
        
        new_agent.set('name', names[op])
        new_agent.set('jid', jid)
        new_agent.set('op', op)
        new_agent.set('operation', operations[op])
        
        fut = new_agent.start()
        op_agents.add(new_agent)
    
    fut.result()
    time.sleep(3)
    
    coord = CoordAgent('agent_coord@yax.im', '123456')
    coord.set('jid', 'agent_coord@yax.im')
    
    expression = input('Expressão: ')
    
    coord.set('agents', agents)
    coord.web.start(hostname="127.0.0.1", port=10000)
    
    fut = coord.start()
    fut.result()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        console.print("\n\n[red]Encerrando...[/red]")
    
    coord.stop()
