AC_INIT([CDL compiler],[1.0])

AC_CONFIG_FILES([Makefile_build_config])
AC_CONFIG_HEADERS([config.h])

AC_CHECK_HEADER([stdio.h],
  [AC_DEFINE([HAVE_STDIO_H], [1],
    [Define to 1 if you have <stdio.h>])],
  [AC_MSG_ERROR([Sorry...])])

AC_PROG_INSTALL
AC_SUBST(INSTALL_PROGRAM)
AC_SUBST(INSTALL_DATA)

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
  AC_MSG_RESULT([$PYTHON_INCLUDE])
])

AC_OUTPUT

