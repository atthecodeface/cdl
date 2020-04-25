/*a Copyright
  
This file 'se_wrapped_verilator.cpp' copyright Gavin J Stark 2020
  
This is free software; you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free Software
Foundation, version 2.1.
  
This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
for more details.
*/

/*a Includes
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <cstddef>
#include <map>
#include "se_wrapped_verilator.h"
#include "sl_debug.h"
#include "c_sl_error.h"
#include "c_se_engine.h"
#include "se_errors.h"
#include "sl_mif.h"
#include "se_cmodel_assist.h"

#include "verilated_syms.h"
#include "verilated.h"

/*a Types
 */
/*a Initialization functions
*/
/*a Constructors and destructors for c_se_wrapped_verilator
*/
/*f c_se_wrapped_verilator
*/
double sc_time_stamp(void) { return 0; }
static void mem_write_thing_callback (void *handle, t_sl_uint64 address, t_sl_uint64 *data )
{
    auto vv = (VerilatedVar*)handle;
    auto dptr = vv->datapAdjustIndex(vv->datap(),1,address-vv->right(1));
    ((char *)dptr)[0] = *data;
}

static void debug(class c_engine *engine, void *eng_handle, t_cdl_verilator_desc *desc, void *handle)
{
    auto m = (VerilatedModule *)handle;
    auto name = engine->get_instance_full_name(eng_handle);
    // auto s = new Vbbc_micro_de1_cl__Syms(m, name);
    fprintf(stderr,"Instantiated verilator module type '%s' name '%s' '%s'\n", "bbc_micro_de1_cl" , name, m->name());
    auto p1 = Verilated::scopeFind(m->name());// const VerilatedScope*
    fprintf(stderr,"Scope %p\n", p1 ); // NULL
    auto p = Verilated::scopeFind("tb.bbc_micro_de1_cl.io.ftb.display.ram");// const VerilatedScope*
    fprintf(stderr,"Scope %p\n", p );
    fprintf(stderr,"type %d\n", p->type() );
    fprintf(stderr,"symsp %p\n", p->symsp() );
    auto sn = Verilated::scopeNameMap(); // const VerilatedScopeNameMap*
    fprintf(stderr,"Scope name map %p\n", sn );
    for (auto it = sn->begin(); it != sn->end(); ++it) {
        fprintf(stderr,"name %s ptr %p\n",it->first,it->second);
    }
    auto vv =  p->varFind("ram"); // VerilatedVar*
    fprintf(stderr,"Var name map %p\n", sn );
    auto vsp = p->varsp();
    for (auto it = vsp->begin(); it != vsp->end(); ++it) {
        // fprintf(stderr,"name %s ptr %p\n",it->first,it->second);
    }
    fprintf(stderr,"Var %p type %d size %d data %p dims %d udims %d %d:%d:%d:%d\n", vv, vv->vltype(), vv->entSize(), vv->datap(), vv->dims(), vv->udims(), vv->left(0), vv->right(0), vv->left(1), vv->right(1) );

    sl_mif_read_mif_file( engine->error, "fred.mif", "CDL wrapped verilog",
                          vv->right(1), // address_offset,
                          vv->left(1)-vv->right(1)+1,// t_sl_uint64 size, // size of memory - don't callback if address in file - address_offset is outside the range 0 to size-1
                          0, // int error_on_out_of_range, // add an error on every memory location that is out of range
                          mem_write_thing_callback, (void *)vv );
    // auto x = svGetScopeFromName("tb.bbc_micro_de1_cl.io.ftb.display.ram");
    // fprintf(stderr,"x %p\n",x);
}

class c_sram_module
{
    class c_se_wrapped_verilator *parent;
    char *data;
    ssize_t ram_size;
    int bytes_per_entry;
    int bit_width;
    int num_elements;
    t_sl_uint64 mask;
    int reset_type;
    int reset_value;
    int first_element;
    const char *filename;
public:
    c_sram_module(class c_se_wrapped_verilator *parent, VerilatedVar &vv, int reset_type, int reset_value, const char *filename);
    ~c_sram_module();
    void write(t_sl_uint64 address, t_sl_uint64 *data);
    void reset(void);
};

