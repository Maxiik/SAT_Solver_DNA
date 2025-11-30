import subprocess
from argparse import ArgumentParser
from itertools import combinations
import time
import sys

WORD_SIZE = 8
CHARS_SIZE = 4
CHARS = "ACGT"

def get_var_id(w, i, c):
    return (w*WORD_SIZE*CHARS_SIZE)+(i*CHARS_SIZE)+c+1

def add_at_most_k(cnf, variables, k):
    for combo in combinations(variables, k+1):
        clause = [-var for var in combo]
        clause.append(0)
        cnf.append(clause)

def encode(K):
    cnf = []
    num_vars = K*WORD_SIZE*CHARS_SIZE
    current_var = num_vars+1

    # Prave jedno pismeno na poziciu
    for w in range(K):
        for i in range(WORD_SIZE):
            vars_at_pos = [get_var_id(w, i, c) for c in range(CHARS_SIZE)]

            # najmenej jedno
            cnf.append(vars_at_pos+[0])
            # najviac jedno
            add_at_most_k(cnf, vars_at_pos, 1)

    # Presne 4 pismena C alebo G
    for w in range(K):
        cg_vars = []
        at_vars = []
        for i in range(WORD_SIZE):
            cg_vars.append(get_var_id(w, i, 1))
            cg_vars.append(get_var_id(w, i, 2))
            at_vars.append(get_var_id(w, i, 0))
            at_vars.append(get_var_id(w, i, 3))

        # Aby sme mali presne 4, tak max 4 CG a max 4 AT
        add_at_most_k(cnf, cg_vars, 4)
        add_at_most_k(cnf, at_vars, 4)

    # Rozdielne slova sa lisia aspon v 4 poziciach
    for w1 in range(K):
        for w2 in range(w1+1, K):
            matches = []
            for i in range(WORD_SIZE):
                p_var = current_var
                current_var += 1
                matches.append(p_var)

                # (v1 AND v2) -> p_var  <=>  (-v1 OR -v2 OR p_var)
                for c in range(CHARS_SIZE):
                    v1 = get_var_id(w1, i, c)
                    v2 = get_var_id(w2, i, c)
                    cnf.append([-v1, -v2, p_var, 0])

            # max 4 implikuje min 4
            add_at_most_k(cnf,matches,4)

    # Reverse complement 
    for w1 in range(K):
        for w2 in range(K):  # Pozera vsetky dvojice, aj seba
            wc_matches = []
            for i in range(WORD_SIZE):
                wc_var = current_var
                current_var += 1
                wc_matches.append(wc_var)

                pos_1 = WORD_SIZE - 1 - i

                # A-T, T-A, C-G, G-C
                pairs = [(0, 3), (3, 0), (1, 2), (2, 1)]

                for c1, c2 in pairs:
                    v1 = get_var_id(w1, pos_1, c1)
                    v2 = get_var_id(w2, i, c2)
                    cnf.append([-v1, -v2, wc_var, 0])

            # max 4 implikuje min 4
            add_at_most_k(cnf,wc_matches,4)

    return cnf, current_var - 1


def call_solver(cnf, nr_vars, output_name, solver_name, verbosity):
    with open(output_name, "w") as file:
        file.write(f"p cnf {nr_vars} {len(cnf)}\n")
        for clause in cnf:
            file.write(" ".join(map(str, clause)) + "\n")
    cmd = ["./" + solver_name, "-model", "-verb=" + str(verbosity), output_name]

    try:
        start_time = time.time()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        end_time = time.time()
        
        return result, end_time - start_time
    except FileNotFoundError:
        print(
            f"\nERROR: '{solver_name}' was not found."
        )
        sys.exit(1)


def print_result(result, K, time):
    # (10 = SAT, 20 = UNSAT)
    if result.returncode == 20:
        print(f"For K={K}: UNSAT. Time: {time:.2f}s")
        return False

    print(f"For K={K}: SAT. Time: {time:.2f}s")

    # Parse model
    output = result.stdout.decode("utf-8")
    model = []
    for line in output.splitlines():
        if line.startswith("v"):
            parts = line.split()[1:]
            model.extend(int(x) for x in parts)

    # Citatelny output
    print("-"*40)
    for w in range(K):
        word_str = ""
        for i in range(WORD_SIZE):
            for c in range(CHARS_SIZE):
                if get_var_id(w, i, c) in model:
                    word_str += CHARS[c]
        print(f"Word {w+1}: {word_str}")
    print("-"*40+"\n")
    return True


if __name__ == "__main__":
    parser = ArgumentParser()
    
    parser.add_argument(
        "-o", "--output", default="formula.cnf", help="Output file for CNF"
    )
    
    parser.add_argument(
        "-s", "--solver", default="glucose-syrup", help="Solver executable"
    )
    
    parser.add_argument(
        "-v", "--verb", default=1, type=int, help="Verbosity"
    )
    
    parser.add_argument(
        "-k",
        "--fixed_k",
        type=int,
        default=0,
        help="If set, solves only for this specific K",
    )
    
    args = parser.parse_args()

    if args.fixed_k > 0:
        K = args.fixed_k
        print(f"Generating and solving for K={K}...")
        cnf, vars_count = encode(K)
        res, t = call_solver(cnf, vars_count, args.output, args.solver, args.verb)
        print_result(res, K, t)
        sys.exit(0)

    print("Starting for the maximum word set size...")
    K = 1
    max_k = 0
    while True:
        cnf, vars_count = encode(K)
        res, t = call_solver(cnf, vars_count, args.output, args.solver, args.verb)

        if res.returncode == 10:  # SAT
            max_k = K
            print_result(res, K, t)
            K += 1
        else:  # UNSAT
            print(f"For K={K} UNSAT.")
            break
