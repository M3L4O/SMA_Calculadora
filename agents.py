from math import sqrt
import time
import asyncio

from spade import quit_spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

class FSM:
    def __init__(self, Q : set, Σ : set, δ : dict, q0 : str, F : set) -> None:
        self.Q = Q
        self.Σ = Σ
        self.δ = δ
        self.q0 = q0
        self.F = F
        
        keys_list = [x for x in δ]
        for key in keys_list:
            if 'RANGE' in key[1]:
                vals = key[1].replace('RANGE', '').split('-')
                δ.update({(key[0], chr(el)) : δ[key] for el in range(ord(vals[0]), ord(vals[1]) + 1)})
                δ.pop(key)
            if 'OR' in key[1]:
                vals = key[1].split('OR')
                δ.update({(key[0], el) : δ[key] for el in vals})
                δ.pop(key)
    
    
    def isValid(self, word : str) -> bool:
        q = self.q0
        for c in str(word):
            q = self.δ.get((q, c), None)
            if q == None: return False
        
        return q in self.F

class ExprParser:
    def __init__(self) -> None:
        self.expr = ''
        self.num_stack = []
        self.op_stack = []
        self.tok_stack = []
        self.postfix = []
        
        self.pops = { '-' : 1, '+' : 1, '*' : 2, '/' : 2, '^' : 3, 'v' : 4 }
        
        self.mops = { '(', ')' }
        self.uops = { x for x in self.pops if self.pops[x] == 4 }
        self.bops = { x for x in self.pops if self.pops[x] < 4 }
        self.symb = { '+', '-', '.', 'e' }
        
        self.aops = self.mops | self.uops | self.bops
        
        self._isValidExpr = False
        
        
        # Máquina de Estados que valida os números
        Q = { 'NewNum', 'q1', 'q2', 'q3', 'q4', 'q5','q6', 'q7', 'q8' }
        Σ = self.symb | {x for x in range(10)}
        δ = {('NewNum', '-') : 'q1', ('NewNum', 'RANGE1-9') : 'q3', ('NewNum', '0') : 'q2',
                ('q1', '0') : 'q2', ('q1', 'RANGE1-9') : 'q3',
                ('q2', '.') : 'q4', ('q2', 'e') : 'q6', 
                ('q3', 'RANGE0-9') : 'q3', ('q3', '.') : 'q4', ('q3', 'e') : 'q6',
                ('q4', 'RANGE0-9') : 'q5',
                ('q5', 'RANGE0-9') : 'q5', ('q5', 'e') : 'q6',
                ('q6', '+OR-') : 'q7', ('q6', 'RANGE0-9') : 'q8',
                ('q7', 'RANGE0-9') : 'q8',
                ('q8', 'RANGE0-9') : 'q8',}
        q0 = 'NewNum'
        F = { 'q2', 'q3', 'q5', 'q8' }
        
        self.NumSyntax = FSM(Q, Σ, δ, q0, F)
    
    
    def _parse(self, expr : str) -> None:
        expr = str(expr).replace(' ', '')
        
        op_stack = []
        num_stack = []
        tok_stack = []
        num_buffer = []
        
        ectrl = True
        for c in expr:
            if c in self.aops and ectrl:
                if num_buffer: 
                    num_stack.append(''.join(num_buffer))
                    tok_stack.append(''.join(num_buffer))
                num_buffer.clear()
                
                op_stack.append(c)
                tok_stack.append(c)
            else:
                num_buffer.append(c)
                ectrl = False if c == 'e' else True
                
        if num_buffer: 
            num_stack.append(''.join(num_buffer))
            tok_stack.append(''.join(num_buffer))
        
        self.expr = expr
        self.op_stack = op_stack
        self.num_stack = num_stack
        self.tok_stack = tok_stack
    
    
    def _verify_parse(self):
        if self.tok_stack[0] in self.num_stack or self.tok_stack[0] in self.uops | self.mops:
            numctrl = True
        else: 
            numctrl = False
        opctrl = not numctrl
        
        parens_cnt = 0
        for token in self.tok_stack:
            if numctrl and self.NumSyntax.isValid(token):
                numctrl = False
                opctrl = True
            elif opctrl and token in self.bops:
                numctrl = True
                opctrl = False
            elif token in self.uops | self.mops:
                if token == '(': parens_cnt += 1
                elif token == ')': parens_cnt -= 1
                if parens_cnt < 0:
                    break
            else:
                break
        else:
            if parens_cnt == 0: self._isValidExpr = True
            else: self._isValidExpr = False
            return self._isValidExpr
        
        self._isValidExpr = False
        return self._isValidExpr
    
    
    def check_valid_num(self, num : str):
        return self.NumSyntax.isValid(num)
    
    
    def parse(self, expr : str) -> tuple:
        if str(expr).replace(' ', '') == self.expr:
            if self._isValidExpr: return self.num_stack.copy(), self.op_stack.copy()
            else: return None
        
        self._parse(expr)
        if not self._verify_parse(): return None
        return self.num_stack.copy(), self.op_stack.copy()
    
    
    def parse_postfix(self, expr : str) -> str:
        if str(expr).replace(' ', '') != self.expr and self.parse(expr) == None: return None 
        
        postfix = []
        conv_stack = []
        
        for token in self.tok_stack:
            if token in self.num_stack:
                postfix.append(token)
            elif token == '(':
                conv_stack.append('(')
            elif token == ')':
                while len(conv_stack) and conv_stack[-1] != '(':
                    postfix.append(conv_stack.pop())
                
                if len(conv_stack):
                    if conv_stack[-1] != '(':
                        return False
                    else:
                        conv_stack.pop()
            else:
                while len(conv_stack) and \
                      self.pops.get(token) <= self.pops.get(conv_stack[-1], 0):
                    if token == '^' and conv_stack[-1] == token:
                        break
                    postfix.append(conv_stack.pop())
                conv_stack.append(token)
        
        while len(conv_stack):
            postfix.append(conv_stack.pop())
        
        self.postfix = postfix
        
        return self.postfix.copy()
    

