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
        self.uops = { '^', 'v' }
        self.bops1 = { '*', '/' }
        self.bops2 = { '+', '-' }
        self.mops = { '(', ')' }
        self.symb = { '+', '-', '.', 'e' }
        
        self.gops = self.uops | self.bops1 | self.bops2 | self.mops
        
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
        
        self.op_stack = []
        self.num_stack = []
        num_buffer = []
        
        ectrl = True
        for c in expr:
            if c in self.gops and ectrl:
                if num_buffer: self.num_stack.append(''.join(num_buffer))
                num_buffer.clear()
                self.op_stack.append(c)
            else:
                num_buffer.append(c)
                ectrl = False if c == 'e' else True
                
        if num_buffer: self.num_stack.append(''.join(num_buffer))
    
    
    def _verify_parse(self):
        for num in self.num_stack:
            if not self.NumSyntax.isValid(num): return False
        
        parens_stack = 0
        for op in self.op_stack:
            if op == '(': parens_stack = parens_stack + 1
            elif op == ')': parens_stack = parens_stack - 1
            elif op not in self.gops: return False
            
            if parens_stack < 0: return False
        
        return True
    
    
    def parse(self, expr : str) -> tuple:
        self._parse(expr)
        if not self._verify_parse(): return None
        return self.num_stack.copy(), self.op_stack.copy()
    

if __name__ == '__main__':
    ep = ExprParser()
    print(ep.parse('133 + 320e+10* (32-10^ 5 - v10 )'))