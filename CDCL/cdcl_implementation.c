#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define MAX_VARS 5000
#define MAX_CLAUSES 100000
#define MAX_LITS 50
#define MAX_TRAIL 100000

#define SAT 10
#define UNSAT 20
#define UNASSIGNED -1

typedef struct {
    int lits[MAX_LITS];
    int size;
} Clause;

typedef struct {

    int num_vars;
    int num_clauses;

    Clause clauses[MAX_CLAUSES];

    int assignment[MAX_VARS+1];
    int level_of[MAX_VARS+1];
    int reason[MAX_VARS+1];

    int trail[MAX_TRAIL];  // stores literals
    int trail_top;

    int level;

} Solver;
typedef struct {
    int row;
    int col;
    int val;
    bool exists;
} VarMap;

VarMap var_map[MAX_VARS+1];

Solver solver;

////////////////////////////////////////////////////////////
// Utility
////////////////////////////////////////////////////////////

int absval(int x) { return x > 0 ? x : -x; }

int lit_value(int lit) {
    int var = absval(lit);
    int val = solver.assignment[var];

    if (val == UNASSIGNED) return UNASSIGNED;
    return (lit > 0) ? val : !val;
}

////////////////////////////////////////////////////////////
// Add clause
////////////////////////////////////////////////////////////

void add_clause(int *lits, int size) {
    Clause *c = &solver.clauses[solver.num_clauses++];
    c->size = size;
    for (int i = 0; i < size; i++)
        c->lits[i] = lits[i];
}

////////////////////////////////////////////////////////////
// Assign literal
////////////////////////////////////////////////////////////

void assign(int lit, int level, int reason_clause) {

    int var = absval(lit);
    int val = (lit > 0);

    solver.assignment[var] = val;
    solver.level_of[var] = level;
    solver.reason[var] = reason_clause;

    solver.trail[solver.trail_top++] = lit;
}

////////////////////////////////////////////////////////////
// Propagation (returns conflict clause index or -1)
////////////////////////////////////////////////////////////

int propagate() {

    bool changed = true;

    while (changed) {

        changed = false;

        for (int i = 0; i < solver.num_clauses; i++) {

            Clause *c = &solver.clauses[i];

            int unassigned = 0;
            int last_lit = 0;
            bool satisfied = false;

            for (int j = 0; j < c->size; j++) {

                int val = lit_value(c->lits[j]);

                if (val == 1) {
                    satisfied = true;
                    break;
                }

                if (val == UNASSIGNED) {
                    unassigned++;
                    last_lit = c->lits[j];
                }
            }

            if (satisfied)
                continue;

            if (unassigned == 0)
                return i;  // conflict clause

            if (unassigned == 1) {
                assign(last_lit, solver.level, i);
                changed = true;
            }
        }
    }

    return -1;
}

////////////////////////////////////////////////////////////
// Decide next variable
////////////////////////////////////////////////////////////

int decide() {
    for (int i = 1; i <= solver.num_vars; i++)
        if (solver.assignment[i] == UNASSIGNED)
            return i;
    return 0;
}

////////////////////////////////////////////////////////////
// Backtrack
////////////////////////////////////////////////////////////

void backtrack(int level) {

    while (solver.trail_top > 0) {

        int lit = solver.trail[solver.trail_top - 1];
        int var = absval(lit);

        if (solver.level_of[var] <= level)
            break;

        solver.assignment[var] = UNASSIGNED;
        solver.reason[var] = -1;
        solver.level_of[var] = 0;

        solver.trail_top--;
    }

    solver.level = level;
}

int int_cuberoot(int x)
{
    int r = 1;
    while (r*r*r < x)
        r++;
    return r;
}
void decode_and_print_sudoku()
{
   int N = int_cuberoot(solver.num_vars);

if (N*N*N != solver.num_vars)
{
    printf("Variable count (%d) is not N^3 — cannot decode as standard Sudoku.\n",
           solver.num_vars);
    return;
}


    if (N*N*N > solver.num_vars)
        N--;  // adjust if overshoot

    if (N <= 0)
    {
        printf("Could not determine Sudoku size.\n");
        return;
    }

    printf("\nSudoku size detected: %dx%d\n\n", N, N);

    // Allocate grid
    int **grid = malloc(N * sizeof(int*));
    for (int i = 0; i < N; i++)
    {
        grid[i] = malloc(N * sizeof(int));
        for (int j = 0; j < N; j++)
            grid[i][j] = 0;
    }

    int sudoku_vars = N*N*N;

    // Decode only first N^3 variables
    for (int var = 1; var <= sudoku_vars; var++)
    {
        if (solver.assignment[var] != 1)
            continue;

        int v = (var - 1) % N;
        int c = ((var - 1) / N) % N;
        int r = (var - 1) / (N * N);

        if (r < N && c < N)
            grid[r][c] = v + 1;
    }

    // Print nicely formatted grid
    int base = 1;
    while (base * base < N)
        base++;

    for (int r = 0; r < N; r++)
    {
        if (r % base == 0 && r != 0)
        {
            for (int i = 0; i < N*2 + base - 1; i++)
                printf("-");
            printf("\n");
        }

        for (int c = 0; c < N; c++)
        {
            if (c % base == 0 && c != 0)
                printf("| ");

            int val = grid[r][c];

            if (val < 10)
                printf("%d ", val);
            else
                printf("%c ", 'A' + val - 10);
        }
        printf("\n");
    }

    for (int i = 0; i < N; i++)
        free(grid[i]);
    free(grid);
}

