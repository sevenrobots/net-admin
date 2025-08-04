## Network/WiFi setup 

Here are steps for WiFi setup to make it working in AP-STA mode. 

1. Working with local connected monitor and keyboard 

The network connections could be disrupted during the WiFi setup, so it will be much easier to work with locally connected monitor and keyboard. 

2. Prepare the system with internet access 

The internet access is needed for the setup, which could be through WiFi connection or ethernet connection.  

3. Script for WiFi setup 

Run below command to initially install necessary software and configure the WiFi setup. 

        ./network-init.sh 

After restart the system, the WiFi should alreay work in AP-STA mode. 

4. WiFi AP  

The default SSID and password for WiFi AP is "NetAdmin/password". The default IP address for the system is "10.0.0.1". The WiFi AP is always online so you may connect to the system through WiFi AP at any time. 

The WiFi AP is designed to work for network admin. Other applications should connect to the system through exernal WiFi router/network.   

5. WiFi STA   

Over the WiFi AP connection and the admin web UI we could configure the system to work as WiFi station, connecting to external WiFi router/network. 

Applications should connect to the system through the xternal WiFi router/network. 
