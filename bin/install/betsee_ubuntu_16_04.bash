#!/usr/bin/env bash
# ====================[ betsee_ubuntu_16_04.bash           ]====================
#
# --------------------( SYNOPSIS                           )--------------------
# Bash shell script automating the installation of BETSEE and all mandatory and
# optional dependencies thereof (e.g., PySide2 and BETSE) for all Ubuntu Linux
# releases newer than or equal to Ubuntu 16.04 (Xenial Xerus).
#
# --------------------( USAGE                              )--------------------
# ./betsee_ubuntu_16_04.bash [INSTALL_DIR]
#
# Installs both BETSEE and BETSE to the passed installation directory,
# defaulting to the common "${HOME}/Applications" directory if unpassed. This
# directory and all parent directories of this directory will be implicitly
# created as needed (i.e., if they do *NOT* currently exist).
#
# --------------------( DOWNLOAD                           )--------------------
# While this script may be run directly from a cloned Git repository, doing so
# would defeat the utility of this script -- which automates the cloning of this
# repository in a predictably structured manner, among other useful installation
# tasks. Instead, users are recommended to directly download this script from
# BETSEE's GitLab-hosted project to the local filesystem and run that.
#
# Since all Ubuntu releases come preinstalled with the "wget" command, the
# following "one-liner" suffices to install BETSEE from any open terminal:
#
#     wget https://gitlab.com/betse/betsee/raw/master/bin/install/betsee_ubuntu_16_04.bash && bash betsee_ubuntu_16_04.bash

# ....................{ BASH                               }....................
# Enable strict mode, terminating the script with non-zero exit status on the
# first command or pipeline failing with non-zero exit status.
set -o errexit

# ....................{ MESSAGES                           }....................
# note(info_message: str) -> None
#
# Print the passed informational message to standard output.
note() {
    echo "${BASH_SOURCE[1]}:" "${@}"
}


# info(info_message: str) -> None
#
# Print the passed informational message to standard output prefixed by a
# newline.
info() {
    echo
    note "${@}"
}


# die(error_message: str) -> None
#
# Print the passed error message to standard error prefixed by a newline and
# terminate the current shell script with the usual failure exit status.
die() {
    echo "${BASH_SOURCE[1]}:" "${@}" >&2
    exit 1
}


# Print a quasi-informative preamble.
note 'Welcome to the BETSE[E] installer for Ubuntu Linux 16.04 and newer!'
note 'Note that this installation typically requires 2GB of free disk space.'
echo

# ....................{ SUDO                               }....................
# If sudo privelages have already expired for the current user, (re)cache these
# privelages in a human-readable manner. The default prompt printed by the
# "sudo" command (e.g., "[sudo] password for ${USERNAME}:") is arguably
# non-human-readable for those unfamiliar with POSIX shell environments.
if ! sudo -S true </dev/null 2> /dev/null; then
    note 'Please enter your user password:'
    sudo true
fi

# ....................{ CHECKS                             }....................
# is_os_linux_ubuntu() -> int
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
note 'Detecting current platform...'
is_os_linux_ubuntu || die 'Current platform not Ubuntu Linux.'

# If the current login shell is *NOT* Bash, fail. The subsequent installation of
# Qt 5.6.2 assumes the shell to be Bash, sadly.
note 'Detecting login shell...'
[[ "${SHELL}" == */bash ]] || die "Login shell \"${SHELL}\" not \"bash\"."

# ....................{ ARGS                               }....................
note 'Parsing script arguments...'

# Absolute or relative path of the parent directory containing the directories
# to which BETSEE and BETSE will be installed, defaulting to a general-purpose
# directory if unpassed.
install_dirname="${1-${HOME}/Applications}"

# Absolute or relative path of the directory to which BETSEE will be installed.
betsee_dirname="${install_dirname}/betsee"

# Absolute or relative path of the directory to which BETSE will be installed.
betse_dirname="${install_dirname}/betse"

# Create this directory and all parent directories of this directory as needed.
note "Installing BETSE[E] to: ${install_dirname}"
mkdir --parents "${install_dirname}"

# ....................{ DEPENDENCIES                       }....................
# Install subsequently required core commands (e.g., "git", "pip3").
note 'Installing project and package managers...'
sudo apt-get install --yes git python3-pip

# ....................{ DEPENDENCIES ~ betsee              }....................
# Since PySide2 is the most fragile and hence failure-prone dependency to be
# installed, do so first -- ensuring that no subsequent dependencies are
# installed in the (all too likely) event that installing this dependency fails.
#
# Note that the entirety of this section is derived from the Ubuntu 16.04
# installation instructions for Fredrick Averpil's unofficial PySide2 wheels at:
#     https://github.com/fredrikaverpil/pyside2-wheels#ubuntu-1604-xenial

