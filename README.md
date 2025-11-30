# **Word Design for DNA Computing on Surfaces**

This project implements a SAT-based solver for the **Word Design for DNA Computing on Surfaces** problem. The goal is to generate the largest possible set of DNA words (strings of length 8 over the alphabet $\\{A, C, G, T\\}$) that satisfy specific combinatorial constraints used in bioinformatics and DNA computing.

## **Problem Description**

We are looking for a set $S$ of words of fixed length $L=8$. The size of the set is denoted by $K = |S|$. The words must satisfy the following properties:

1. **Length:** Each word has exactly $L=8$ characters.  
2. **GC:** Each word must contain exactly 4 characters from the set $\{C, G\}$ (and consequently exactly 4 characters from $\{A, T\}$).  
3. **Hamming Distance:** For every pair of distinct words $u, v \in S$, the Hamming distance $d_H(u, v) \ge 4$.  
   * *Note:* This is equivalent to saying that they match in *at most* $4$ positions.  
4. **Reverse Complement:** For every pair of words $u, v \in S$ (including the case where $u=v$), the Hamming distance between the reverse of $u$ ($u^R$) and the Watson-Crick complement of $v$ ($v^C$) must be at least $4$.  
   * *Watson-Crick pairs:* $A \leftrightarrow T$, $C \leftrightarrow G$.

### **Strategy**

The script solves the decision problem "Does a set of size K exist?" iteratively for $K=1, 2,\dots$

* If the solver returns **SAT**, we know that $K_{max} \ge K$.  
* If the solver returns **UNSAT**, we know that $K_{max} < K$.  
* If the solver **Times Out**, we cannot determine the truth value, but we establish a lower bound based on the last successful $K$.

## **Encoding**

The problem is encoded into CNF using the DIMACS format. We use two types of variables: **Basic Variables** representing the characters, and **Auxiliary Variables** representing matching positions between words.

### **Variables**

1\. Word Variables  
Variables $X\_{w,i,c}$ represent that word number $w$ has character $c$ at position $i$.

* $w \in \{0, \dots, K-1\}$  
* $i \in \{0, \dots, 7\}$  
* $c \in \{0, 1, 2, 3\}$ (Mapping: 0=A, 1=C, 2=G, 3=T)

2\. Match Indicator Variables  
* $M_{w_1, w_2, i}$: True if word $w_1$ and word $w_2$ have the same character at position $i$.  
* $WC_{w_1, w_2, i}$: True if word $w_1$ (reversed) and word $w_2$ (complemented) match at position $i$.

### **Constraints**

The following constraints are generated:

1. **Physical Constraints:**  
   * At least one character per position: $\bigvee_{c} X_{w,i,c}$.  
   * At most one character per position: $\neg X_{w,i,c_1} \lor \neg X_{w,i,c_2}$ for $c_1 \neq c_2$.  
2. **GC-Content:**  
   * We enforce that $\sum_{i} (X_{w,i,C} \lor X_{w,i,G}) = 4$.  
   * This is implemented using **At-Most-K** constraints on the set of C/G variables and the set of A/T variables.  
3. **Hamming Distance:**  
   * We imply the match variable: $(X_{w_1,i,c} \land X_{w_2,i,c}) \implies M_{w_1, w_2, i}$.  
   * We enforce that the total number of matches is at most 4: $\sum_{i} M_{w_1, w_2, i} \le 4$.  
4. **Reverse Complement:**  
   * We compare We compare $u[7-i]$ with $v[i]$. A match occurs if they form a Watson-Crick pair. A match occurs if they form a Watson-Crick pair.  
   * We enforce that the total number of WC-matches is at most 4\.

For constraints of the form "At most $k$ variables are True", we use **Binomial Encoding**. We explicitly forbid every combination of $k+1$ variables.

* For $L=8$, this is efficient. For example, ensuring "At most 4" requires forbidding all subsets of size 5\. The number of clauses is $\binom{8}{5} = 56$, which is negligible.

## **User Documentation**

The script requires **Python 3** and **Glucose**.

### **Basic Usage**

./dna\_solver.py \[-h\] \[-s SOLVER\] \[-o OUTPUT\] \[-v {0,1}\] \[-k FIXED\_K\]

### **Command-line Options**

* \-h, \--help: Show help message and exit.  
* \-s SOLVER: Path to the solver executable (default: glucose).  
* \-o OUTPUT: Output filename for the generated CNF (default: formula.cnf).  
* \-v {0,1}: Verbosity of the solver output (default: 1).  
* \-k FIXED\_K: If set to a positive integer, the script solves for a specific set size $K$ and exits. If not set, it runs in optimization mode (finding max $K$).

## **Example Instances**

The following instances are included in the solution:

* **small\_sat.cnf**: A trivial instance for $K=2$. Solvable immediately.   
* **big\_instance.cnf**: A large satisfiable instance ($K=74$). This represents the limit of what can be solved within a reasonable timeframe using this encoding.

## **Experiments**

Experiments were run on **Intel Core i7-10510U (1.80 GHz)** with **32 GB RAM**. The solver used was Glucose 4.1.

We focused on finding the maximum set size $K$.

| Set Size (K) | Result | Time (s) |
| :---- | :---- | :---- |
| 10 | SAT | 0.60 |
| 30 | SAT | 3.13 |
| 50 | SAT | 4.28 |
| 70 | SAT | 15.89 |
| 74 | SAT | 572.20 |
| 75 | **Timeout** | \> 600.0 |

Observations:  
The time complexity grows exponentially with $K$.
We observed a significant **difference** between $K=70$ and $K=74$. The computation time jumped from \~16 seconds to nearly 10 minutes. At $K=75$, the solver could not find a solution or prove unsatisfiability within a reasonable time limit, suggesting that the problem instance becomes exceptionally hard at this boundary.