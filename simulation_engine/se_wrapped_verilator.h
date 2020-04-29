/*a Copyright
  
This file 'se_wrapped_verilator.h' copyright Gavin J Stark 2020
  
This is free software; you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free Software
Foundation, version 2.1.
  
This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
for more details.
*/
/*a Wrapper
 */
#ifdef __INC_SE_WRAPPED_VERILATOR
#else
#define __INC_SE_WRAPPED_VERILATOR

/*a Includes */
#include "c_se_engine.h"
#include "se_cmodel_assist.h"
#include <functional>
#include <list>
#include <memory>

/*a Types
 */
/*t t_cvd_clock_desc
 */
typedef struct t_cvd_clock_desc {
    const char *name;
} t_cvd_clock_desc;

/*t t_cdl_verilator_desc
 */
typedef struct t_cdl_verilator_desc {
    int               all_signals_size;
    void (*eval_fn)(class c_se_wrapped_verilator *cvd, int clocks_to_toggle);
    void (*delete_fn)(class c_se_wrapped_verilator *cvd);
    t_se_cma_module_desc *module_desc;
} t_cdl_verilator_desc;

/*t t_cdl_verilator_data
 */
typedef void *t_cdl_verilator_data;

typedef std::unique_ptr<t_se_engine_std_function> t_uniq_efn;
typedef class c_sram_module* t_sram_uniq_ptr;

/*t t_module_data
 */
class c_se_wrapped_verilator {
private:
    t_cdl_verilator_desc *desc;

    std::list<t_uniq_efn> callback_list;
    std::list<t_sram_uniq_ptr> sram_list;
    // Following deduced from desc
    int module_data_size; // Size of data to be allocated in module_data
    int num_clks;         // Number of clocks in desc
    
    // Memory allocated due to desc
    void *module_data; // Ownership point for data allocated
    class VerilatedModule *module; // Client verilated module
    t_sl_uint64 *all_signals; // Data of size 'desc->all_signals_size' for client within module_data
    int *clock_values; // Levels of clock signals - one per clock - zero or one each - within module_data

    t_se_engine_std_function *add_callback(t_se_engine_std_function fn);
    
    // Per-clock-edge data
    int inputs_captured;
    int eval_invoked;
    int clocks_to_toggle;
    void delete_instance(void);
    void capture_inputs(void);
    void eval(int clocks_to_toggle);
    void prepreclock(void);
    void create_submodule_for_verilated_var(const char *mp, const char *mn, class VerilatedVar &vv);
    void create_verilated_submodules_with_publics(void);
    
public:
    class c_engine *engine;
    void *engine_handle;
    void preclock(int clock, int posedge);
    void clock(int clock, int posedge);
    void reset( int pass );
    c_se_wrapped_verilator(class c_engine *eng, void *eng_handle, t_cdl_verilator_desc *cv_desc, class VerilatedModule *handle);
    ~c_se_wrapped_verilator();
    inline class VerilatedModule *get_module(void) const {return module;};
    inline t_sl_uint64 *get_all_signals(void) const {return all_signals;};
    inline int get_clock_value(int n) const {return clock_values[n];};
};


/*a Wrapper
 */
#endif