# Add an unofficial Qt 5.6.2 PPA. The subsequently installed PySide2 wheels
# currently require Qt 5.6.2.
info 'Installing Qt 5.6.2 PPA (Personal Package Archive)...'
sudo apt-get update --yes
sudo apt-get install --yes software-properties-common
sudo add-apt-repository --yes ppa:beineri/opt-qt562-xenial

# Install Qt 5.6.2.
info 'Installing Qt 5.6.2...'
sudo apt-get update --yes
sudo apt-get install --yes qt56-meta-full

# Enable Qt 5.6.2 in the local Bash shell environment.
info 'Enabling Qt 5.6.2...'
echo ". /opt/qt56/bin/qt56-env.sh" >> ~/.bashrc
. ~/.bashrc

# Install the Ubuntu 16.04- and Python 3-specific PySide2 wheel.
info 'Installing PySide2...'
sudo pip3 install \
    https://dl.bintray.com/fredrikaverpil/pyside2-wheels/ubuntu16.04/PySide2-5.6-cp35-cp35m-linux_x86_64.whl

# ....................{ DEPENDENCIES ~ betse               }....................
# Note that the entirety of this section is derived from the Debian-specific
# installation instructions for BETSE at:
#     https://gitlab.com/betse/betse/blob/master/doc/md/INSTALL.md#debian

# Install all mandatory BETSE-specific dependencies.
info 'Installing mandatory BETSE dependencies...'
sudo apt-get install --yes \
    python3-dev python3-dill python3-matplotlib \
    python3-numpy python3-pil python3-pip python3-scipy python3-setuptools \
    python3-six python3-yaml tcl tk

# Install an OpenBLAS-optimized scientific stack. While the SourceForge-hosted
# ATLAS project would also apply, the GitHub-hosted OpenBLAS project is
# (unsurprisingly) significantly better maintained.
info 'Installing OpenBLAS-optimized scientific stack...'
sudo apt-get install --yes build-essential libopenblas-dev
sudo update-alternatives --set libblas.so.3 /usr/lib/openblas-base/libblas.so.3
sudo update-alternatives --set liblapack.so.3 /usr/lib/lapack/liblapack.so.3

#FIXME: Add installation instructions to "INSTALL.md" documenting installation
#of FFMpeg and LibAV on all supported platforms.
#FIXME: "INSTALL.md" incorrectly lists BETSE as optionally requiring
#"PyDot >= 1.0.29" when in fact BETSE only optionally requires
#"PyDot >= 1.0.28". Amend this, please.

# Install all optional BETSE-specific dependencies.
#
# Note that:
#
# * The "libav-tools" package provides the "avconv" command required for
#   exporting compressed videos of simulation phase runs.
# * The "python3-networkx" package provides NetworkX 1.11, which breaks
#   backward compatibility with respect to PyDot support required by BETSE.
#   Hence, the next-most-recent NetworkX release is installed manually.
info 'Installing optional BETSE dependencies...'
sudo apt-get install --yes graphviz libav-tools python3-pydot
sudo pip3 install 'networkx==1.10'

# ....................{ BETSE[E]                           }....................
# install_py_git_repo(repo_url: str, repo_dirname: str) -> None
#
# Install the Python project hosted at the remote Git repository with the passed
# URL to the local directory with the passed absolute or relative path in an
# editable manner, preventing repository synchronization issues.
install_git_repo() {
    (( ${#} == 2 )) || die 'Two arguments expected.'

    local repo_url="${1}"
    local repo_dirname="${2}"

    # If this directory already exists...
    if [[ -d "${repo_dirname}" ]]; then
        # If this directory is *NOT* a Git repository, fail.
        [[ -d "${repo_dirname}/.git" ]] ||
            die "\"${repo_dirname}\" not a Git repository."

        # Synchronize this local repository against remote changes.
        note 'Updating Git repository...'
        GIT_WORK_TREE="${repo_dirname}" git pull
    # Else, clone this remote repository to this local directory.
    else
        note 'Cloning Git repository...'
        git clone "${repo_url}" "${repo_dirname}"
    fi

    # If this directory contains no "setup.py" script, fail.
    [[ -f "${repo_dirname}/setup.py" ]] ||
        die "\"${repo_dirname}\" not a Python project."

    # Install this Python project editably.
    note 'Installing Python project...'
    pushd "${repo_dirname}"
    sudo python3 setup.py develop
    popd "${repo_dirname}"
}


# Install BETSE *BEFORE* BETSEE, as the latter requires the former.
info 'Installing BETSE...'
install_git_repo 'https://gitlab.com/betse/betse.git' "${betse_dirname}"

# Install BETSEE.
info 'Installing BETSEE...'
install_git_repo 'https://gitlab.com/betse/betsee.git' "${betsee_dirname}"

# ....................{ INSTRUCTIONS                       }....................
# For usability, provide rudimentary usage instructions.
info 'To run BETSEE, enter the following command in any open terminal:
    betsee &!
'
