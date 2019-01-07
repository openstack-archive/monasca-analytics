#
# Copyright 2016 FUJITSU LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Monasca-analytics DevStack plugin
#
# Install and start Monasca-analytics service in devstack
#
# To enable Monasca-analytics in devstack add an entry to local.conf that
# looks like
#
# [[local|localrc]]
# enable_plugin monasca-analytics https://git.openstack.org/openstack/monasca-analytics
#
# By default all Monasca services are started (see
# devstack/settings). To disable a specific service use the
# disable_service function. For example to turn off notification:
#
# disable_service monasca-notification
#
# Several variables set in the localrc section adjust common behaviors
# of Monasca (see within for additional settings):
#
# EXAMPLE VARS HERE

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

ERREXIT=$(set +o | grep errexit)
set -o errexit

# Determine if we are running in devstack-gate or devstack.
if [[ $DEST ]]; then
    # We are running in devstack-gate.
    export MONASCA_BASE=${MONASCA_BASE:-"${DEST}"}

else
    # We are running in devstack.
    export MONASCA_BASE=${MONASCA_BASE:-"/opt/stack"}

fi
export MONASCA_ANALYTICS_BASE=${MONASCA_ANALYTICS_BASE:-"${MONASCA_BASE}/monasca-analytics"}

###
function pre_install_spark {
:
}

###
function pre_install_monasca_analytics {
:
}

###
function unstack_monasca_analytics {
    echo_summary "Unstack Monasca-analytics"

    delete_monasca_analytics_files

    sudo userdel monasca-analytics || true
    sudo groupdel monasca-analytics || true

    unstack_spark
}

###
function delete_monasca_analytics_files {
    sudo rm -rf /opt/monasca/analytics || true
    sudo rm -rf /etc/monasca/analytics || true
    sudo rm /etc/init/monasca-analytics.conf || true

    MONASCA_ANALYTICS_DIRECTORIES=("/var/log/monasca/analytics" "/var/run/monasca/analytics" "/etc/monasca/analytics/init")

    for MONASCA_ANALYTICS_DIRECTORY in "${MONASCA_ANALYTICS_DIRECTORIES[@]}"
    do
       sudo rm -rf ${MONASCA_ANALYTICS_DIRECTORY} || true
    done
}

###
function unstack_spark {
    echo_summary "Unstack Spark"

    delete_spark_directories
    sudo rm -rf /opt/spark/download || true
}

###
function clean_monasca_analytics {
    set +o errexit
    unstack_monasca_analytics
    unistall_pkgs
    set -o errexit
}

###
function delete_spark_directories {
    for SPARK_DIRECTORY in "${SPARK_DIRECTORIES[@]}"
        do
           sudo rm -rf ${SPARK_DIRECTORY} || true
        done

    sudo rm -rf /var/log/spark-events || true
}

###
function unistall_pkgs {
    sudo apt-get -y purge ipython python-scipy python-numpy
    sudo apt-get -y purge python-setuptools

    sudo apt-get -y purge sbt
    sudo apt-key del $KEYID
    sudo sed -i -e '/deb https\:\/\/dl.bintray.com\/sbt\/debian \//d' /etc/apt/sources.list.d/sbt.list
    sudo dpkg -r scala

    sudo apt-get -y purge $JDK_PKG

    sudo rm -rf ~/.m2

    sudo rm -rf $SPARK_DIR
}

###
function install_pkg {
    ## JDK
    sudo -E apt-get -y install $JDK_PKG

    ## SCALA
    sudo -E curl $SCALA_URL -o $SPARK_DOWNLOAD/$SCALA
    sudo -E dpkg -i $SPARK_DOWNLOAD/$SCALA
    echo "deb https://dl.bintray.com/sbt/debian /" | sudo -E tee -a /etc/apt/sources.list.d/sbt.list
    sudo -E apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv $KEYID
    sudo -E apt-get update
    sudo -E apt-get -y install sbt

    ## other pkg
    sudo -E apt-get -y install python-setuptools
    sudo -E apt-get -y install python-numpy python-scipy ipython
}

