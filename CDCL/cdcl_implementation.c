#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

/*  ═══════════════════════════════════════════════════════════════════════════
    CDCL SAT Solver — compatible with the Kwon & Jain optimised φ' encoding
    produced by sudoku_to_cnf.py.

    The CNF file embeds three kinds of comment lines the solver uses to
    reconstruct the full Sudoku grid after finding a satisfying assignment:

        c SIZE <N>                 board is N×N
        c MAP  <var> <r> <c> <v>  DIMACS variable <var> represents cell(r,c)=v
        c FIXED <r> <c> <v>       cell(r,c) was pre-assigned to v (not in CNF)

    All (r,c,v) values are 1-indexed.
    ═══════════════════════════════════════════════════════════════════════════ */

/* ─── tuneable limits ─────────────────────────────────────────────────────── */
#define MAX_VARS      500000
#define MAX_TRAIL     500000
#define MAX_LIT_BUF   256        /* max literals per clause in the input file */
#define INIT_CLAUSES  65536      /* initial clause array capacity              */

/* ─── result codes ────────────────────────────────────────────────────────── */
#define SAT        10
#define UNSAT      20
#define UNASSIGNED -1

/* ══════════════════════════════════════════════════════════════════════════ */
/* Data structures                                                            */
/* ══════════════════════════════════════════════════════════════════════════ */

typedef struct {
    int *lits;
    int  size;
} Clause;

typedef struct {
    int num_vars;
    int num_clauses;
    int clause_cap;

    Clause *clauses;

    int *assignment;   /* [0..num_vars]  1=true  0=false  UNASSIGNED        */
    int *level_of;     /* decision level when var was assigned               */
    int *reason;       /* forcing clause index, or -1 for decisions          */

    int *trail;        /* literals in assignment order                       */
    int  trail_top;

    int level;         /* current decision level                             */
} Solver;

/* ─── Sudoku metadata, read from CNF comments ─────────────────────────────── */
typedef struct { int r, c, v; } VarEntry;  /* all 1-indexed                  */

static int       N             = 0;
static VarEntry *var_info      = NULL;     /* var_info[dimacs_var] -> (r,c,v) */
static int       var_info_cap  = 0;

/* fixed cells stored as flat int triples: [r0, c0, v0, r1, c1, v1, ...]     */
static int *fixed_flat  = NULL;
static int  fixed_count = 0;
static int  fixed_cap   = 0;

static Solver solver;

/* ══════════════════════════════════════════════════════════════════════════ */
/* Utility                                                                    */
/* ══════════════════════════════════════════════════════════════════════════ */

static inline int absval(int x) { return x > 0 ? x : -x; }

