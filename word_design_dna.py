import subprocess
import sys
import time
from argparse import ArgumentParser

WORD_LENGTH = 8      # Length of one word
ALPHABET_SIZE = 4    
CHARS = "ACGT"       # 0=A, 1=C, 2=G, 3=T

def get_var_id(w, i, c):
    # +1 because DIMACS format requires variables starting from 1
    return (w * WORD_LENGTH * ALPHABET_SIZE) + (i * ALPHABET_SIZE) + c + 1

def generate_combinations(elements, k):
    if k == 0:
        return [[]]
    if not elements:
        return []
    
    head = elements[0]
    tail = elements[1:]
    
    with_head = []
    for combo in generate_combinations(tail, k - 1):
        with_head.append([head] + combo)
        
    without_head = generate_combinations(tail, k)
    
    return with_head + without_head

def add_at_most_k_constraint(cnf, variables, k):
    forbidden_combinations = generate_combinations(variables, k + 1)
    
    for combo in forbidden_combinations:
        # Clause: (NOT a OR NOT b OR ...)
        clause = []
        for var in combo:
            clause.append(-var)
        clause.append(0) # 0 is the line terminator in DIMACS
        cnf.append(clause)

def encode(K):
    cnf = []
    
    num_basic_vars = K * WORD_LENGTH * ALPHABET_SIZE

    current_aux_var = num_basic_vars + 1

    # 1. PHYSICAL CONSTRAINTS: Exactly one letter per position
    for w in range(K):
        for i in range(WORD_LENGTH):
            vars_at_pos = [get_var_id(w, i, c) for c in range(ALPHABET_SIZE)]
            
            # At least one letter
            cnf.append(vars_at_pos + [0])
            
            # At most one letter
            add_at_most_k_constraint(cnf, vars_at_pos, 1)

    # 2. GC-CONTENT: Exactly 4 characters must be C or G
    for w in range(K):
        cg_vars = []
        at_vars = []
        for i in range(WORD_LENGTH):
            cg_vars.append(get_var_id(w, i, 1))
            cg_vars.append(get_var_id(w, i, 2))
            at_vars.append(get_var_id(w, i, 0))
            at_vars.append(get_var_id(w, i, 3))
        
        # To have exactly 4, we enforce: max 4 are CG and max 4 are AT
        add_at_most_k_constraint(cnf, cg_vars, 4)
        add_at_most_k_constraint(cnf, at_vars, 4)

    # 3. HAMMING DISTANCE: Distinct words differ in at least 4 positions
    for w1 in range(K):
        for w2 in range(w1 + 1, K):
            matches = []
            for i in range(WORD_LENGTH):
                p_var = current_aux_var
                current_aux_var += 1
                matches.append(p_var)
                
                # If both words have the same char, p_var must be TRUE
                # Implication: (v1 AND v2) -> p_var  <=>  (-v1 OR -v2 OR p_var)
                for c in range(ALPHABET_SIZE):
                    v1 = get_var_id(w1, i, c)
                    v2 = get_var_id(w2, i, c)
                    cnf.append([-v1, -v2, p_var, 0])
            
            # Max 4 matches implies Min 4 differences
            add_at_most_k_constraint(cnf, matches, 4)

    # 4. REVERSE COMPLEMENT: Watson-Crick pairing constraint
    for w1 in range(K):
        for w2 in range(K): # Check every pair, including self
            wc_matches = []
            for i in range(WORD_LENGTH):
                wc_var = current_aux_var
                current_aux_var += 1
                wc_matches.append(wc_var)
                
                pos_1 = WORD_LENGTH - 1 - i
                
                # Watson-Crick pairs: A-T, T-A, C-G, G-C
                pairs = [(0,3), (3,0), (1,2), (2,1)]
                
                for c1, c2 in pairs:
                    v1 = get_var_id(w1, pos_1, c1)
                    v2 = get_var_id(w2, i, c2)
                    cnf.append([-v1, -v2, wc_var, 0])
            
            # Max 4 WC-matches implies Min 4 differences
            add_at_most_k_constraint(cnf, wc_matches, 4)

    return cnf, current_aux_var - 1

def call_solver(cnf, nr_vars, output_name, solver_name, verbosity):
    with open(output_name, "w") as file:
        file.write(f"p cnf {nr_vars} {len(cnf)}\n")
        for clause in cnf:
            file.write(" ".join(map(str, clause)) + "\n")

    cmd = ['./' + solver_name, '-model', '-verb=' + str(verbosity), output_name]
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        end_time = time.time()
        return result, end_time - start_time
    except FileNotFoundError:
        print(f"\nERROR: The solver '{solver_name}' was not found in the current directory.")
        sys.exit(1)

def print_result(result, K, time_taken):
    # Check return code (10 = SAT, 20 = UNSAT)
    if result.returncode != 10: 
        print(f"For K={K}: UNSAT (No solution found). Time: {time_taken:.2f}s")
        return False

    print(f"For K={K}: SAT (Solution found!). Time: {time_taken:.2f}s")
    
    # Parse the model from output
    output = result.stdout.decode('utf-8')
    model = []
    for line in output.splitlines():
        if line.startswith("v"):
            parts = line.split()[1:]
            model.extend(int(x) for x in parts)

    print("-" * 40)
    for w in range(K):
        word_str = ""
        for i in range(WORD_LENGTH):
            for c in range(ALPHABET_SIZE):
                if get_var_id(w, i, c) in model:
                    word_str += CHARS[c]
        print(f"Word {w+1}: {word_str}")
    print("-" * 40 + "\n")
    return True

# ==============================================================================
# MAIN execution
# ==============================================================================

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-o", "--output", default="formula.cnf", help="Output file for CNF")
    parser.add_argument("-s", "--solver", default="glucose-syrup", help="Solver executable")
    parser.add_argument("-v", "--verb", default=1, type=int, help="Verbosity")
    parser.add_argument("-k", "--fixed_k", type=int, default=0, help="If set, solves only for this specific K")
    args = parser.parse_args()

    # If user specified -k, solve only that instance (for generating files)
    if args.fixed_k > 0:
        K = args.fixed_k
        print(f"Generating and solving instance for fixed K={K}...")
        cnf, vars_count = encode(K)
        res, t = call_solver(cnf, vars_count, args.output, args.solver, args.verb)
        print_result(res, K, t)
        sys.exit(0)

    # Otherwise, find the maximum set size (Optimization)
    print("Starting search for the maximum DNA word set size...")
    K = 1
    max_k = 0
    while True:
        cnf, vars_count = encode(K)
        res, t = call_solver(cnf, vars_count, args.output, args.solver, args.verb)
        
        if res.returncode == 10: # SAT
            max_k = K
            print_result(res, K, t)
            K += 1
        else: # UNSAT
            print(f"For K={K} solution does not exist (UNSAT).")
            print(f"Maximum set size found is: {max_k}")
            break