c_sram_module::c_sram_module(class c_se_wrapped_verilator *parent, VerilatedVar &vv, int reset_type, int reset_value, const char *filename)
{
    char *data = (char *)vv.datap();
    int bit_width = vv.left(0) - vv.right(0);
    int num_elements = vv.left(1) - vv.right(1);
    int first_element = vv.left(1);
    ssize_t ram_size = vv.entSize();
    if (bit_width<0) bit_width=-bit_width;
    if (num_elements<0) num_elements=-num_elements;
    num_elements++;
    if (first_element>vv.right(1)) first_element=vv.right(1);
    t_sl_uint64 mask = ((bit_width==64)?0:(1ULL<<bit_width))-1;

    this->parent = parent;
    this->data = data;
    this->ram_size = ram_size;
    this->bytes_per_entry = bytes_per_entry;
    this->bit_width = bit_width;
    this->num_elements = num_elements;
    this->mask = mask;
    this->reset_type = reset_type;
    this->reset_value = reset_value;
    this->filename = sl_str_alloc_copy(filename);
}
c_sram_module::~c_sram_module()
{
    free((void *)filename);
}

static void sram_write_callback(void *handle, t_sl_uint64 address, t_sl_uint64 *data)
{
    auto sram = (c_sram_module *)handle;
    sram->write(address, data);
}
void c_sram_module::write(t_sl_uint64 address, t_sl_uint64 *write_data)
{
    if (address<first_element) return;
    address -= first_element;
    if (address>=num_elements) return;
    auto value = mask & (*write_data);
    if (bytes_per_entry==1) {
        auto d = (char *)data;
        d[address] = value;
    } else if (bytes_per_entry==2) {
        auto d = (t_sl_uint16 *)data;
        d[address] = value;
    } else if (bytes_per_entry==4) {
        auto d = (t_sl_uint32 *)data;
        d[address] = value;
    } else {
        auto d = (t_sl_uint64 *)data;
        d[address] = value;
    }
}
void c_sram_module::reset()
{
    sl_mif_read_mif_file( parent->engine->error, filename, "CDL wrapped verilog",
                          first_element, // address_offset,
                          num_elements, // t_sl_uint64 size, // size of memory - don't callback if address in file - address_offset is outside the range 0 to size-1
                          0, // int error_on_out_of_range, // add an error on every memory location that is out of range
                          sram_write_callback, (void *)this );
}

void c_se_wrapped_verilator::create_verilated_submodules_with_publics(void)
{
    auto name = module->name();
    int name_len = strlen(name);
    auto sn = Verilated::scopeNameMap();
    for (auto it = sn->begin(); it != sn->end(); ++it) {
        auto sn = it->first;
        if (strncmp(name,sn,name_len)!=0) continue;
        if (sn[name_len]!='.') continue;
        auto sc = it->second;
        auto vsp = sc->varsp();
        for (auto vv = vsp->begin(); vv != vsp->end(); ++vv) {
            create_submodule_for_verilated_var(sn+name_len+1, vv->first, vv->second);
        }
    }
}    

void c_se_wrapped_verilator::create_submodule_for_verilated_var(const char *mp, const char *mn, VerilatedVar &vv)
{
    int bytes_per_entry;
    if ((vv.dims()!=2) || (vv.udims()!=1)) return;
    bytes_per_entry = 0;
    if (vv.vltype()==VLVT_UINT8)  { bytes_per_entry=1; }
    if (vv.vltype()==VLVT_UINT16) { bytes_per_entry=2; }
    if (vv.vltype()==VLVT_UINT32) { bytes_per_entry=4; }
    if (vv.vltype()==VLVT_UINT64) { bytes_per_entry=8; }
    if (bytes_per_entry==0) return;

    int needs_ram;
    auto filename="blah.mif";
    int reset_type = 0;
    int reset_value = 0;
    needs_ram = 1;
    if (needs_ram) {
    auto sram = new c_sram_module(this, vv, reset_type, reset_value, filename);
        sram_list.push_back(sram);
    }
    // filename = engine->get_option_string( engine_handle, "filename", "" );
    // reset_type = engine->get_option_int( engine_handle, "reset_type", 2 );
    // reset_value = engine->get_option_int( engine_handle, "reset_value", 0 );
}