class CoordinatorAgent(Agent):
    class RecieveBehav(CyclicBehaviour):
        async def on_start(self) -> None:
            self.expr_request = False
            self.expr_queue = []
            self.ontologies = ['solve', 'environ_request', 'request_for_expr', 'request_for_computation']
            
            self.presence.set_available()
        
        
        def _print(self, out_str : str):
            print(f'Coordinator > Receiver > ' + str(out_str))
        
        
        async def run(self):
            msg = await self.receive()
            
            if msg:
                self._print(f'\nGot mail! {msg.body}\n')
                
                if msg.metadata.get('ontology') == 'request_for_computation':
                    await self.send(msg)
                
                elif msg.metadata.get('ontology') == 'solve':
                    await self.agent.SolBehav.enqueue(msg)
                    self._print(f'Solution to solver: {msg.body}')
                    
                elif msg.metadata.get('ontology') == 'environ_request':
                    if self.expr_request:
                        self.expr_request = False
                        await self.agent.SolBehav.enqueue(msg)
                        self._print(f'Expression to solver: {msg.body}')
                        
                    else: 
                        self.expr_queue.append(msg.body)
                        
                elif msg.metadata.get('ontology') == 'request_for_expr':
                    if self.expr_queue:
                        self.expr_request = False
                        expr = Message(sender=self.get('jid'))
                        expr.body = self.expr_queue.pop(0)
                        await self.agent.SolBehav.enqueue(msg)
                        self._print(f'Expression to solver: f{expr}')
                    else: 
                        self.expr_request = True
                        
                elif msg.metadata.get('ontology') == 'end':
                    self.kill()
        
        
        async def on_end(self):
            await self.agent.stop()
    
    
    class SolveBehav(CyclicBehaviour):
        async def on_start(self) -> None:
            self.parser = ExprParser()
            
            self.curr_expr_dict = {}
            self.curr_expr_postfix = []
            self.curr_expr_postfix_save = []
            self.curr_expr = None
            
            self.busy_agents = { op : False for op in self.parser.uops | self.parser.bops }
            
            self.sends = set()
            self.recvs = set()
            
            self.eval_complete = True
            self.request_sent = False
            self.request_mail = Message(to=self.get('jid'), sender=self.get('jid'))
            self.request_mail.set_metadata('performative', 'request')
            self.request_mail.set_metadata('ontology', 'request_for_expr')
            
            self.presence.set_available()
            for jid in self.get('agents').values():
                self.presence.subscribe(jid)
            
            self._print('Solver is solv\'n!')
        
        
        def _print(self, out_str : str) -> None:
            print(f'Coordinator > Solver > ' + str(out_str))
        
        
        async def request_expr(self):
            if not self.request_sent:
                self.request_sent = True
                await self.agent.RecvBehav.enqueue(self.request_mail)
            
            msg = await self.receive(3)
            if msg is None: return None
            
            expr = msg.body
            self.curr_expr_postfix = self.parser.parse_postfix(expr)
            
            if self.curr_expr_postfix == None:
                self._print(f'Expression {msg.body} not valid. Skipping...')
                await self.agent.RecvBehav.enqueue(self.request_mail)
                return None
            
            self.curr_expr_dict['nums'], self.curr_expr_dict['ops'] = self.parser.parse(expr) 
            self.curr_expr_postfix_save = self.curr_expr_postfix
            self.curr_expr = self.parser.expr
            
            self._print(f'Expression {msg.body} received. Evaluating...')
            self.eval_complete = False
        
        
        def get_oportunities(self):
            oportunity_list = []
            
            for i in range(len(self.curr_expr_postfix)):
                if self.parser.check_valid_num(self.curr_expr_postfix[i]): continue
                
                curr_op = self.curr_expr_postfix[i]
                
                if self.parser.check_valid_num(self.curr_expr_postfix[i - 1]):
                    if curr_op in self.parser.uops and \
                        self.busy_agents[curr_op] == False:
                        self.busy_agents[curr_op] = True
                        oportunity_list.append(i)
                    elif self.parser.check_valid_num(self.curr_expr_postfix[i - 2]) and \
                        self.busy_agents[curr_op] == False:
                        self.busy_agents[curr_op] = True
                        oportunity_list.append(i)
            
            return oportunity_list
        
        
        async def send_oportunity(self, oportunity : int):
            op = self.curr_expr_postfix[oportunity]
            
            if op in self.parser.uops: op_range = [oportunity - 1, oportunity]
            else: op_range = [oportunity - 2, oportunity]
            
            msg = Message(to=self.get('agents')[op], sender=self.get('jid'))
            msg.body = ' '.join([ x for x in self.curr_expr_postfix[op_range[0] : op_range[1]] ])
            msg.set_metadata('ontology', 'request_for_computation')
            msg.set_metadata('performative', 'query')
            
            await self.agent.RecvBehav.enqueue(msg)
            
            return [ self.get('agents')[op], op_range ]
        
        
        async def run(self):
            # Verifica se há novos pedidos para resolver expressões
            if self.eval_complete:
                await self.request_expr()
            
            # Agente coordenador busca oportunidades de realizar operações
            if not self.eval_complete:
                oportunities = self.get_oportunities()
                
                # Agente coordenador envia as oportunidades
                expected_resps = []
                for oportunity in oportunities:
                    exp = await self.send_oportunity(oportunity)
                    expected_resps.append(exp)
                # print('OPORTUNIDADES ENVIADAS')
                # print(oportunities, self.curr_expr_postfix)
                
                # Agente coordenador verifica as respostas e atualiza listas de mudanças
                updates = []
                n_recvs = len(oportunities)
                while n_recvs > 0:
                    time.sleep(0.1)
                    msg = await self.receive(3)
                    
                    if msg:
                        for exp in expected_resps:
                            if str(msg.sender) == exp[0]:
                                exp_range = exp[1]
                                break
                        updates.append((exp_range, msg.body))
                        n_recvs -= 1
                
                # print('RESPOSTAS RECEBIDAS')
                
                # Agente aplica as mudanças na ordem reversa de índice
                updates.sort()
                print([x for x in reversed(updates)])
                print(self.curr_expr_postfix)
                for up in reversed(updates):
                    self.curr_expr_postfix[up[0][0] : up[0][1] + 1] = [ up[1] ]
                updates.clear()
                
                print('RESPOSTAS APLICADAS')
                print(self.curr_expr_postfix)
                # Agente verifica se a expressão está finalizada
                self.busy_agents = dict.fromkeys(self.busy_agents, False)
                if self.parser.check_valid_num(''.join(self.curr_expr_postfix)):
                    self._print(f'Expressão {self.curr_expr} = {self.curr_expr_postfix}.')
                    self.eval_complete = True
        
        
        async def mass_kill_instruction(self) -> None:
            self.sends = set()
            for contact in self.get('agents').values():
                msg = Message(to=contact, sender=self.get('jid'))
                msg.body('end of the line')
                msg.set_metadata('performative', 'request')
                
                send = asyncio.create_task(self.send(msg))
                self.sends.add(send)
                send.add_done_callback(self.sends.discard)
            await asyncio.gather(*(t for t in self.sends), return_exceptions=True)
        
        
        async def on_end(self) -> None:
            await self.mass_kill_instruction()
            self._print(f'Coordinator is no more...')
            self.agent.stop()
    
    
    async def setup(self):
        print(f'Agent Coordinator > Coordinator is up!')
        
        self.RecvBehav = self.RecieveBehav()
        self.add_behaviour(self.RecvBehav, Template(to=self.get('jid')))
        
        self.SolBehav = self.SolveBehav()
        self.add_behaviour(self.SolBehav, Template(to='avoid@nope'))


