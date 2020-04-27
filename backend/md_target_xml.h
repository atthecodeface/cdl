/*a Copyright
  
  This file 'md_target_xml.h' copyright Gavin J Stark 2003, 2004
  
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
#ifdef __INC_MD_TARGET_XML
#else
#define __INC_MD_TARGET_XML

/*a Includes
 */
#include "c_md_target.h"
#include "c_model_descriptor.h"

/*a Subclass of c_md_target for Xml */
/*c Class c_md_target_xml */
class c_md_target_xml: public c_md_target {
public:
    c_md_target_xml(class c_model_descriptor *model, t_md_output_fn output_fn, void *output_handle):
        c_md_target(model, output_fn, output_handle) {}
    void output_xml_model(void);
};

/*a Wrapper
 */
#endif
