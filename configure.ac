AC_INIT([CDL compiler],[2.0])
AC_CONFIG_AUX_DIR([build-aux])
AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([Makefile_build_config])
AC_CONFIG_FILES([scripts/Makefile_cdl_template_config])

AC_CHECK_HEADER([stdio.h],
  [AC_DEFINE([HAVE_STDIO_H], [1],
    [Define to 1 if you have <stdio.h>])],
  [AC_MSG_ERROR([Sorry...])])

AC_PROG_INSTALL
AC_SUBST(INSTALL_PROGRAM)
AC_SUBST(INSTALL_DATA)

AC_LANG([C++])
# AX_CXX_COMPILE_STDCXX_11

AC_PROG_YACC
AC_PATH_PROG(YACC_INST, $YACC)
if test -z "$YACC_INST"; then
   AC_MSG_ERROR([yacc not found])
fi

AM_PATH_PYTHON([3])
AC_ARG_VAR([PYTHON_INCLUDE], [Include flags for python, bypassing python3-config])
AC_ARG_VAR([PYTHON_CONFIG],  [Path to python3-config])
AS_IF([test -z "$PYTHON_INCLUDE"], [
  AS_IF([test -z "$PYTHON_CONFIG"], [
    AC_PATH_PROGS([PYTHON_CONFIG],
                  [python$PYTHON_VERSION-config python-config],
                  [no],
                  [`dirname $PYTHON`])
    AS_IF([test "$PYTHON_CONFIG" = no], [AC_MSG_ERROR([cannot find python-config for $PYTHON.])])
  ])
  AC_MSG_CHECKING([python include flags])
  PYTHON_INCLUDE=`$PYTHON_CONFIG --includes`
  AC_MSG_RESULT([:$PYTHON_INCLUDE])
  AC_MSG_CHECKING([python library flags])
  PYTHON_LIBS=`$PYTHON_CONFIG --ldflags`
  AC_MSG_RESULT([:$PYTHON_LIBS])
])
AC_SUBST([PYTHON_INCLUDE])
AC_SUBST([PYTHON_LIBS])

AC_CANONICAL_HOST
os_cxxflags="-fPIC"
os_cflags="-fPIC"

dynamic_library_flags="-shared"
pthread_cflags="-pthread"
pthread_cxxflags="-pthread"
make_static_binary="\${CXX} \${CXXFLAGS} -o"
make_static_library="ar rcs "
make_dynamic_library="\${CXX} $dynamic_library_flags -o"
case $host_os in
  darwin* )
    os_cxxflags=""
    os_cflags=""
    dynamic_library_flags="-bundle"
    pthread_cflags=""
    pthread_cxxflags=""
    # possibly also LINKFLAGS but that may be old
    make_static_binary="\${CXX} \${CXXFLAGS} -o"
    make_static_library="libtool -static -o "
    make_dynamic_library="\${CXX} $dynamic_library_flags -o"
esac
OS_CFLAGS="$os_cflags"
OS_CXXFLAGS="$os_cxxflags"
AC_SUBST([OS_CFLAGS])
AC_SUBST([OS_CXXFLAGS])

MAKE_STATIC_BINARY=$make_static_binary
MAKE_STATIC_LIBRARY=$make_static_library
MAKE_DYNAMIC_LIBRARY=$make_dynamic_library
AC_SUBST([MAKE_STATIC_BINARY])
AC_SUBST([MAKE_STATIC_LIBRARY])
AC_SUBST([MAKE_DYNAMIC_LIBRARY])

PTHREAD_CFLAGS="$pthread_cflags"
PTHREAD_CXXFLAGS="$pthread_cxxflags"
AC_SUBST([PTHREAD_CFLAGS])
AC_SUBST([PTHREAD_CXXFLAGS])


BUILD_VERILATED="no"
AC_ARG_VAR([VERILATOR_ROOT],  [Path to bin/verilator*])
AC_ARG_VAR([VERILATOR_SHARE], [Path to include/verilated.h etc])
AS_IF([test "x$ac_cv_env_VERILATOR_ROOT" == x],
  [ AC_PATH_PROG([VERILATOR_BIN],[verilator],[verilator_not_found])
    AS_IF([test "$ac_cv_path_VERILATOR_BIN" = "verilator_not_found"],
      [AC_MSG_WARN(['verilator' not found - not including verilator support; add verilator to the path or set VERILATOR_ROOT and VERILATOR_SHARE when configuring])],
      [ ac_cv_env_VERILATOR_ROOT="$(dirname $(dirname $ac_cv_path_VERILATOR_BIN))"
        ac_cv_env_VERILATOR_SHARE="$ac_cv_env_VERILATOR_ROOT/share/verilator"
      ])
    ]
)
AC_MSG_CHECKING([Verilator])
AS_IF([test "x$ac_cv_env_VERILATOR_ROOT" != x],
      [AS_IF([test -x "$ac_cv_env_VERILATOR_ROOT/bin/verilator"],
             [],
             [AC_MSG_ERROR([VERILATOR_ROOT of '$ac_cv_env_VERILATOR_ROOT' does not contain bin/verilator])]
            )]
      [AS_IF([test -f "$ac_cv_env_VERILATOR_SHARE/include/verilated.h"],
             [],
             [AC_MSG_ERROR([VERILATOR_SHARE of '$ac_cv_env_VERILATOR_SHARE' does not contain include/verilated.h])]
            )]
     VERILATOR_ROOT=$ac_cv_env_VERILATOR_ROOT
     VERILATOR_SHARE=$ac_cv_env_VERILATOR_SHARE
     BUILD_VERILATED="yes"
     AC_MSG_RESULT([:$VERILATOR_SHARE ; $VERILATOR_ROOT])
     ,
     AC_MSG_RESULT([not being supported])
     )
AC_SUBST([BUILD_VERILATED])

AC_OUTPUT


dnl AC_CHECK_HEADERS([png.h])
dnl AC_CHECK_HEADERS([noway.h])
dnl AC_SEARCH_LIBS([png_get_io_ptr],[png],,[AC_MSG_ERROR([Sorry... no libpng])])
dnl AC_SEARCH_LIBS([jpeg_CreateDecompress], [jpeg],,[AC_MSG_ERROR([Sorry... no libjpeg])])
dnl AC_PATH_PROG([CYCLICITY],[bin/linux/cdl],[not_found])
dnl AS_IF([test "$ac_cv_path_CYCLICITY" = "not_found"],[AC_MSG_ERROR(['cdl' not found - try using CYCLICITY=/path/to/cdl])])