###
function build_spark {
    ## install maven
    sudo -E curl $MAVEN_URL -o $SPARK_DOWNLOAD/$MAVEN_TARBAL
    sudo chown stack:stack $SPARK_DOWNLOAD/$MAVEN_TARBAL
    sudo -u stack tar -xzf $SPARK_DOWNLOAD/$MAVEN_TARBAL -C $SPARK_DIR

    if [ ${http_proxy} ];then
        read HTTP_PROXY_USER_NAME HTTP_PROXY_PASSWORD HTTP_PROXY_HOST<< END
`echo ${http_proxy:7} | awk -F: '{sub("@", ":");print $1, $2, $3}'`
END
        if [ -z $HTTP_PROXY_HOST ];then
            LENGTH_FOR_HOST=`expr match "$http_proxy" 'http://[\.A-Za-z\-]*'`-7
            sed -e '7,8d' \
                -e "s/<host><\/host>/<host>${http_proxy:7:$LENGTH_FOR_HOST}<\/host>/g" \
                ${MONASCA_ANALYTICS_BASE}/devstack/files/maven/settings.xml > ~/.m2/settings.xml
        else
            sed -e "s/<username><\/username>/<username>${HTTP_PROXY_USER_NAME}<\/username>/g" \
                -e "s/<password><\/password>/<password>${HTTP_PROXY_PASSWORD}<\/password>/g" \
                -e "s/<host><\/host>/<host>${HTTP_PROXY_HOST}<\/host>/g" \
                ${MONASCA_ANALYTICS_BASE}/devstack/files/maven/settings.xml > ~/.m2/settings.xml
        fi
    fi

    ## Build Spark
    sudo -E curl $SPARK_URL -o $SPARK_DOWNLOAD/${SPARK_TARBALL_NAME}
    sudo chown stack:stack $SPARK_DOWNLOAD/${SPARK_TARBALL_NAME}
    sudo -u stack tar -xzf $SPARK_DOWNLOAD/${SPARK_TARBALL_NAME} -C $SPARK_DIR

    DEVSTACK_DIR=`pwd`
    cd $SPARK_DIR/spark-${SPARK_VERSION}
    $SPARK_DIR/$MAVEN/bin/mvn -DskipTests clean package
    sudo cp -pf ./conf/log4j.properties.template ./conf/log4j.properties
    sudo sed -i 's/log4j.rootCategory=INFO/log4j.rootCategory=ERROR/g' ./conf/log4j.properties
    cd $DEVSTACK_DIR
}

###
function install_zookeeper {
    if [ ! -e /etc/init.d/zookeeper ]; then
        echo_summary "Install Monasca Zookeeper"

        sudo apt-get -y install zookeeperd

        sudo cp "${MONASCA_ANALYTICS_BASE}"/devstack/files/zookeeper/myid /etc/zookeeper/conf/myid
        sudo cp "${MONASCA_ANALYTICS_BASE}"/devstack/files/zookeeper/environment /etc/zookeeper/conf/environment
        sudo cp "${MONASCA_ANALYTICS_BASE}"/devstack/files/zookeeper/log4j.properties /etc/zookeeper/conf/log4j.properties
        sudo cp "${MONASCA_ANALYTICS_BASE}"/devstack/files/zookeeper/zoo.cfg /etc/zookeeper/conf/zoo.cfg
        if [[ ${SERVICE_HOST} ]]; then
            sudo sed -i "s/server\.0=127\.0\.0\.1/server.0=${SERVICE_HOST}/g" /etc/zookeeper/conf/zoo.cfg
        fi

        sudo mkdir -p /var/log/zookeeper || true
        sudo chmod 755 /var/log/zookeeper

        sudo systemctl start zookeeper || sudo systemctl restart zookeeper
    else
        echo_summary "SKIP:Install Monasca Zookeeper"
    fi
}

