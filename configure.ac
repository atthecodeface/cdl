AC_INIT([CDL compiler],[1.0])

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

os_cxxflags="-fPIC"
os_cflags="-fPIC"
dynamic_library_flags="-shared"
pthread_cflags="-pthread"
pthread_cxxflags="-pthread"
case $host_os in
  darwin* )
    os_cxxflags=""
    os_cflags=""
    dynamic_library_flags="-bundle"
    pthread_cflags=""
    pthread_cxxflags=""
esac
OS_CFLAGS="$os_cflags"
OS_CXXFLAGS="$os_cxxflags"
AC_SUBST([OS_CFLAGS])
AC_SUBST([OS_CXXFLAGS])

MAKE_STATIC_BINARY="\${CXX} \${CXXFLAGS} -o"
MAKE_STATIC_LIBRARY="ar rcs "
MAKE_DYNAMIC_LIBRARY="\${CXX} $dynamic_library_flags -o"
AC_SUBST([MAKE_STATIC_BINARY])
AC_SUBST([MAKE_STATIC_LIBRARY])
AC_SUBST([MAKE_DYNAMIC_LIBRARY])

PTHREAD_CFLAGS="$pthread_cflags"
PTHREAD_CXXFLAGS="$pthread_cxxflags"
AC_SUBST([PTHREAD_CFLAGS])
AC_SUBST([PTHREAD_CXXFLAGS])

AC_OUTPUT