class OperatorAgent(Agent):
    class OperateBehav(CyclicBehaviour):
        async def on_start(self):
            self.operation = self.get('operation')
            
            self.presence.set_available()
            
            self._print(f'Operator {self.get("op")} is opera\'ing!')
        
        
        def _print(self, out_str) -> None:
            print(f'Agent {self.get("op")} > ' + str(out_str))
        
        
        async def run(self):
            msg = await self.receive()
            
            if msg:
                if msg.body == 'end of the line':
                    await self.kill(exit_code=f'Agent {self.get("op")} CoD: Message from coordinator.')
                
                operands = [ float(x) for x in msg.body.split() ]
                
                resp = self.operation(*operands)
                
                msg_back = Message(to=str(msg.sender), sender=self.get('jid'))
                msg_back.body = str(resp)
                msg_back.set_metadata('ontology', 'solve')
                msg_back.set_metadata('performative', 'inform')
                
                self._print(f'Calculating operation {self.get("op")} for {operands} results {resp}.')
                
                await self.send(msg_back)
                
                msg = None
        
        
        async def on_end(self) -> None:
            self._print(f'Goodbye, cruel world...')
            if self.exit_code: self._print('\t' + self.exit_code)
            await self.agent.stop()
    
    async def setup(self):
        print(f'Agent {self.get("op")} > Operator {self.get("op")} is up!')
        
        self.OpBehav = self.OperateBehav()
        self.add_behaviour(self.OpBehav)


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
    
    op_agents = set()
    # start_tasks = []
    for op, jid in agents.items():
        new_agent =  OperatorAgent(jid, '123456')
        new_agent.set('jid', jid)
        new_agent.set('op', op)
        new_agent.set('operation', operations[op])
        
        new_agent.start()
        # start_tasks.append(new_agent.start())
        op_agents.add(new_agent)
    # await asyncio.gather(*start_tasks)
    time.sleep(3)
    
    coord = CoordinatorAgent('agent_coord@yax.im', '123456')
    coord.set('jid', 'agent_coord@yax.im')
    coord.set('agents', agents)
    
    fut = coord.start()
    fut.result()
    coord.web.start(hostname="127.0.0.1", port=10000)
    
    time.sleep(1)
    
    expr = input('Expressão: ')
    send_flag = True
    while(True):
        try:
            if send_flag:
                msg = Message()
                msg.body = expr
                msg.set_metadata('performative', 'request')
                msg.set_metadata('ontology', 'environ_request')
                asyncio.run(coord.RecvBehav.enqueue(msg))
                send_flag = False
            
        except KeyboardInterrupt:
            expr = input('Expressão: ')
            send_flag = True
            
            if expr == 'end':
                break
    
    coord.stop()
    quit_spade()