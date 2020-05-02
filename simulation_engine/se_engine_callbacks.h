/*a Copyright
  
  This file 'se_engine_function.h' copyright Gavin J Stark 2003, 2004
  
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
#ifdef __INC_ENGINE__SE_ENGINE_CALLBACKS
#else
#define __INC_ENGINE__SE_ENGINE_CALLBACKS

/*a Includes
 */
#include <list>
#include "c_se_engine.h"

/*a Callback template class
 */
template <typename T, typename ...As>
class c_se_engine_callbacks {
    std::list<T> entries;
    t_sl_timer timer;
    int invocation_count;
public:
    c_se_engine_callbacks() {};
    ~c_se_engine_callbacks() {};
    void add(T t) {entries.push_back(t);};
    void clear()  {entries.clear();};
    int empty() {return entries.empty();}
    std::list<T> e() {return entries;};
    typename std::list<T>::iterator begin() {return entries.begin();};
    typename std::list<T>::iterator end()   {return entries.end();};
    void invoke_all(As... args) { SL_TIMER_ENTRY(timer); for (auto &x:entries) { x(args...); }; SL_TIMER_EXIT(timer); }
};
typedef class c_se_engine_callbacks<t_se_engine_std_function>                 c_se_engine_callbacks_void;
typedef class c_se_engine_callbacks<t_se_engine_int_std_function, int>        c_se_engine_callbacks_int;
typedef class c_se_engine_callbacks<t_se_engine_voidp_std_function, void*> c_se_engine_callbacks_voidp;
typedef class c_se_engine_callbacks<t_se_engine_msg_std_function, t_se_message *> c_se_engine_callbacks_msg;

/*a Wrapper
 */
#endif

/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/

