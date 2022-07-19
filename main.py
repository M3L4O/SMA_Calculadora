from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from asyncio import sleep
import time


class CoordAgent(Agent):
    class RecvBeha(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)

            if msg:
                print(f"O resultado da {msg.body}.")

    class OperBeha(CyclicBehaviour):
        async def run(self):
            expression = "1+2"
            msg = Message(to="agent_mult@yax.im")
            msg.body = expression
            await sleep(5)
            await self.send(msg)
            print("Mensagem enviada.")

        # async def on_end(self):
        #     await self.agent.stop()

    async def setup(self):
        print("Agente coordenador iniciado.")
        op_beha = self.OperBeha()
        self.add_behaviour(op_beha)
        recv_beha = self.RecvBeha()
        self.add_behaviour(recv_beha)


class AddAgent(Agent):
    class RecvBeha(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20)
            if msg:
                response = Message(to="agent_coord@yax.im")
                response.body = f"{msg.body} é {eval(msg.body)}"
                await self.send(response)
                print("Expressão respondida")

        #     else:
        #         self.kill(0

        # async def on_end(self):
        #     await self.agent.stop()

    async def setup(self):
        print("Agente soma iniciado")
        recv_beha = self.RecvBeha()
        self.add_behaviour(recv_beha)


if __name__ == "__main__":
    add_agent = AddAgent("agent_mult@yax.im", "123456")
    add_agent.start()
    coord_agent = CoordAgent("agent_coord@yax.im", "123456")
    coord_agent.start()
    coord_agent.web.start(hostname="127.0.0.1", port=10000)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando...")
