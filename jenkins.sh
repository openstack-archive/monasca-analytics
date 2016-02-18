# Everything will be done in a tmp directoy.
mkdir ~/tmp-build-for-arc-alc
cd ~/tmp-build-for-arc-alc


if hash scala 2>/dev/null; then
  # Scala is installed do nothing
  echo "Scala is already installed"
else
  # Install it
  curl https://downloads.typesafe.com/scala/2.11.7/scala-2.11.7.deb > scala.deb
  sudo dpkg -i scala.deb
  # Install sbt
  echo "deb https://dl.bintray.com/sbt/debian /" | sudo tee -a /etc/apt/sources.list.d/sbt.list
  sudo -E apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 642AC823
  sudo -E apt-get update
  sudo -E apt-get -y install sbt
fi


if [ "$SPARK_HOME" ]; then
  # Spark is installed and home is setup properly
  echo "Spark is already installed"
else
  curl http://apache.arvixe.com/spark/spark-1.4.1/spark-1.4.1.tgz > spark.tgz
  tar -xzf spark.tgz
  mv spark-1.4.1/ ~/spark
  cd ~/spark
  mvn -DskipTests clean package
  cp ~/spark/conf/log4j.properties.template ~/spark/conf/log4j.properties
  sed -i 's/log4j.rootCategory=INFO/log4j.rootCategory=ERROR/g' ~/spark/conf/log4j.properties
  set -v
  echo 'export SPARK_HOME=~/spark' >> $HOME/.profile
  echo 'export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.8.2.1-src.zip:$PYTHONPATH' >> $HOME/.profile
  set +v
  cd ~/tmp-build-for-arc-alc
fi


if hash pep8 2>/dev/null; then
  echo "Pep8 is already installed!"
else
  sudo -E apt-get -y install python-pip python-setuptools
  sudo -E pip install pep8
fi


# Python dependencies
sudo -E apt-get -y install python-numpy python-scipy ipython python-pyparsing
sudo -E -H python setup.py develop


# Remove tmp directory
cd ..
rm tmp-build-for-arc-alc