###
function install_kafka {
    if [ ! -e /etc/init/kafka.conf ];then
        echo_summary "Install Monasca Kafka"

        sudo groupadd --system kafka || true
        sudo useradd --system -g kafka kafka || true

        sudo -E curl $KAFKA_URL -o $SPARK_DOWNLOAD/$KAFKA_TARBALL
        sudo tar -xzf $SPARK_DOWNLOAD/$KAFKA_TARBALL -C /opt
        sudo ln -sf /opt/kafka_${KAFKA_VERSION} /opt/kafka

        sudo cp -f "${MONASCA_ANALYTICS_BASE}"/devstack/files/kafka/kafka-server-start.sh /opt/kafka_${KAFKA_VERSION}/bin/kafka-server-start.sh
        sudo cp -f "${MONASCA_ANALYTICS_BASE}"/devstack/files/kafka/kafka.conf /etc/init/kafka.conf

        sudo chown root:root /etc/init/kafka.conf
        sudo chmod 644 /etc/init/kafka.conf

        sudo mkdir -p /var/kafka || true
        sudo chown kafka:kafka /var/kafka
        sudo chmod 755 /var/kafka
        sudo rm -rf /var/kafka/lost+found

        sudo mkdir -p /var/log/kafka || true
        sudo chown kafka:kafka /var/log/kafka
        sudo chmod 755 /var/log/kafka

        sudo ln -sf /opt/kafka/config /etc/kafka
        sudo cp -f "${MONASCA_ANALYTICS_BASE}"/devstack/files/kafka/log4j.properties /etc/kafka/log4j.properties
        sudo chown kafka:kafka /etc/kafka/log4j.properties

        sudo chmod 644 /etc/kafka/log4j.properties
        sudo cp -f "${MONASCA_ANALYTICS_BASE}"/devstack/files/kafka/server.properties /etc/kafka/server.properties
        sudo chown kafka:kafka /etc/kafka/server.properties
        sudo chmod 644 /etc/kafka/server.properties

        if [[ ${SERVICE_HOST} ]]; then
            sudo sed -i "s/host\.name=127\.0\.0\.1/host.name=${SERVICE_HOST}/g" /etc/kafka/server.properties
            sudo sed -i "s/zookeeper\.connect=127\.0\.0\.1:2181/zookeeper.connect=${SERVICE_HOST}:2181/g" /etc/kafka/server.properties
        fi

        sudo cp -f "${MONASCA_ANALYTICS_BASE}"/devstack/files/kafka/kafka.service /etc/systemd/system/kafka.service
        sudo chmod 644 /etc/systemd/system/kafka.service

        sudo systemctl enable kafka
        sudo systemctl start kafka || sudo systemctl restart kafka
    else
        echo_summary "SKIP:Install Monasca Kafka"
    fi
}

###
function install_spark {
    echo_summary "Install Spark"

    sudo mkdir -p $SPARK_DOWNLOAD
    sudo chown -R stack:stack $SPARK_DIR
    sudo chmod -R 755 $SPARK_DIR
    mkdir -p ~/.m2

    sudo -E apt-get update

    install_pkg

    build_spark

    install_zookeeper

    install_kafka
}

###
function post_config_monasca_analytics {
:
}

###
function extra_monasca_analytics {
:
}


# check for service enabled
echo_summary "Monasca-analytics plugin with service enabled = `is_service_enabled monasca-analytics`"

if is_service_enabled monasca-analytics; then

    if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        # Set up system services
        echo_summary "Configuring Spark system services"
        pre_install_spark
        echo_summary "Configuring Monasca-analytics system services"
        pre_install_monasca_analytics

    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        # Perform installation of service source
        echo_summary "Installing Spark"
        install_spark

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        # Configure after the other layer 1 and 2 services have been configured
        echo_summary "Configuring Monasca-analytics"
        post_config_monasca_analytics

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        # Initialize and start the Monasca service
        echo_summary "Initializing Monasca-analytics"
        extra_monasca_analytics
    fi

    if [[ "$1" == "unstack" ]]; then
        echo_summary "Unstacking Monasca-analytics"
        unstack_monasca_analytics
    fi

    if [[ "$1" == "clean" ]]; then
        # Remove state and transient data
        # Remember clean.sh first calls unstack.sh
        echo_summary "Cleaning Monasca-analytics"
        clean_monasca_analytics
    fi

else
    echo_summary "Monasca-analytics not enabled"
fi

#Restore errexit
$ERREXIT

# Restore xtrace
$XTRACE
