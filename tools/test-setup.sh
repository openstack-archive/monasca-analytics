#!/bin/bash -xe

# This script will be run by OpenStack CI before unit tests are run,
# it sets up the test system as needed.
# Developers should setup their test systems in a similar way.

HOME=${{HOME:-/home/jenkins}}
SPARK_DIR=$HOME/spark
SPARK_VERSION=${{SPARK_VERSION:-1.6.1}}
SPARK_TARBALL_NAME=spark-$SPARK_VERSION.tgz
SPARK_URL=http://archive.apache.org/dist/spark/spark-$SPARK_VERSION/$SPARK_TARBALL_NAME

mkdir -p $SPARK_DIR
curl $SPARK_URL -o $SPARK_DIR/$SPARK_TARBALL_NAME
tar -xzf $SPARK_DIR/$SPARK_TARBALL_NAME -C $SPARK_DIR
