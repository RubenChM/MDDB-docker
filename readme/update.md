# Update services

This section explains in detail how to **update** one or more **services** of the docker swarm.

## Check & update

An **update script** is provided for checking the **versions** of all the running services and see if there are **updates** available. This same script allows to **update** one or all the updatable services.

How to execute the script from the root of this repository:

```sh
python3 scripts/update.py
```

Example of output:

```sh
============================================================
📊 VERSION SUMMARY
============================================================
Service         Current      Latest       Status         
------------------------------------------------------------
client          0.0.2        0.0.2        ✅ Up to date   
rest            0.0.1        0.0.1        ✅ Up to date   
vre_lite        0.0.1        0.0.1        ✅ Up to date   
loader          0.0.1        0.0.1        ✅ Up to date   
workflow        0.1.1        0.1.4        🆙 Updatable    

============================================================
🎯 1 service(s) can be updated:
   • workflow: 0.1.1 -> 0.1.4

============================================================
🛠️  INTERACTIVE UPDATE MENU
============================================================
Available actions:
1. Update all services
2. Update specific service
3. Show version summary
4. Re-check versions
5. Exit
```

In this case, the workflow service is **updatable**, so after selecting options 1 or 2, the **service** is updated and the following output is shown:

```sh
============================================================
📊 VERSION SUMMARY
============================================================
Service         Current      Latest       Status         
------------------------------------------------------------
client          0.0.2        0.0.2        ✅ Up to date   
rest            0.0.1        0.0.1        ✅ Up to date   
vre_lite        0.0.1        0.0.1        ✅ Up to date   
loader          0.0.1        0.0.1        ✅ Up to date   
workflow        0.1.4        0.1.4        ✅ Up to date   

============================================================
✅ All services are up to date!

============================================================
🛠️  INTERACTIVE UPDATE MENU
============================================================
✅ No services need updating!
```

The script recognises the **services in development** and marks them as non-updatable:

```sh
============================================================
📊 VERSION SUMMARY
============================================================
Service         Current      Latest       Status         
------------------------------------------------------------
client          0.0.2        0.0.2        ✅ Up to date   
rest            0.0.1        0.0.1        ✅ Up to date   
vre_lite        dev          0.0.2        📦 Development  
loader          0.0.1        0.0.1        ✅ Up to date   
workflow        0.1.4        0.1.4        ✅ Up to date   

============================================================
✅ All services are up to date!

============================================================
🛠️  INTERACTIVE UPDATE MENU
============================================================
✅ No services need updating!

1. Re-check versions
2. Exit
```

## Rebuild service(s)

A **rebuild script** is provided for rebuilding **one or more services** in an **automatic** way. Please execute the script, located in [**scripts/rebuild.py**](../scripts/rebuild.py). 

How to execute the help script from the root of this repository:

```sh
python3 scripts/rebuild.py -h
```

Example for rebuilding the **client** and **vre_lite** services from the **my_stack** stack: 

```sh
python3 scripts/rebuild.py -s client vre_lite -t my_stack
```

Note that this script will **rebuild the service** to the **latest** available **version**.

For performing the same process step by step:

1. **Rebuild the Service Image Without Cache:** Use docker-compose to rebuild the image locally, targeting only the service you want to update:

    ```sh
    docker-compose build --no-cache <service_name>
    ```

2. **Update the Service in the Swarm:** In Docker Swarm, you can force the service to use the updated image by running:

    ```sh
    docker service update --force <stack_name>_<service_name>
    ```

3. **Remove Stopped Container(s):** After updating the service, the old container remains stopped, execute the following instruction for removing it:

    ```sh
    docker container prune -f
    ````

4. **Remove Unused Image(s):** After rebuilding the image, the old image remains unused, execute the following instruction for removing it:

    ```sh
    docker image prune -f
    ```

A **rollback script** is provided for rebuilding an old version of **one service** in an **automatic** way. Please execute the script, located in [**scripts/rebuild-legacy.py**](../scripts/rebuild-legacy.py). 

How to execute the help script from the root of this repository:

```sh
python3 scripts/rebuild-legacy.py -h
```

Example for rollback to the **version 0.0.1** of the **client** service from the **my_stack** stack: 

```sh
python3 scripts/rebuild-legacy.py -s client vre_lite -v 0.0.1 -t my_stack
```

## Update services versions

The versions for **each service** of the stack are stored into a database. The **status** of these services is shown in the **VRE lite service**. Though this script is **integrated** into the automatic **deploy** script, it can be used **separately** for updating all the versions in a single call:

```sh
python3 scripts/update-services-versions.py 
```