c_se_wrapped_verilator::c_se_wrapped_verilator(class c_engine *eng, void *eng_handle, t_cdl_verilator_desc *desc, VerilatedModule *module)
{
    this->engine        = eng;
    this->engine_handle = eng_handle;
    this->desc          = desc;
    this->module        = module;
    auto module_desc = desc->module_desc;

    create_verilated_submodules_with_publics();
    // enumerate_public_vars((VerilatedModule *)handle,([]{fprintf(stderr,"%s %s %d %d %d\n",mp,mn,vv.vltype(),vv.dims(),vv.udims());}));
    // debug(eng, eng_handle, desc, handle);

    module_data_size  = sizeof(t_cdl_verilator_data);
    module_data_size += desc->all_signals_size;
    num_clks = 0;
    for (int i=0; module_desc->clock_descs_list[i]; i++) {
        num_clks++;
    }
    module_data_size += num_clks*sizeof(int);
    module_data = malloc(module_data_size);
    memset(module_data, 0, module_data_size);
    all_signals  = (t_sl_uint64 *)(((t_cdl_verilator_data *)module_data)+1);
    clock_values = (int *)(((char *)all_signals)+desc->all_signals_size);

    engine->register_delete_function( engine_handle, [this](){delete(this);} );
    engine->register_reset_function( engine_handle,  [this](int pass){this->reset(pass);});
    engine->register_prepreclock_fn( engine_handle,  [this](){this->prepreclock();} );
    for (auto i=0; module_desc->clock_descs_list[i]; i++) {
        engine->register_clock_fns( engine_handle,
                                    module_desc->clock_descs_list[i]->name,
                                    std::bind(&c_se_wrapped_verilator::preclock,this,i,1),
                                    std::bind(&c_se_wrapped_verilator::clock,this,i,1),
                                    std::bind(&c_se_wrapped_verilator::preclock,this,i,0),
                                    std::bind(&c_se_wrapped_verilator::clock,this,i,0) );
    }
    se_cmodel_assist_module_declaration( engine, engine_handle, (void *)all_signals, desc->module_desc );
    //engine->register_state_desc( engine_handle, 1, module_desc->state_desc, &module_data->all_signals, NULL );

    inputs_captured = 0;
}

/*f ~c_se_wrapped_verilator
*/
c_se_wrapped_verilator::~c_se_wrapped_verilator()
{
    delete_instance();
}

/*f c_se_wrapped_verilator::delete_instance
*/
void c_se_wrapped_verilator::delete_instance( void )
{
    callback_list.clear();
    sram_list.clear();
    if (module_data) {
        free(module_data);
        module_data = NULL;
        desc->delete_fn(this);
    }
}

/*a Class reset/preclock/clock methods for c_se_wrapped_verilator
*/
/*f c_se_wrapped_verilator::reset
*/
void c_se_wrapped_verilator::reset( int pass )
{
    for (auto m=sram_list.begin(); m != sram_list.end(); ++m) {
        (*m)->reset();
    }
    if (pass==0) {  // Dont call capture_inputs on first pass as they may be invalid; wait for second pass
        se_cmodel_assist_check_unconnected_inputs(engine, engine_handle, (void *)all_signals, desc->module_desc->input_descs, "bbc_keyboard_csr" );
    } else {
        capture_inputs();
    }
    eval();
    inputs_captured = 0;
}

/*f capture_inputs
*/
void c_se_wrapped_verilator::capture_inputs( void )
{
}

/*f eval
*/
void c_se_wrapped_verilator::eval( void )
{
    desc->eval_fn(this);
}

/*f prepreclock
*/
void c_se_wrapped_verilator::prepreclock( void )
{
    inputs_captured = 0;
    eval_invoked = 0;
}

/*f preclock
*/
void c_se_wrapped_verilator::preclock(int clock, int posedge)
{
    if (!inputs_captured) { capture_inputs(); inputs_captured++; }
    clock_values[clock] = posedge;
}

/*f clock
*/
void c_se_wrapped_verilator::clock(int clock, int posedge)
{
    if (!eval_invoked) { eval(); eval_invoked=1; }
}