////////////////////////////////////////////////////////////
// First-UIP Conflict Analysis
////////////////////////////////////////////////////////////

int analyze(int conflict_clause, int *out_clause) {

    int seen[MAX_VARS+1] = {0};
    int counter = 0;
    int idx = solver.trail_top - 1;

    Clause *c = &solver.clauses[conflict_clause];

    // mark literals in conflict clause
    for (int i = 0; i < c->size; i++) {
        int v = absval(c->lits[i]);
        seen[v] = 1;

        if (solver.level_of[v] == solver.level)
            counter++;
    }

    while (counter > 1) {

        int lit = solver.trail[idx--];
        int v = absval(lit);

        if (!seen[v])
            continue;

        seen[v] = 0;
        counter--;

        int reason_clause = solver.reason[v];

        if (reason_clause == -1)
            continue;

        Clause *rc = &solver.clauses[reason_clause];

        for (int i = 0; i < rc->size; i++) {

            int vv = absval(rc->lits[i]);

            if (!seen[vv]) {
                seen[vv] = 1;

                if (solver.level_of[vv] == solver.level)
                    counter++;
            }
        }
    }

    int size = 0;
    int backtrack_level = 0;

    for (int v = 1; v <= solver.num_vars; v++) {

        if (seen[v]) {

            int lit = solver.assignment[v] ? -v : v;
            out_clause[size++] = lit;

            if (solver.level_of[v] != solver.level &&
                solver.level_of[v] > backtrack_level)
                backtrack_level = solver.level_of[v];
        }
    }

    add_clause(out_clause, size);
    return backtrack_level;
}

////////////////////////////////////////////////////////////
// Solve
////////////////////////////////////////////////////////////

int solve() {

    solver.level = 0;

    while (1) {

        int conflict = propagate();

        if (conflict != -1) {

            if (solver.level == 0)
                return UNSAT;

            int learned[MAX_LITS];
            int backtrack_level = analyze(conflict, learned);

            backtrack(backtrack_level);
            continue;
        }

        int var = decide();

        if (var == 0)
            return SAT;

        solver.level++;
        assign(var, solver.level, -1);  // decision literal
    }
}

////////////////////////////////////////////////////////////
// DIMACS parser
////////////////////////////////////////////////////////////

void parse_dimacs(FILE *f) {

    char line[1024];
    int lits[MAX_LITS];

    solver.num_clauses = 0;

    while (fgets(line, sizeof(line), f)) {

        if (line[0] == 'c')
            continue;

        if (line[0] == 'p') {

            sscanf(line, "p cnf %d %d",
                   &solver.num_vars,
                   &solver.num_clauses);

            solver.num_clauses = 0;
            continue;
        }

        int lit, count = 0;
        char *token = strtok(line, " \t\n");

        while (token) {

            lit = atoi(token);
            if (lit == 0) break;

            lits[count++] = lit;
            token = strtok(NULL, " \t\n");
        }

        if (count > 0)
            add_clause(lits, count);
    }
}

////////////////////////////////////////////////////////////
// Print Result
////////////////////////////////////////////////////////////

void print_result(int res) {

    if (res == SAT) {

        printf("SAT\nv ");

        for (int i = 1; i <= solver.num_vars; i++) {

            if (solver.assignment[i] == 1)
                printf("%d ", i);
            else if (solver.assignment[i] == 0)
                printf("-%d ", i);
            else
                printf("%d ", i); // default true
        }

        printf("0\n");
    }
    else {
        printf("UNSAT\n");
    }
}

////////////////////////////////////////////////////////////
// Main
////////////////////////////////////////////////////////////

int main(int argc, char **argv) {

    if (argc < 2) {
        printf("Usage: solver file.cnf\n");
        return 1;
    }

    memset(&solver, 0, sizeof(solver));

    for (int i = 0; i <= MAX_VARS; i++)
        solver.assignment[i] = UNASSIGNED;

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        printf("File error\n");
        return 1;
    }

    parse_dimacs(f);
    fclose(f);

  int res = solve();
print_result(res);

if (res == SAT)
{
    decode_and_print_sudoku();
}


    return 0;
}
