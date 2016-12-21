# This file is intended to be used by vagrant only.
if [ "$VAGRANT_ENV" ]; then

  # Create a temporary folder
  mkdir ~/tmp
  cd ~/tmp

  # Java 8
  sudo -E apt-get update
  sudo -E apt-get -y install openjdk-7-jre-headless openjdk-7-jdk

  # Maven
  curl ftp://mirror.reverse.net/pub/apache/maven/maven-3/3.3.9/binaries/apache-maven-3.3.9-bin.tar.gz > mvn.tar.gz
  tar -xzf mvn.tar.gz
  sudo mv apache-maven-3.3.9 /usr/local/apache-maven-3.3.9
  echo 'export PATH=/usr/local/apache-maven-3.3.9/bin:$PATH' >> $HOME/.profile
  source $HOME/.profile
  mkdir ~/.m2
  LENGTH_FOR_HOST=`expr match "$HTTP_PROXY" 'http://[\.A-Za-z\-]*'`-7
  echo '<?xml version="1.0" encoding="UTF-8"?>
    <settings xmlns="http://maven.apache.org/SETTINGS/1.1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.1.0 http://maven.apache.org/xsd/settings-1.1.0.xsd">
    <proxies>
    <proxy>'"
        <active>true</active>
        <protocol>http</protocol>
        <host>${HTTP_PROXY:7:$LENGTH_FOR_HOST}</host>
        <port>8080</port>
        <nonProxyHosts>localhost</nonProxyHosts>
    </proxy>
    </proxies></settings>" > ~/.m2/settings.xml


  # Scala
  curl https://downloads.typesafe.com/scala/2.11.7/scala-2.11.7.deb > scala.deb
  sudo dpkg -i scala.deb

  # Scala build tool
  echo "deb https://dl.bintray.com/sbt/debian /" | sudo tee -a /etc/apt/sources.list.d/sbt.list
  sudo -E apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 642AC823
  sudo -E apt-get update
  sudo -E apt-get -y install sbt

  # Spark
  curl http://apache.claz.org/spark/spark-1.6.2/spark-1.6.2.tgz > spark.tgz
  echo "-------------------------"
  echo "unzip spark to ~/spark"
  mkdir ~/spark/
  tar -xzf spark.tgz
  mv spark-1.6.2/ ~/spark/spark-1.6.2
  cd ~/spark/spark-1.6.2
  mvn -DskipTests clean package
  cd ~/tmp
  # config for logging in spark
  cp ~/spark/spark-1.6.2/conf/log4j.properties.template ~/spark/spark-1.6.2/conf/log4j.properties
  sed -i 's/log4j.rootCategory=INFO/log4j.rootCategory=ERROR/g' ~/spark/spark-1.6.2/conf/log4j.properties

  # Kafka
  mkdir ~/kafka
  curl http://apache.arvixe.com/kafka/0.9.0.0/kafka_2.11-0.9.0.0.tgz > kafka.tgz
  echo "-------------------------"
  echo "unzip kafka to ~/kafka"
  tar -xzf kafka.tgz -C ~/kafka
  mv ~/kafka/kafka_2.11-0.9.0.0/* ~/kafka
  rm -r ~/kafka/kafka_2.11-0.9.0.0

  # Python dependencies
  sudo -E apt-get -y install python-pip python-setuptools
  sudo -E pip install pep8

  # Remove temporary folder
  echo "-------------------------"
  echo "Removing temporary folder"
  rm -r ~/tmp

  # Monanas dependencies
  echo "-------------------------"
  echo "Get Monanas deps"
  cd /vagrant
  sudo -E apt-get -y install python-numpy python-scipy ipython
  sudo -E -H python setup.py develop

  # Environment setup
  set -v
  echo 'export SPARK_HOME=~/spark/spark-1.6.1' >> $HOME/.profile
  echo 'export KAFKA_HOME=~/kafka' >> $HOME/.profile
  echo 'export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.9-src.zip:$PYTHONPATH' >> $HOME/.profile
  set +v

else
  echo "This file is intended to be used by a vagrant vm only."
fi
