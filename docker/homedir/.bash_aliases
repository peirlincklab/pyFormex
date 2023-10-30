# System-wide .bashrc file for interactive bash(1) shells.

# To enable the settings / commands in this file for login shells as well,
# this file has to be sourced in /etc/profile.

# functions for use in all shells, both interactive and not

# aliases
alias ls='ls --color=auto --group-directories-first'
alias ll='ls -l'
alias la='ls -A'
alias l.='ls -d .[a-zA-Z]*'
alias lsd='ls -d */'
alias more='less'
alias md='mkdir'
alias rd='rmdir'
alias pd='pushd'
alias rod='pushd +1'
alias m='more'
alias h='history'
alias dux='du -x --max-depth=1'
alias pysea='pyformex --search --'
