/** Copyright (C) 2020,  Gavin J Stark.  All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * @file   srams.cpp
 * @brief  SRAM CDL module creation
 *
 * This file is loaded in to a CDL simulation environment, and it uses
 * the simulation libraries to create a set of SRAMs that can be
 * instantiated by the simulation. The SRAMs are hard-coded here, so
 * if a design requires a new SRAM then it should be added in to this
 * file.
 *
 * In an ASIC or FPGA the SRAM modules should be supplied by
 * libraries; this file is effectively simulation library support.
 */

/*a Includes */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "be_model_includes.h"
#include "sl_general.h"

/*a Defines */
/**
 * A macro to define the wrapper for an SRAM of a defined size and width, with full width write enable
 */
#define SRAM_WRAPPER(size,width,bpe)                                       \
static t_sl_error_level se_sram_srw_ ## size ## x ## width ## _ ## bpe ## _instance_fn(c_engine *engine, void *engine_handle) { \
    engine->set_option_list( engine_handle, sl_option_list(engine->get_option_list( engine_handle ), "size", size) ); \
    engine->set_option_list( engine_handle, sl_option_list(engine->get_option_list( engine_handle ), "width", width) ); \
    engine->set_option_list( engine_handle, sl_option_list(engine->get_option_list( engine_handle ), "bits_per_enable", bpe) ); \
    void *sram_mod = se_external_module_find("se_sram_srw"); \
    if (sram_mod) return se_external_module_instantiate(sram_mod, engine, engine_handle); \
    return error_level_fatal; \
}
#define SRAM_WRAPPER_DP(size,width) \
static t_sl_error_level se_sram_mrw_2_ ## size ## x ## width ## _instance_fn(c_engine *engine, void *engine_handle) { \
    engine->set_option_list( engine_handle, sl_option_list(engine->get_option_list( engine_handle ), "num_ports", 2) ); \
    engine->set_option_list( engine_handle, sl_option_list(engine->get_option_list( engine_handle ), "size", size) ); \
    engine->set_option_list( engine_handle, sl_option_list(engine->get_option_list( engine_handle ), "width", width) ); \
    engine->set_option_list( engine_handle, sl_option_list(engine->get_option_list( engine_handle ), "bits_per_enable", 0) ); \
    void *sram_mod = se_external_module_find("se_sram_mrw"); \
    if (sram_mod) return se_external_module_instantiate(sram_mod, engine, engine_handle); \
    return error_level_fatal; \
}

/**
 * A macro to be used in 'srams__init' to register an SRAM whose
 * 'SRAM_WRAPPER' has been declared
 */
#define SRAM_REGISTER(size,width,bpe)                                      \
    se_external_module_register( 1, "se_sram_srw_" #size "x" #width, se_sram_srw_ ## size ## x ## width ## _ ## bpe ## _instance_fn );
#define SRAM_REGISTER_WE(size,width,bpe)                                      \
    se_external_module_register( 1, "se_sram_srw_" #size "x" #width "_we" #bpe, se_sram_srw_ ## size ## x ## width ## _ ## bpe ## _instance_fn );
#define SRAM_REGISTER_DP(size,width) \
    se_external_module_register( 1, "se_sram_mrw_2_" #size "x" #width, se_sram_mrw_2_ ## size ## x ## width ##_instance_fn );

/*a Static SRAM wrappers */
/**
 * Use the SRAM_WRAPPER macro to create instantiation functions that
 * can be registered with CDL, for all the required SRAMs.
 */
SRAM_WRAPPER(65536, 16, 16)

/*a Initialization functions */
/*f rams__init */
/**
 * Externally visible function invoked by simulation harness with this
 * is loaded in to simulation, to register them SRAM modules so they
 * may be instantiated
 */
extern void
rams__init( void )
{
    SRAM_REGISTER(65536, 16, 16);
}

/*a Scripting support code */
/*f initsrams */
/**
 * Externally visible function invoked by simulation harness with this
 * is loaded in to simulation, to register them SRAM modules so they
 * may be instantiated
 */
extern "C" void initrams( void )
{
    rams__init( );
    scripting_init_module( "rams" );
}
