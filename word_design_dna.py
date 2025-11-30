import subprocess
import itertools
from argparse import ArgumentParser

length = 8
alphabet = 4

def get_var(w, i, c):
    return (w*length*alphabet)+(i*alphabet)+c+1

def add_at_most_k(cnf, variables, k):
    """
    Jednoduchá implementácia "At Most K" pomocou kombinácií.
    Zakáže všetky kombinácie veľkosti k+1.
    """
    for combo in itertools.combinations(variables, k + 1):
        # Klauzula: (-A v -B v -C ...)
        clause = [-x for x in combo] + [0]
        cnf.append(clause)

def add_clause(cnf, literals):
    cnf.append(literals + [0])

def encode(K):
    """
    Vygeneruje CNF formulu pre hľadanie K slov.
    Vráti (cnf, pocet_premennych)
    """
    cnf = []
    
    # Počet základných premenných (pre písmená)
    basic_vars_count = K * length * alphabet
    
    # Pomocné premenné začínajú hneď za základnými
    next_aux_var = basic_vars_count + 1

    # --------------------------------------
    # 1. FYZIKA (Physical Constraints)
    # --------------------------------------
    for w in range(K):
        for i in range(length):
            vars_pos = [get_var(w, i, c) for c in range(alphabet)]
            
            # Aspoň jeden znak
            add_clause(cnf, vars_pos)
            
            # Najviac jeden znak
            add_at_most_k(cnf, vars_pos, 1)

    # --------------------------------------
    # 2. GC-CONTENT (Presne 4 sú C alebo G)
    # --------------------------------------
    for w in range(K):
        cg_vars = []
        at_vars = []
        for i in range(length):
            cg_vars.append(get_var(w, i, 1)) # C
            cg_vars.append(get_var(w, i, 2)) # G
            at_vars.append(get_var(w, i, 0)) # A
            at_vars.append(get_var(w, i, 3)) # T
        
        # Aby bolo presne 4 C/G, musí byť max 4 C/G a zároveň max 4 A/T
        add_at_most_k(cnf, cg_vars, 4)
        add_at_most_k(cnf, at_vars, 4)

    # --------------------------------------
    # 3. HAMMINGOVA VZDIALENOSŤ
    # --------------------------------------
    # Každá dvojica (w1, w2) sa líši aspoň v 4 => Zhoduje max v 4
    for w1 in range(K):
        for w2 in range(w1 + 1, K):
            match_vars = []
            
            for i in range(length):
                m_var = next_aux_var
                next_aux_var += 1
                match_vars.append(m_var)
                
                # Ak majú rovnaký znak, m_var musí byť TRUE
                # (-A1 v -A2 v m_var)
                for c in range(alphabet):
                    v1 = get_var(w1, i, c)
                    v2 = get_var(w2, i, c)
                    add_clause(cnf, [-v1, -v2, m_var])
            
            # Max 4 zhody
            add_at_most_k(cnf, match_vars, 4)

    # --------------------------------------
    # 4. REVERSE COMPLEMENT (WC)
    # --------------------------------------
    # Každá dvojica (w1, w2) vrátane w1==w2
    for w1 in range(K):
        for w2 in range(K): 
            wc_vars = []
            
            for i in range(length):
                wc_var = next_aux_var
                next_aux_var += 1
                wc_vars.append(wc_var)
                
                # Porovnávame w1[7-i] a w2[i]
                # Zhoda je, ak tvoria pár A-T alebo C-G
                pairs = [(0,3), (3,0), (1,2), (2,1)] # (A,T), (T,A), (C,G), (G,C)
                
                for c1, c2 in pairs:
                    v1 = get_var(w1, 7 - i, c1)
                    v2 = get_var(w2, i, c2)
                    # Ak w1 má c1 a w2 má c2, tak wc_var je TRUE
                    add_clause(cnf, [-v1, -v2, wc_var])
            
            # Max 4 WC-zhody
            add_at_most_k(cnf, wc_vars, 4)

    return cnf, next_aux_var - 1

def print_result(result, K):
    # Skontrolujeme návratový kód
    if result.returncode != 10: # 10 = SAT, 20 = UNSAT
        print(f"Pre K={K} riešenie neexistuje (UNSAT).")
        return False

    # Parsovanie modelu
    model = []
    output = result.stdout.decode('utf-8')
    for line in output.splitlines():
        if line.startswith("v"):
            parts = line.split()[1:]
            model.extend(int(x) for x in parts)
    
    # Dekódovanie a výpis
    print(f"\nNÁJDENÉ RIEŠENIE PRE K={K}:")
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
    # print CNF into formula.cnf in DIMACS format
    with open(output_name, "w") as file:
        file.write("p cnf " + str(nr_vars) + " " + str(len(cnf)) + '\n')
        for clause in cnf:
            file.write(' '.join(str(lit) for lit in clause) + '\n')

    # call the solver and return the output
    return subprocess.run(['./' + solver_name, '-model', '-verb=' + str(verbosity) , output_name], stdout=subprocess.PIPE)

if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        default="input.in",
        type=str,
        help=(
            "The instance file."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="formula.cnf",
        type=str,
        help=(
            "Output file for the DIMACS format (i.e. the CNF formula)."
        ),
    )
    parser.add_argument(
        "-s",
        "--solver",
        default="glucose-syrup",
        type=str,
        help=(
            "The SAT solver to be used."
        ),
    )
    parser.add_argument(
        "-v",
        "--verb",
        default=1,
        type=int,
        choices=range(0,2),
        help=(
            "Verbosity of the SAT solver used."
        ),
    )
    args = parser.parse_args()

    # get the input instance
    instance = load_instance(args.input)

    # encode the problem to create CNF formula
    cnf, nr_vars = encode(instance)

    # call the SAT solver and get the result
    result = call_solver(cnf, nr_vars, args.output, args.solver, args.verb)

    # interpret the result and print it in a human-readable format
    print_result(result)
