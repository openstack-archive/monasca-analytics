# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Default box
  config.vm.box = "ubuntu/trusty64"

  # Setup port for Machine Learning Framework
  config.vm.network "forwarded_port", guest: 3000, host: 3000
  config.vm.network "forwarded_port", guest: 4040, host: 4040

  # Shell provisioning
  config.vm.provision "shell",
    inline: "echo 'export VAGRANT_ENV=1' >> /home/vagrant/.profile"

  config.vm.provision "shell" do |s|
    # s.env is only available since Vagrant 1.8
    s.path = "fetch-deps.sh"
    s.privileged = false
  end

  # Virtual box settings
  config.vm.provider "virtualbox" do |v|
    v.memory = 4096
    v.cpus = 3
  end

  # Proxy settings
  if Vagrant.has_plugin?("vagrant-proxyconf")
     config.proxy.http     = ENV['HTTP_PROXY'] || ENV['http_proxy']
     config.proxy.https    = ENV['HTTPS_PROXY'] || ENV['https_proxy']
     config.proxy.no_proxy = "localhost,127.0.0.1"
  end

end
