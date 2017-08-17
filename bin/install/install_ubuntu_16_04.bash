#!/usr/bin/env bash
# ====================[ install_ubuntu_16_04.bash          ]====================
#
# --------------------( SYNOPSIS                           )--------------------
# Bash shell script automating the installation of BETSEE and all mandatory and
# optional dependencies thereof (e.g., PySide2 and BETSE) for all Ubuntu Linux
# releases newer than or equal to Ubuntu 16.04 (Xenial Xerus).
#
# --------------------( USAGE                              )--------------------
# ./install_ubuntu_16_04.bash [INSTALL_DIR]
#
# Installs both BETSEE and BETSE to the passed installation directory,
# defaulting to the common "${HOME}/Applications" directory if unpassed. This
# directory and all parent directories of this directory will be implicitly
# created as needed (i.e., if they do *NOT* currently exist).

# ....................{ BASH                               }....................
# Enable strict mode, terminating the script with non-zero exit status on the
# first command or pipeline failing with non-zero exit status.
set -o errexit

# ....................{ MESSAGES                           }....................
# info(info_message: str) -> None
#
# Print the passed informational message to standard output.
info() {
    echo "${BASH_SOURCE[1]}:" "${@}"
    exit 1
}


# die(error_message: str) -> None
#
# Print the passed error message to standard error and terminate the current
# shell script with the standard failure exit status.
die() {
    echo "${BASH_SOURCE[1]}:" "${@}" >&2
    exit 1
}


# Print a quasi-informative preamble.
info 'Welcome to the BETSEE installer for Ubuntu Linux (>= 16.04).'

# ....................{ CHECKS                             }....................
# is_os_ubuntu_linux() -> int
#
# Success only if the current platform is Ubuntu Linux.
is_os_linux_ubuntu() {
    python - << '__HEREDOC'
    import platform, sys

    # If the Linux-specific platform.linux_distribution() function is available
    # *AND* the first item of the 3-tuple "(distname, version, id)" returned by
    # this function is "Ubuntu", the current platform is Ubuntu Linux. In this
    # case, the active Python process is terminated with the success exit code.
    # Since the platform.system() function returns the low-level kernel name
    # "Linux", this function is *NOT* called here.
    if (hasattr(platform, 'linux_distribution') and
        platform.linux_distribution()[0] == 'Ubuntu'):
        sys.exit(0)
    # Else, the current platform is *NOT* Ubuntu Linux. In this case, the active
    # Python process is terminated with a failure exit code.
    else:
        sys.exit(1)
__HEREDOC
}

# If the current platform is *NOT* Ubuntu Linux, fail.
info 'Detecting current platform...'
is_os_ubuntu_linux || die 'Current platform not Ubuntu Linux.'

# If the current login shell is *NOT* Bash, fail. The subsequent installation of
# Qt 5.6.2 assumes the shell to be Bash, sadly.
info 'Detecting login shell...'
[[ "${SHELL}" == bash ]] || die "Login shell \"${SHELL}\" not \"bash\"."

# ....................{ ARGS                               }....................
info 'Parsing script arguments...'

# Absolute or relative path of the directory to which BETSEE and BETSE will be
# installed to, defaulting to a general-purpose directory if unpassed.
local install_dirname="${1-${HOME}/Applications}"

# Create this directory and all parent directories of this directory as needed.
mkdir --parents "${install_dirname}"

# ....................{ DEPENDENCIES                       }....................
# Install the subsequently required "pip3" command.
info 'Installing Python 3 package manager...'
sudo apt-get install python3-pip

# ....................{ DEPENDENCIES ~ betsee              }....................
# Since PySide2 is the most fragile and hence failure-prone dependency to be
# installed, do so first -- ensuring that no subsequent dependencies are
# installed in the (all too likely) event that installing this dependency fails.

# Add an unofficial Qt 5.6.2 PPA. The subsequently installed PySide2 wheels
# currently require Qt 5.6.2.
info 'Installing Qt 5.6.2 PPA (Personal Package Archive)...'
sudo apt-get update
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:beineri/opt-qt562-xenial

# Install Qt 5.6.2.
info 'Installing Qt 5.6.2...'
sudo apt-get update
sudo apt-get install qt56-meta-full

# Enable Qt 5.6.2 in the local Bash shell environment.
info 'Enabling Qt 5.6.2...'
echo . /opt/qt56/bin/qt56-env.sh >> ~/.bashrc
. ~/.bashrc

# Install PySide2.
info 'Installing PySide2...'
pip3 install https://dl.bintray.com/fredrikaverpil/pyside2-wheels/ubuntu16.04/PySide2-5.6-cp35-cp35m-linux_x86_64.whl

# ....................{ DEPENDENCIES ~ betse               }....................
#FIXME: Implement us up.
# Install all mandatory BETSE-specific dependencies.
info 'Installing mandatory BETSE dependencies...'

# Install all optional BETSE-specific dependencies.
info 'Installing optional BETSE dependencies...'

# ....................{ BETSE[E]                           }....................
#FIXME: Implement us up via a "git clone" approach.
# Install BETSE *BEFORE* BETSEE, as the latter requires the former.
info 'Installing BETSE...'

#FIXME: Implement us up via a "git clone" approach.
# Install BETSEE.
info 'Installing BETSEE...'
