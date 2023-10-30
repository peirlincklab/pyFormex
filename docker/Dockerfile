# This is a Dockerfile for building a image containing pyFormex

# By default based on latest Debian
ARG FROM=debian:latest
FROM ${FROM}
MAINTAINER bverheg@gmail.com

# Argument defaults
ARG PYFVER=2.0

ARG USER=demo

ENV HOME=/home/$USER

COPY apt_install_deps entry.sh /
RUN /apt_install_deps "" sudo joe libnss-wrapper emacs-gtk python3-vtk7; \
    apt-get clean

# Create the user and give full sudo rights
RUN useradd --create-home --home-dir /home/$USER --shell /bin/bash \
  --user-group --groups sudo $USER;\
  echo "$USER ALL = NOPASSWD: ALL" > /etc/sudoers.d/$USER;\
  chmod 440 /etc/sudoers.d/$USER

# Install pyFormex as user
WORKDIR /home/$USER
USER $USER
COPY --chown=demo:demo homedir/ /home/$USER/
RUN \
  tar xzf pyformex-$PYFVER.tar.gz; \
  rm pyformex-$PYFVER.tar.gz; \
  cd pyformex-$PYFVER; \
  ./install.sh -d all

# Switch to '$USER'
USER $USER
WORKDIR /home/$USER

ENTRYPOINT [ "/bin/bash", "/entry.sh" ]

# End
