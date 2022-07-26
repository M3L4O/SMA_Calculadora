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
        
        # self.pops = { 'v' : 1, '^' : 2, '*' : 3, '/' : 3, '+' : 4, '-' : 4 }
        self.pops = { '-' : 1, '+' : 1, '*' : 2, '/' : 2, '^' : 3, 'v' : 4 }
        
        self.mops = { '(', ')' }
        self.uops = { x for x in self.pops if self.pops[x] == 4 }
        self.bops = { x for x in self.pops if self.pops[x] < 4 }
        self.symb = { '+', '-', '.', 'e' }
        
        self.aops = self.mops | self.uops | self.bops
        
        
        # Máquina de Estados que valida os números
        Q = { 'NewNum', 'q2', 'q3', 'q4', 'q5','q6', 'q7', 'q8' }
        Σ = self.symb | {x for x in range(10)}
        δ = {('NewNum', 'RANGE1-9') : 'q3', ('NewNum', '0') : 'q2',
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
            return True if parens_cnt == 0 else False
        
        return False
    
    
    def check_valid_num(self, num : str):
        return self.NumSyntax.isValid(num)
    
    
    def parse(self, expr : str) -> tuple:
        self._parse(expr)
        if not self._verify_parse(): return None
        return self.num_stack.copy(), self.op_stack.copy()
    
    
    def parse_postfix(self, expr : str) -> str:
        if expr != self.expr and self.parse(expr) == None: return None 
        
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
        
        self.postfix = ''.join(postfix)
        
        return ''.join(postfix)
    

if __name__ == '__main__':
    ep = ExprParser()
    expr = '(1 + 2)* 3-4^ 5 - v6 '
    print(ep.parse(expr))
    print(ep.parse_postfix(expr))
    print(ep.expr)
    print(ep.check_valid_num(30), ep.check_valid_num(30.23), ep.check_valid_num(30.13e-10))