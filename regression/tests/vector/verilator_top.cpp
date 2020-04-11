#include <verilated.h>
#include "Vvector_test_harness.h"
int main(int argc, char** argv, char** env) {
    (void) argc;
    (void) argv;
    (void) env;
    int clks;

    Vvector_test_harness* m = new Vvector_test_harness;
    m->reset_l = 0;
    m->clk = 0;
    clks = 0;
    while (!Verilated::gotFinish() && (clks<40)) {
        clks++;
        m->clk = !m->clk;
        if ((!m->clk) && (clks>10)) {
            m->reset_l = 1;
        }
        m->eval();
    }
    m->final();
    delete m;
    return 0;
}
