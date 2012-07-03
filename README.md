Swift Scout
===========

A set of utilities for simplifying tasks in [Swift](http://github.com/openstack/swift)

## ringscout - scan for and easily bulk add devices to the ring.

ringscout lets you scan for hosts and interrogates nodes with [swift-recon](http://docs.openstack.org/developer/swift/admin_guide.html#cluster-telemetry-and-monitoring) enabled to let you bulk add devices to the swift ring.

    Usage:
        usage: ringscout [-v] [--suppress] [-y] [-z zone] [-w weight] [-m "meta"]
        [--swift-dir=/etc/swift] builder.file

        ex: ringscout -y -r 1.1.1.1-254 -p 6000 --zone=1 -w 25 object.builder -y


    Options:
      -h, --help            show this help message and exit
      -v, --verbose         Print verbose info
      --dry-run             Dry run don't make any changes to builder files
      --suppress            Suppress most connection related errors
      -z ZONE, --zone=ZONE  Add devices to given zone
      -w WEIGHT, --weight=WEIGHT
                            Add devices with given weight
      -t SECONDS, --timeout=SECONDS
                            Time to wait for a response from a server
      -y, --yes             Answer all questions yes
      -m META, --meta=META  Default = Nothing
      -r IPRANGE, --iprange=IPRANGE
      -p PORT, --port=PORT
      -e DRIVE_EXCLUDE, --drive-exclude=DRIVE_EXCLUDE
                            Exclude drives matching this pattern
      -i DRIVE_INCLUDE, --drive-include=DRIVE_INCLUDE
                            Include only drives matching this pattern
      --swiftdir=SWIFTDIR   Default = /etc/swift

## Building a debian package:

    python setup.py --command-packages=stdeb.command bdist_deb
    dpkg -i deb_dist/python-swiftscout_X.X.Xall.deb
