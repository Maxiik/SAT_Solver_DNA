import subprocess
import itertools
from argparse import ArgumentParser
import sys

# ==========================================
# 1. KONŠTANTY A NASTAVENIA
# ==========================================
length = 8
alphabet = 4

# ==========================================
# 2. LOGICKÉ FUNKCIE (Tvoje, sú správne)
# ==========================================
def get_var(w, i, c):
    return (w * length * alphabet) + (i * alphabet) + c + 1

def add_at_most_k(cnf, variables, k):
    """Zakáže všetky kombinácie veľkosti k+1."""
    for combo in itertools.combinations(variables, k + 1):
        clause = [-x for x in combo] + [0]
        cnf.append(clause)

def add_clause(cnf, literals):
    cnf.append(literals + [0])

def encode(K):
    """Vygeneruje CNF formulu pre hľadanie K slov."""
    cnf = []
    
    # Počet základných premenných
    basic_vars_count = K * length * alphabet
    # Pomocné premenné začínajú hneď za základnými
    next_aux_var = basic_vars_count + 1

    # --- 1. FYZIKA ---
    for w in range(K):
        for i in range(length):
            vars_pos = [get_var(w, i, c) for c in range(alphabet)]
            add_clause(cnf, vars_pos)       # Aspoň jeden
            add_at_most_k(cnf, vars_pos, 1) # Najviac jeden

    # --- 2. GC-CONTENT ---
    for w in range(K):
        cg_vars = []
        at_vars = []
        for i in range(length):
            cg_vars.append(get_var(w, i, 1)) # C
            cg_vars.append(get_var(w, i, 2)) # G
            at_vars.append(get_var(w, i, 0)) # A
            at_vars.append(get_var(w, i, 3)) # T
        add_at_most_k(cnf, cg_vars, 4)
        add_at_most_k(cnf, at_vars, 4)

    # --- 3. HAMMINGOVA VZDIALENOSŤ ---
    for w1 in range(K):
        for w2 in range(w1 + 1, K):
            match_vars = []
            for i in range(length):
                m_var = next_aux_var
                next_aux_var += 1
                match_vars.append(m_var)
                for c in range(alphabet):
                    v1 = get_var(w1, i, c)
                    v2 = get_var(w2, i, c)
                    add_clause(cnf, [-v1, -v2, m_var])
            add_at_most_k(cnf, match_vars, 4)

    # --- 4. REVERSE COMPLEMENT (WC) ---
    for w1 in range(K):
        for w2 in range(K): 
            wc_vars = []
            for i in range(length):
                wc_var = next_aux_var
                next_aux_var += 1
                wc_vars.append(wc_var)
                pairs = [(0,3), (3,0), (1,2), (2,1)]
                for c1, c2 in pairs:
                    v1 = get_var(w1, 7 - i, c1)
                    v2 = get_var(w2, i, c2)
                    add_clause(cnf, [-v1, -v2, wc_var])
            add_at_most_k(cnf, wc_vars, 4)

    return cnf, next_aux_var - 1

# ==========================================
# 3. VOLANIE SOLVERA A VÝPIS
# ==========================================
def print_result(result, K):
    # Kontrola návratového kódu (10 = SAT, 20 = UNSAT)
    if result.returncode != 10:
        return False

    model = []
    output = result.stdout.decode('utf-8')
    for line in output.splitlines():
        if line.startswith("v"):
            parts = line.split()[1:]
            model.extend(int(x) for x in parts)
    
    print(f"\n[SAT] Našiel som sadu {K} slov:")
    print("-" * 30)
    chars = "ACGT"
    for w in range(K):
        word_str = ""
        for i in range(length):
            for c in range(alphabet):
                var_idx = get_var(w, i, c)
                if var_idx in model:
                    word_str += chars[c]
        print(f"Slovo {w+1}: {word_str}")
    print("-" * 30)
    return True

def call_solver(cnf, nr_vars, output_name, solver_name, verbosity):
    with open(output_name, "w") as file:
        file.write(f"p cnf {nr_vars} {len(cnf)}\n")
        for clause in cnf:
            file.write(' '.join(str(lit) for lit in clause) + '\n')

    # Automatická detekcia .exe pre Windows
    cmd = ['./' + solver_name, '-model', '-verb=' + str(verbosity) , output_name]
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE)
    except FileNotFoundError:
        # Fallback ak užívateľ zabudol napísať .exe
        cmd[0] += ".exe"
        return subprocess.run(cmd, stdout=subprocess.PIPE)

# ==========================================
# 4. HLAVNÝ PROGRAM (LOOP)
# ==========================================
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-o", "--output", default="formula.cnf", type=str)
    # Tu si nastav názov tvojho solvera (napr. glucose.exe)
    parser.add_argument("-s", "--solver", default="glucose-syrup", type=str)
    parser.add_argument("-v", "--verb", default=1, type=int)
    args = parser.parse_args()

    # --- TOTO JE TÁ SLUČKA, KTORÁ TI CHÝBALA ---
    K = 1
    max_found = 0
    
    while True:
        print(f"Skúšam K={K} ... ", end="", flush=True)
        
        # 1. Zakóduj pre číslo K
        cnf, nr_vars = encode(K)
        
        # 2. Spusti solver
        result = call_solver(cnf, nr_vars, args.output, args.solver, args.verb)
        
        # 3. Skontroluj výsledok
        if result.returncode == 10: # SAT
            print("OK!")
            print_result(result, K)
            max_found = K
            K += 1 # Ideme skúsiť viac
        else: # UNSAT
            print("UNSAT (Nemožné).")
            print(f"\n>>> KONIEC. Maximálna veľkosť sady je: {max_found}")
            break