#!/usr/bin/env bash
# ====================[ betsee_ubuntu_16_04.bash           ]====================
#
# --------------------( SYNOPSIS                           )--------------------
# Bash shell script automating the updating of BETSEE and BETSE installations
# previously installed by an installation script bundled with BETSEE (e.g.,
# "bin/install/betsee_ubuntu_16_04.bash") to the most recent remote Git commits
# to both repositories.
#
# --------------------( USAGE                              )--------------------
# This script is safely run from anywhere in the filesystem. For example,
# assuming BETSEE and BETSE were installed to their default locations on Linux:
#
#     bash ~/Applications/betsee/bin/update

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
note 'Welcome to the BETSE[E] updater.'

# ....................{ DIRS                               }....................
# Absolute or relative path of the directory containing the current script.
script_dirname="$(dirname "${BASH_SOURCE[0]}")"

# Absolute or relative path of the directory to which BETSEE was installed.
betsee_dirname="${script_dirname}/.."

# Absolute or relative path of the directory to which BETSE was installed.
betse_dirname="${betsee_dirname}/../betse"

# ....................{ UPDATE                             }....................
# update_py_git_repo(repo_dirname: str) -> None
#
# Update the Git repository at the local directory with the passed absolute or
# relative path against remote changes.
update_git_repo() {
    (( ${#} == 1 )) || die 'One arguments expected.'

    local repo_dirname="${1}"

    # If this directory does *NOT* exists, fail
    [[ -d "${repo_dirname}" ]] ||
        die "Directory \"${repo_dirname}\" not found."

    # If this directory is *NOT* a Git repository, fail.
    [[ -d "${repo_dirname}/.git" ]] ||
        die "Directory \"${repo_dirname}\" not a Git repository."

    # Synchronize this local repository against remote changes.
    note 'Updating Git repository...'
    pushd "${repo_dirname}"
    git pull
    popd
}


# Update BETSE *BEFORE* BETSEE, as the latter requires the former.
info 'Updating BETSE...'
update_git_repo "${betse_dirname}"

# Update BETSEE.
info 'Updating BETSEE...'
update_git_repo "${betsee_dirname}"
