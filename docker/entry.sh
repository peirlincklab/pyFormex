#/bin/bash

# GPL v3 or higher
# (c) Benedict Verhegghe
# Based on a script from OpenFOAM Copyright (C) 2017-2020 OpenFOAM Foundation

cat << __EOF__
Welcome to the pyFormex Docker Image

Provides bash terminal with pyFormex

Parameters: $@

__EOF__

USER_ID=$(id -u)
GROUP_ID=$(id -g)
USER=demo
PATH=/home/$USER/.local/bin:/home/$USER/bin:/usr/local/bin:/usr/bin:/bin

# if [ "$USER_ID" != "0" ]; then
#     NSS_WRAPPER_PASSWD=/tmp/passwd.nss_wrapper
#     NSS_WRAPPER_GROUP=/tmp/group.nss_wrapper

#     cat /etc/passwd | sed -e "s/^${USER}:/ignore:/" > $NSS_WRAPPER_PASSWD
#     echo "${USER}:x:$USER_ID:$GROUP_ID:${USER},,,:/home/${USER}:/bin/bash" >> $NSS_WRAPPER_PASSWD

#     if [ "$GROUP_ID" != "0" ]; then
#         cat /etc/group | sed -e "s/^${USER}:/ignore:/" > $NSS_WRAPPER_GROUP
#         echo "${USER}:x:$GROUP_ID:" >> $NSS_WRAPPER_GROUP
#     fi

#     export NSS_WRAPPER_PASSWD
#     export NSS_WRAPPER_GROUP

#     LD_PRELOAD=/usr/lib/libnss_wrapper.so
#     export LD_PRELOAD
# fi

exec /usr/bin/env "$@"
