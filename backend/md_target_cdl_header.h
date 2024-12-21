/*a Copyright
  
  This file 'md_target_cdl_header.h' copyright Gavin J Stark 2003-2020
  
  This program is free software; you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation, version 2.0.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
  for more details.
*/
/*a Wrapper
 */
#ifdef __INC_MD_TARGET_CDLH
#else
#define __INC_MD_TARGET_CDLH

/*a Includes
 */
#include "c_md_target.h"
#include "c_model_descriptor.h"

/*a Subclass of c_md_target for CDL headers */
/*c Class c_md_target_cdlh */
class c_md_target_cdlh: public c_md_target {
    void output_ports_nets_clocks(t_md_module *module, int include_all_clocks);    
public:
    c_md_target_cdlh(class c_model_descriptor *model, t_md_output_fn output_fn, void *output_handle):
        c_md_target(model, output_fn, output_handle) {}
    void output_cdlh_model(void);
};

/*a Wrapper
 */
#endif

