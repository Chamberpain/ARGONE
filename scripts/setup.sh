#!/bin/bash -ex

cd $(dirname "${BASH_SOURCE[0]}")
if ! [ -e env ]
then
    if [ -z "$(which python2.7)" ]
    then
        python=python
    else
        python=python2.7
    fi
    virtualenv -p $python env ||
        virtualenv2 -p $python env ||
        virtualenv-2.7 -p $python env # OS X macports
fi
. env/bin/activate
pip2 install numpy
if pip2 install -r ../requirements.txt
then
    echo -e "The environment has been created and is up to date."
    echo -e "Use it by sourcing env/bin/activate (type \033[34;1msource $(pwd)/env/bin/activate\033[0m)"
else
    echo -e "There were errors, please ensure libatlas or blas + lapack are installed."
    echo -e "On arch linux, this is \033[34;1msudo pacman -S blas lapack\033[0m"
    echo -e "On ubuntu, this is \033[34;1msudo apt-get install libatlas-dev liblapack-dev gfortran\033[0m"
    echo -e "On fedora, this is \033[34;1msudo yum install atlas-devel gcc-fortran lapack-devel gcc-c++\033[0m"
fi