static inline int lit_value(int lit) {
    int var = absval(lit);
    int val = solver.assignment[var];
    if (val == UNASSIGNED) return UNASSIGNED;
    return (lit > 0) ? val : !val;
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* Clause management (dynamic)                                                */
/* ══════════════════════════════════════════════════════════════════════════ */

static void add_clause(int *lits, int size) {
    if (solver.num_clauses >= solver.clause_cap) {
        solver.clause_cap *= 2;
        solver.clauses = realloc(solver.clauses,
                                 (size_t)solver.clause_cap * sizeof(Clause));
        if (!solver.clauses) { fprintf(stderr, "OOM: clauses\n"); exit(1); }
    }
    Clause *c  = &solver.clauses[solver.num_clauses++];
    c->size    = size;
    c->lits    = malloc((size_t)size * sizeof(int));
    if (!c->lits) { fprintf(stderr, "OOM: clause lits\n"); exit(1); }
    memcpy(c->lits, lits, (size_t)size * sizeof(int));
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* Assignment                                                                 */
/* ══════════════════════════════════════════════════════════════════════════ */

static void assign(int lit, int level, int reason_clause) {
    int var = absval(lit);
    solver.assignment[var] = (lit > 0) ? 1 : 0;
    solver.level_of[var]   = level;
    solver.reason[var]     = reason_clause;
    solver.trail[solver.trail_top++] = lit;
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* Unit propagation                                                           */
/* Returns first conflict clause index, or -1.                               */
/* ══════════════════════════════════════════════════════════════════════════ */

static int propagate(void) {
    bool changed = true;
    while (changed) {
        changed = false;
        for (int i = 0; i < solver.num_clauses; i++) {
            Clause *c = &solver.clauses[i];
            int unassigned = 0, last_lit = 0;
            bool satisfied = false;

            for (int j = 0; j < c->size; j++) {
                int val = lit_value(c->lits[j]);
                if (val == 1)          { satisfied = true; break; }
                if (val == UNASSIGNED) { unassigned++; last_lit = c->lits[j]; }
            }
            if (satisfied)     continue;
            if (unassigned == 0) return i;        /* conflict               */
            if (unassigned == 1) {
                assign(last_lit, solver.level, i);
                changed = true;
            }
        }
    }
    return -1;
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* Decision — first unassigned variable, positive polarity                   */
/* ══════════════════════════════════════════════════════════════════════════ */

static int decide(void) {
    for (int i = 1; i <= solver.num_vars; i++)
        if (solver.assignment[i] == UNASSIGNED)
            return i;
    return 0;
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* Backtrack to given level                                                   */
/* ══════════════════════════════════════════════════════════════════════════ */

static void backtrack(int level) {
    while (solver.trail_top > 0) {
        int lit = solver.trail[solver.trail_top - 1];
        int var = absval(lit);
        if (solver.level_of[var] <= level) break;
        solver.assignment[var] = UNASSIGNED;
        solver.reason[var]     = -1;
        solver.level_of[var]   = 0;
        solver.trail_top--;
    }
    solver.level = level;
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* First-UIP conflict analysis                                                */
/* Adds learned clause, returns backtrack level.                             */
/* ══════════════════════════════════════════════════════════════════════════ */

static int analyze(int conflict_clause) {
    /*
     * Use a generation counter instead of memset to clear seen[]:
     *   gen_of[v] == cur_gen  means  seen[v] is active.
     */
    static int seen[MAX_VARS + 1];
    static int gen_of[MAX_VARS + 1];
    static int cur_gen = 0;
    cur_gen++;

    static int learned[MAX_LIT_BUF];
    int size    = 0;
    int counter = 0;
    int idx     = solver.trail_top - 1;

    /* initialise with conflict clause */
    Clause *c = &solver.clauses[conflict_clause];
    for (int i = 0; i < c->size; i++) {
        int v = absval(c->lits[i]);
        if (gen_of[v] != cur_gen) {
            gen_of[v] = cur_gen; seen[v] = 1;
            if (solver.level_of[v] == solver.level) counter++;
        }
    }

    /* resolve until one literal at current level remains (the UIP) */
    while (counter > 1) {
        while (gen_of[absval(solver.trail[idx])] != cur_gen ||
               !seen[absval(solver.trail[idx])])
            idx--;

        int lit = solver.trail[idx--];
        int v   = absval(lit);
        seen[v] = 0;
        counter--;

        int rc = solver.reason[v];
        if (rc < 0) continue;

        Clause *rc_c = &solver.clauses[rc];
        for (int i = 0; i < rc_c->size; i++) {
            int vv = absval(rc_c->lits[i]);
            if (gen_of[vv] != cur_gen) {
                gen_of[vv] = cur_gen; seen[vv] = 1;
                if (solver.level_of[vv] == solver.level) counter++;
            }
        }
    }

    /* build learned clause */
    int backtrack_level = 0;
    for (int v = 1; v <= solver.num_vars; v++) {
        if (gen_of[v] != cur_gen || !seen[v]) continue;
        int lit = (solver.assignment[v] == 1) ? -v : v;
        if (size < MAX_LIT_BUF) learned[size++] = lit;
        if (solver.level_of[v] != solver.level &&
            solver.level_of[v] > backtrack_level)
            backtrack_level = solver.level_of[v];
    }

    add_clause(learned, size);
    return backtrack_level;
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* CDCL main loop                                                             */
/* ══════════════════════════════════════════════════════════════════════════ */

static int solve(void) {
    solver.level = 0;
    for (;;) {
        int conflict = propagate();
        if (conflict >= 0) {
            if (solver.level == 0) return UNSAT;
            int bt = analyze(conflict);
            backtrack(bt);
            continue;
        }
        int var = decide();
        if (var == 0) return SAT;
        solver.level++;
        assign(var, solver.level, -1);
    }
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* DIMACS parser — reads clause lines AND c SIZE / c MAP / c FIXED comments  */
/* ══════════════════════════════════════════════════════════════════════════ */

static void ensure_var_info(int var) {
    if (var < var_info_cap) return;
    int new_cap = var_info_cap ? var_info_cap * 2 : 1024;
    while (new_cap <= var) new_cap *= 2;
    var_info = realloc(var_info, (size_t)new_cap * sizeof(VarEntry));
    if (!var_info) { fprintf(stderr, "OOM: var_info\n"); exit(1); }
    memset(var_info + var_info_cap, 0,
           (size_t)(new_cap - var_info_cap) * sizeof(VarEntry));
    var_info_cap = new_cap;
}

static void push_fixed(int r, int c, int v) {
    if (fixed_count * 3 + 3 > fixed_cap) {
        fixed_cap = fixed_cap ? fixed_cap * 2 : 192;
        fixed_flat = realloc(fixed_flat, (size_t)fixed_cap * sizeof(int));
        if (!fixed_flat) { fprintf(stderr, "OOM: fixed_flat\n"); exit(1); }
    }
    fixed_flat[fixed_count * 3 + 0] = r;
    fixed_flat[fixed_count * 3 + 1] = c;
    fixed_flat[fixed_count * 3 + 2] = v;
    fixed_count++;
}

static void parse_dimacs(FILE *f) {
    char line[8192];
    int  lits[MAX_LIT_BUF];

    solver.clause_cap  = INIT_CLAUSES;
    solver.clauses     = malloc((size_t)INIT_CLAUSES * sizeof(Clause));
    solver.num_clauses = 0;

    while (fgets(line, sizeof(line), f)) {

        /* ── comment line ──────────────────────────────────────────────── */
        if (line[0] == 'c') {
            int vi, r, c, v;
            if      (sscanf(line, "c SIZE %d",           &v)          == 1) { N = v; }
            else if (sscanf(line, "c MAP %d %d %d %d",  &vi,&r,&c,&v) == 4) {
                ensure_var_info(vi);
                var_info[vi] = (VarEntry){r, c, v};
            }
            else if (sscanf(line, "c FIXED %d %d %d",   &r,&c,&v)    == 3) {
                push_fixed(r, c, v);
            }
            continue;
        }

        /* ── problem line ──────────────────────────────────────────────── */
        if (line[0] == 'p') {
            int dv, dc;
            sscanf(line, "p cnf %d %d", &dv, &dc);
            solver.num_vars   = dv;
            solver.assignment = malloc((size_t)(dv + 1) * sizeof(int));
            solver.level_of   = calloc((size_t)(dv + 1), sizeof(int));
            solver.reason     = malloc((size_t)(dv + 1) * sizeof(int));
            solver.trail      = malloc((size_t)(dv + 1) * sizeof(int));
            if (!solver.assignment||!solver.level_of||
                !solver.reason    ||!solver.trail) {
                fprintf(stderr,"OOM: solver arrays\n"); exit(1);
            }
            for (int i = 0; i <= dv; i++) {
                solver.assignment[i] = UNASSIGNED;
                solver.reason[i]     = -1;
            }
            continue;
        }

        /* ── clause line ───────────────────────────────────────────────── */
        int count = 0;
        char *tok = strtok(line, " \t\n");
        while (tok) {
            int lit = atoi(tok);
            if (lit == 0) break;
            if (count < MAX_LIT_BUF) lits[count++] = lit;
            tok = strtok(NULL, " \t\n");
        }
        if (count > 0) add_clause(lits, count);
    }
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* Print DIMACS-style result                                                  */
/* ══════════════════════════════════════════════════════════════════════════ */

static void print_result(int res) {
    if (res == SAT) {
        printf("SAT\nv ");
        for (int i = 1; i <= solver.num_vars; i++) {
            if      (solver.assignment[i] == 1) printf("%d ",  i);
            else if (solver.assignment[i] == 0) printf("-%d ", i);
            else                                printf("%d ",  i);
        }
        printf("0\n");
    } else {
        printf("UNSAT\n");
    }
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* Decode and pretty-print the Sudoku grid                                    */
/*                                                                            */
/*  Steps:                                                                    */
/*    1. Allocate N×N grid, zero-filled.                                      */
/*    2. Stamp in FIXED cells (pre-assigned, not in SAT variables).           */
/*    3. For each SAT variable assigned TRUE, use var_info[] to find          */
/*       which cell and value it represents, stamp into grid.                 */
/* ══════════════════════════════════════════════════════════════════════════ */

static void decode_and_print_sudoku(void) {
    if (N <= 0) {
        printf("(Sudoku decode skipped: no 'c SIZE N' comment found in CNF)\n");
        return;
    }

    /* ── allocate grid ──────────────────────────────────────────────────── */
    int **grid = malloc((size_t)N * sizeof(int *));
    for (int i = 0; i < N; i++)
        grid[i] = calloc((size_t)N, sizeof(int));

    /* ── stamp fixed (pre-assigned) cells ───────────────────────────────── */
    for (int i = 0; i < fixed_count; i++) {
        int r = fixed_flat[i*3],  c = fixed_flat[i*3+1],  v = fixed_flat[i*3+2];
        if (r >= 1 && r <= N && c >= 1 && c <= N)
            grid[r-1][c-1] = v;
    }

    /* ── stamp free variables that were assigned TRUE ────────────────────── */
    int conflicts = 0;
    for (int var = 1; var <= solver.num_vars; var++) {
        if (solver.assignment[var] != 1) continue;
        if (var >= var_info_cap)          continue;

        VarEntry *e = &var_info[var];
        if (e->r < 1 || e->r > N || e->c < 1 || e->c > N || e->v < 1) continue;

        int existing = grid[e->r - 1][e->c - 1];
        if (existing != 0 && existing != e->v) {
            fprintf(stderr,
                "DECODE CONFLICT cell(%d,%d): existing=%d new=%d var=%d\n",
                e->r, e->c, existing, e->v, var);
            conflicts++;
        }
        grid[e->r - 1][e->c - 1] = e->v;
    }
    if (conflicts)
        fprintf(stderr, "WARNING: %d decode conflicts detected.\n", conflicts);

    /* ── pretty-print ───────────────────────────────────────────────────── */
    printf("\nSudoku solution (%dx%d):\n\n", N, N);

    /* box width = smallest integer whose square >= N */
    int base = 1;
    while (base * base < N) base++;

    for (int r = 0; r < N; r++) {
        /* horizontal separator between box rows */
        if (r > 0 && r % base == 0) {
            int dashes = N * 2 + (N / base - 1) * 2;
            for (int i = 0; i < dashes; i++) putchar('-');
            putchar('\n');
        }
        for (int c = 0; c < N; c++) {
            /* vertical separator between box columns */
            if (c > 0 && c % base == 0) printf("| ");

            int val = grid[r][c];
            if      (val == 0)  printf(". ");
            else if (val <= 9)  printf("%d ", val);
            else                printf("%c ", 'A' + val - 10);
        }
        putchar('\n');
    }

    /* ── cleanup ────────────────────────────────────────────────────────── */
    for (int i = 0; i < N; i++) free(grid[i]);
    free(grid);
}

/* ══════════════════════════════════════════════════════════════════════════ */
/* main                                                                       */
/* ══════════════════════════════════════════════════════════════════════════ */

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s file.cnf\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (!f) { fprintf(stderr, "Cannot open file: %s\n", argv[1]); return 1; }

    parse_dimacs(f);
    fclose(f);

    int res = solve();
    print_result(res);

    if (res == SAT)
        decode_and_print_sudoku();

    /* ── cleanup ──────────────────────────────────────────────────────── */
    for (int i = 0; i < solver.num_clauses; i++) free(solver.clauses[i].lits);
    free(solver.clauses);
    free(solver.assignment);
    free(solver.level_of);
    free(solver.reason);
    free(solver.trail);
    free(var_info);
    free(fixed_flat);

    return 0;
}