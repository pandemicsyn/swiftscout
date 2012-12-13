Swift Scout
===========

A set of utilities for simplifying tasks in [Swift](http://github.com/openstack/swift)

## drivescout - scan for and easily bulk add devices to the ring.

drivescout lets you scan for hosts by interrogating nodes with [swift-recon](http://docs.openstack.org/developer/swift/admin_guide.html#cluster-telemetry-and-monitoring)
enabled to let you bulk add devices to the swift ring. It also supports add devices with a "target weight" for use with [swift-ring-master](http://github.com/pandemicsyn/swift-ring-master).

    Usage:
        usage: drivescout [-v] [--suppress] [-y] [-z zone] [-w weight] [-W tgt_weight]
        [-m "meta"] [--swift-dir=/etc/swift] builder.file

        ex: drivescout -y -r 1.1.1.1-254 -p 6000 --zone=1 -w 25 object.builder -y


    Options:
      -h, --help            show this help message and exit
      -v, --verbose         Print verbose info
      --dry-run             Dry run don't make any changes to builder files
      --suppress            Suppress most connection related errors
      -z ZONE, --zone=ZONE  Add devices to given zone
      -w WEIGHT, --weight=WEIGHT
                            Add devices with given weight
      -t TARGET_WEIGHT, --target-weight=TARGET_WEIGHT
                            Add devices with given target weight, Default = Not
                            Used
      --timeout=SECONDS     Time to wait for a response from a server
      -y, --yes             Answer all questions yes
      -m META, --meta=META  Default = Nothing
      -r IPRANGE, --iprange=IPRANGE
      -p PORT, --port=PORT
      -e DRIVE_EXCLUDE, --drive-exclude=DRIVE_EXCLUDE
                            Exclude drives matching this pattern
      -i DRIVE_INCLUDE, --drive-include=DRIVE_INCLUDE
                            Include only drives matching this pattern
      --mount-prefix=MOUNT_PREFIX
                            Search for drives mounted along this path
      --swiftdir=SWIFTDIR   Default = /etc/swift

## Sample usage

    fhines@ubuntu:~/swiftscout (master)$ bin/drivescout -r 172.16.63.128-150 -p 6010 /etc/swift/object.builder -z 4 -w 99 --mount-prefix=/mnt/sdb1/1/node
    Scanning 172.16.63.128-150[:6010] for drives to add to zone 4 with metadata []
    172.16.63.128:6010 found: ['sdc1']
    Add devices to ZONE 4: [y/n]: y
    Backed up builder too /etc/swift/backups/1347906863.object.builder (fd91cbc872d95488e7ec2476f304929c)
    Adding z4-172.16.63.128:6010/sdc1_ 99
    Success. /etc/swift/object.builder updated. (a3f942f954eeeb0287a5f7b35c3703fe)
    Rebalance still required.
    fhines@ubuntu:~/swiftscout (master)$ swift-ring-builder /etc/swift/object.builder 
    /etc/swift/object.builder, build version 5
    262144 partitions, 3 replicas, 4 zones, 5 devices, 2475.00 balance
    The minimum number of hours before a partition can be reassigned is 1
    Devices:    id  zone      ip address  port      name weight partitions balance meta
                 0     1       127.0.0.1  6010      sdb1   1.00     196608 2475.00 
                 1     2       127.0.0.1  6020      sdb2   1.00     196608 2475.00 
                 2     3       127.0.0.1  6030      sdb3   1.00     196608 2475.00 
                 3     4       127.0.0.1  6040      sdb4   1.00     196608 2475.00 
                 4     4   172.16.63.128  6010      sdc1  99.00          0 -100.00 

## Building a debian package:

    python setup.py --command-packages=stdeb.command bdist_deb
    dpkg -i deb_dist/python-swiftscout_X.X.Xall.deb
