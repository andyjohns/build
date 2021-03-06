# Docker container for SuSE 12.0 SP2

# See https://github.com/ceejatec/naked-docker/ for details about the
# construction of the base image.

FROM suse/sles12sp2:latest
MAINTAINER kenneth.lareau@couchbase.com

USER root
ARG REGCODE
RUN zypper ref -s
RUN zypper install -y SUSEConnect
RUN SUSEConnect -r ${REGCODE} -e kenneth.lareau@couchbase.com
RUN SUSEConnect -p sle-sdk/12.2/x86_64
RUN zypper ref -s
RUN zypper -n in vim
RUN zypper -n install openssh sudo && zypper clean

# Set up for SSH daemon
RUN sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config && \
    sed -ri 's/#UsePAM no/UsePAM no/g' /etc/ssh/sshd_config && \
    sed -ri 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config && \
    sed -ri 's/#PermitUserEnvironment no/PermitUserEnvironment yes/g' /etc/ssh/sshd_config && \
    ssh-keygen -f /etc/ssh/ssh_host_rsa_key -N '' -t rsa && \
    ssh-keygen -f /etc/ssh/ssh_host_dsa_key -N '' -t dsa

# Create couchbase user with password-less sudo privs, and give
# ownership of /opt/couchbase
RUN groupadd -g1000 couchbase && \
    useradd couchbase -g couchbase -u1000 -G wheel -m -s /bin/bash && \
    mkdir /opt/couchbase && chown -R couchbase:couchbase /opt/couchbase && \
    echo 'couchbase:couchbase' | chpasswd && \
    sed -ri 's/ALL\) ALL/ALL) NOPASSWD:ALL/' /etc/sudoers

### Install Couchbase build dependencies ######################################
# * Packages from the base CentOS repository
RUN zypper -n install \
                binutils \
                curl \
                ed \
                gcc gcc-c++ \
                make \
                cmake \
                ccache \
                git \
                man \
                ncurses-devel \
                libffi48-devel \
                libnuma-devel \
                libopenssl-devel \
                lsb-release \
                python-devel \
                rpm-build \
                ruby rubygems rubygem-rake \
                tar \
                unzip && \
                zypper clean

#paramiko for testrunner
#RUN zypper install -y python-paramiko && zypper clean
RUN zypper addrepo -f obs://Cloud:OpenStack:Liberty/SLE_12 Liberty
RUN zypper -n --gpg-auto-import-keys install python-pip
RUN pip install paramiko

# Install autoconf and friends - necessary for building some third-party deps
# from source, not for Couchbase. (The "full" version of perl is also required
# for some third-party builds, so don't remove that after building libtool.)
RUN zypper -n install perl && \
    mkdir /tmp/deploy && \
    curl -L http://ftp.gnu.org/gnu/m4/m4-1.4.17.tar.bz2 -o /tmp/deploy/m4-1.4.17.tar.bz2 && \
    cd /tmp/deploy && tar -xjf m4-1.4.17.tar.bz2 && \
    cd m4-1.4.17 && ./configure --prefix=/usr/local && make -j8 && make install && \
    curl -L http://ftpmirror.gnu.org/autoconf/autoconf-2.69.tar.gz -o /tmp/deploy/autoconf-2.69.tar.gz && \
    cd /tmp/deploy && tar -xzf autoconf-2.69.tar.gz && \
    cd autoconf-2.69 && ./configure --prefix=/usr/local && make -j8 && make install && \
    curl -L http://ftpmirror.gnu.org/automake/automake-1.14.tar.gz -o /tmp/deploy/automake-1.14.tar.gz && \
    cd /tmp/deploy && tar -xzf automake-1.14.tar.gz && \
    cd automake-1.14 && ./configure --prefix=/usr/local && make && make install && \
    curl -L http://ftpmirror.gnu.org/libtool/libtool-2.4.2.tar.gz -o /tmp/deploy/libtool-2.4.2.tar.gz && \
    cd /tmp/deploy && tar -xzf libtool-2.4.2.tar.gz && \
    cd libtool-2.4.2 && ./configure --prefix=/usr/local && make -j8 && make install && \
    cd /tmp && rm -rf /tmp/deploy && zypper clean

# * ccache symlinks
RUN ln -s /usr/bin/ccache /home/couchbase/bin/gcc && \
    ln -s /usr/bin/ccache /home/couchbase/bin/g++ && \
    ln -s /usr/bin/ccache /home/couchbase/bin/cc && \
    ln -s /usr/bin/ccache /home/couchbase/bin/c++

# * repo
RUN curl https://storage.googleapis.com/git-repo-downloads/repo -o /usr/local/bin/repo && \
    chmod a+x /usr/local/bin/repo

# Oracle JDK (for Jenkins and Analytics).
RUN mkdir /tmp/deploy && \
    cd /tmp/deploy && \
    curl -L --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" \
    http://download.oracle.com/otn-pub/java/jdk/8u121-b13/e9e7ea248e2c4826b92b3f075a80e441/jdk-8u121-linux-x64.rpm -o jdk.rpm && \
    rpm -Uvh jdk.rpm && \
    cd /tmp && rm -rf deploy
ENV JAVA_HOME=/usr/java/latest

# Maven (for Analytics).
RUN mkdir /tmp/deploy && \
    cd /tmp/deploy && \
    curl -L http://mirror.cogentco.com/pub/apache/maven/maven-3/3.3.9/binaries/apache-maven-3.3.9-bin.tar.gz \
       -o maven.tar.gz && \
    cd /usr/local && \
    tar xzf /tmp/deploy/maven.tar.gz && \
    ln -s /usr/local/apache-maven-3.3.9/bin/mvn /usr/local/bin/mvn && \
    rm -rf /tmp/deploy

# Expose SSH daemon and run our builder startup script
EXPOSE 22
ADD .ssh /home/couchbase/.ssh
COPY build/couchbuilder_start.sh /usr/sbin/
ENTRYPOINT [ "/usr/sbin/couchbuilder_start.sh" ]
CMD [ "default" ]
