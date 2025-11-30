# DNA Word Design Problem - SAT Solver

Cieľom je nájsť čo najväčšiu množinu slov dĺžky 8, ktoré spĺňajú špecifické podmienky.

## 1. Popis problému

Hľadáme množinu $S$ obsahujúcu $K$ slov nad abecedou $\{A, C, G, T\}$. Každé slovo má pevnú dĺžku $L=8$.

### Parametre a rozhodovacie premenné

- **Abeceda:** 4 znaky (A, C, G, T).
- **Dĺžka slova:** 8 znakov.
- **Veľkosť množiny ($K$):** Počet hľadaných slov.
- **Rozhodovacie premenné:**  
  $X_{w,i,c}$ je binárna premenná, ktorá je pravdivá (True), ak slovo $w$ na pozícii $i$ obsahuje znak $c$.

### Podmienky

Riešenie musí spĺňať nasledujúce podmienky:

1. **Validita slova:**  
   Na každej pozícii každého slova musí byť presne jeden znak.

2. **GC obsah:**  
   Každé slovo musí obsahovať presne 4 znaky z množiny $\{C, G\}$ (a teda 4 znaky z $\{A, T\}$).

3. **Hammingova vzdialenosť:**  
   Každá dvojica rôznych slov $u, v \in S$ sa musí líšiť aspoň na 4 pozíciách ($H(u, v) \ge 4$).

4. **Vzdialenosť voči reverznému komplementu:**  
   Pre každú dvojicu slov $u, v \in S$ (vrátane prípadu $u=v$) musí platiť:  
   $H(u, v^{RC}) \ge 4$  
   kde $v^{RC}$ je reverzný komplement slova.

5. **Reverzný komplement:**  
   Vznikne otočením slova a zámennou A↔T, C↔G.

---

## 2. Popis kódovania do CNF

Program generuje formulu v CNF vo formáte DIMACS.

### Použité kódovanie

- **Premenné:**  
  Mapovanie $(w, i, c)$ na celé číslo pomocou vzorca:  
  $$(w \cdot WORD\_SIZE \cdot CHARS\_SIZE) + (i \cdot CHARS\_SIZE) + c + 1$$

- **At Most K:**  
  Použité **Binomial Encoding**.

  Pre obmedzenie $\sum x_i \le k$ sú generované klauzuly pre každú kombináciu $k+1$ premenných, ktoré sa nesmú vyskytovať súčasne.

  **Príklad:**  
  Pre „maximálne 1 znak na pozícii“ (k = 1):  
  - $(\neg A \lor \neg C)$  
  - $(\neg A \lor \neg G)$  
  - …

  Na zabezpečenie $H(u,v) \ge d$ (t. j. počet zhôd ≤ L−d) sú zavedené pomocné premenné `match`.

  Implikácia:  
  $(x_{w1} \land x_{w2}) \implies match$  
  sa prevedie na klauzulu:  
  $(\neg x_{w1} \lor \neg x_{w2} \lor match)$

  Následne sa na sumu premenných `match` aplikuje **At Most K**.

### Spustenie

```bash
python3 word_desing_dna.py [-h] [-s SOLVER] [-o OUTPUT] [-v {0,1}] [-k FIXED_K]
```

### Argumenty

- `-o, --output` — názov výstupného CNF súboru (default: `formula.cnf`)  
- `-s, --solver` — cesta k solveru (default: `glucose-syrup`)  
- `-v, --verb` — verbosity solvera 
- `-k, --fixed_k` — vyrieši len pre konkrétne $K$

### Formát výstupu

Ak je riešenie **SAT**, vypíšeme nájdené slová:

```
For K=2: SAT. Time: 0.05s
----------------------------------------
Word 1: ACGTACGT
Word 2: GGTCCATG
----------------------------------------
```
## 5. Experimenty

Experimenty boli vykonané na nasledujúcej konfigurácii:

- **CPU:** Intel(R) Core(TM) i7-10510U CPU @ 1.80GHz  
- **RAM:** 32 GB  
- **OS:** Windows 11 Pro (WSL/Linux prostredie)  
- **Solver:** glucose-syrup  

### Výsledky

Skript dokázal v rozumnom čase nájsť riešenie pre **K = 72** slov.

| K | Čas výpočtu | Výsledok |
|---|-------------|----------|
| 10 | 0.79 s  | SAT |
| 20 | 1.82 s  | SAT |
| 40 | 4.22 s  | SAT |
| 50 | 9.94 s  | SAT |
| 60 | 14.20 s | SAT |
| 70 | 46.27 s | SAT |
| 72 | 68.80 s | SAT |

### Pozorovania

- **Malé inštancie ($K \le 30$):** riešenie sa nájce veľmi rýchlo, často do 3 sekúnd.  
- **Nelineárny nárast náročnosti:** od $K = 50$ začína čas rásť strmšie; medzi $K = 60$ a $K = 72$ je zrýchlenie rastu výrazné (viac ako 4×).  
- **Maximálna dosiahnutá veľkosť:**  
  Skript úspešne vygeneroval **72 slov** spĺňajúcich všetky kritériá (GC obsah, Hamming, RC Hamming).
