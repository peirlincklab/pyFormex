# User Functions

# Make directory and change into it
mcd() {
    [ -n "$1" ] && mkdir -p "$1" && cd "$1"
}

# Remove cruft
clean () {
    rm -f $1 .*~ *~ *% *.bak *.BAK \#* core DEADJOE dead.letter "@*"
}

# Remove empty files in the current directory
rm_empty () {
    find $1 -size 0 -exec rm {} \;
}

# Get the file extension of a filename
file_ext () {
    expr "$1" : ".*\.\(.*\)"
}

# Execute a command $@ inside directory $1
indir () {
    [ -d "$1" ] && ( pushd $1; $2; popd; )
}

#Remove component $1 from path $2
removepath () {
  echo :$2: | sed "s|:$1:|:|g;s|^:||;s|:\$||"
}

# Execute a function for all key/val tuples in the boot command line
all_cmdline_pars() {
    [ -n "$(type -t $1)" ] && for f in $(cat /proc/cmdline); do
	key=$(expr "$f" : "\([^=]*\).*")
        val=${f#${key}=}
       	$1 $key $val
    done
}

# Execute a function $2 for all words in $1
#
all_words() {
    [ -r "$1" ] && for f in $(cat $1); do
        $2 $f
    done
}

# Maximum of a sequence of integer numbers
#
max() {
    if [ -z "$2" ]; then
	echo "$1"
    else
	if [ "$1" -lt "$2" ]; then
	    m="$2"
	else
	    m="$1"
	fi
	shift 2
	if [ -z "$1" ]; then
	    echo "$m"
	else
	    echo "$(max $m $@)"
	fi
    fi
}
#
# Bump the trailing numerical part of a string to the next version
# Make sure that the string ends with a digit!
#
bump_version() {
  val=$(expr "$1" : '.*[^0-9]\+\([0-9]\+\)')
  echo "${1%$val}$(expr $val + 1)"
}

# Check that $1 is in list $2...
# Returns zero if $1 is in $2..., else nonzero
inside_list() {
    word=$1
    shift
    for i in $*; do
	[ "$word" = "$i" ] && return 0
    done
    return 1
}

# Check that character $1 is in string $2
char_in_string() {
    char="$1"
    foo="$2"
    for (( i=0; i<${#foo}; i++ )); do
	[ "${foo:$i:1}" = "$char" ] && return 0
    done
    return 1
}

# Convert date string to unix date (seconds since epoch)
# All parameters are considered to be the date string!
unixdate() {
    date -d "$*" +'%s'
}

# Get the last modification time of a file (seconds since epoch)
filedate() {
    stat --printf="%Y" "$1"
}

# Convert unix time to string
strdate() {
    date -d "@$1"
}

#
# Display the creation date of a file (works for ext4, not for all file systems)
#
# $@ = filename(s)
#
xstat() {
   for target in "${@}"; do
     inode=$(ls -di "${target}" | cut -d ' ' -f 1)
     fs=$(df "${target}"  | tail -1 | awk '{print $1}')
     crtime=$(sudo debugfs -R 'stat <'"${inode}"'>' "${fs}" 2>/dev/null |
     grep -oP 'crtime.*--\s*\K.*')
     printf "%s\t%s\n" "${crtime}" "${target}"
   done
}

# Ask for user acknowledgments
# The user can enter a single character, in either upper or lower
# case, and the result will always be translated to lower case.
#
#   $1 = prompt
#   $2 = choices: set of characters that can be entered. If the
#        first one is an upper case, it
#   $3 = name of variable to return the user answer, which is
#        a single character from choices
ask() {
    local __ans=
    local __ok=${2,,}
    local __default=${2::1}
    # No default if not upper case
    [ "${__default^^}" = "$__default" ] || __default=
    __default=${__default,,}
    while true; do
	read -p "$1 ($2) " __ans
	[ -n "$__ans" ] || {
	    __ans=$__default
	}
	__ans=${__ans,,}  # convert to lower case
	char_in_string "$__ans" "$__ok" && break
	echo
	echo "Invalid response! enter ONE of the proposed characters!"
    done
    eval $3="'$__ans'"
}

# End
