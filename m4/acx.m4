dnl Support the --with-pkgprovider configure option.
dnl ACX_PKGVERSION(default-pkgprovider)
AC_DEFUN([ACX_PKGPROVIDER],[
  AC_ARG_WITH(pkgprovider,
    AS_HELP_STRING([--with-pkgprovider=ORGANIZATION],
                   [Use ORGANIZATION in the provider string in place of "$1"]),
    [case "$withval" in
      yes) AC_MSG_ERROR([package provider not specified]) ;;
      no)  PKGPROVIDER= ;;
      *)   PKGPROVIDER="$withval" ;;
     esac],
    PKGPROVIDER="$1"
    DEFAULTPROVIDER="$1"
  )
  AC_SUBST(PKGPROVIDER)
  AC_SUBST(DEFAULTPROVIDER)
])


dnl Support the --with-bugurl configure option.
dnl ACX_BUGURL(default-bugurl)
AC_DEFUN([ACX_BUGURL],[
  AC_ARG_WITH(bugurl,
    AS_HELP_STRING([--with-bugurl=URL],
                   [Direct users to URL to report a bug]),
    [case "$withval" in
      yes) AC_MSG_ERROR([bug URL not specified]) ;;
      no)  BUGURL=
           ;;
      *)   BUGURL="$withval"
           ;;
     esac],
     BUGURL="$1"
  )
  case ${BUGURL} in
  "")
    REPORT_BUGS_TO=
    ;;
  *)
    REPORT_BUGS_TO="<$BUGURL>"
    ;;
  esac;
  AC_SUBST(REPORT_BUGS_TO)
])


AC_DEFUN([ACX_GIT_COMMIT_SHA1],[
    AC_MSG_CHECKING(for Git commit SHA1)
    GIT_COMMIT_SHA1=$(git rev-parse --short HEAD 2> /dev/null)
    if test $? -eq 0;
    then
        :
    else
        GIT_COMMIT_SHA1="unknown"
        broken_git="true"
    fi

    if test "$broken_git" != "true"; then
        git_version=$(git version | cut -d' ' -f3)
        major_version=$(echo $git_version | cut -d'.' -f1)
        minor_version=$(echo $git_version | cut -d'.' -f2)
        bugfix_version=$(echo $git_version | cut -d'.' -f3)

        if test "$major_version" -le 1 || test "$minor_version" -le 7 || test "$bugfix_version" -le 2; then
            # pretty old git...
            submodule_syntax="--ignore-submodules=dirty"
        else
            submodule_syntax=""
        fi

        git_status=$(git status -s ${submodule_syntax} 2> /dev/null | tail -n1)
        if test -n "$git_status"; then
            GIT_COMMIT_SHA1="${GIT_COMMIT_SHA1}-dirty"
        fi
    fi

    AC_MSG_RESULT($GIT_COMMIT_SHA1)
    AC_SUBST(GIT_COMMIT_SHA1)
])
