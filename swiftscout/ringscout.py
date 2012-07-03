#!/usr/bin/env python
from swiftscout.utils import RingScan
from urlparse import urlparse
from sys import exit, argv, modules
import optparse
import cPickle as pickle
from os.path import basename, isfile, join as pathjoin
from hashlib import md5
from swift.common.ring import RingBuilder
from time import time
from errno import EEXIST
from os import mkdir
import re


class RingScout(object):

    def __init__(self, builder_file, swiftdir='/etc/swift',
                 backup_dir_name='backups', verbose=False):
        self.verbose = verbose
        self.builder_file = builder_file
        self.swiftdir = swiftdir
        self.backup_dir = pathjoin(self.swiftdir, backup_dir_name)
        if self.verbose:
            print ">>> Loading %s (%s)" % (
                self.builder_file, self.get_md5sum(self.builder_file))
        try:
            self.builder = pickle.load(open(self.builder_file, 'rb'))
            if not hasattr(self.builder, 'devs'):
                if self.verbose:
                    print ">>> No devs, calling RingBuilder"
                builder_dict = self.builder
                self.builder = RingBuilder(1, 1, 1)
                self.builder.copy_from(builder_dict)
        except ImportError:  # Happens with really old builder pickles
            if self.verbose:
                print ">>> Using old builder"
            modules['swift.ring_builder'] = \
                modules['swift.common.ring.builder']
            self.builder = RingBuilder(1, 1, 1)
            self.builder.copy_from(pickle.load(open(self.builder_file, 'rb')))
        for dev in self.builder.devs:
            if dev and 'meta' not in dev:
                dev['meta'] = ''

    def make_backup(self):
        """Create a backup of the current builder builder contents"""
        try:
            mkdir(self.backup_dir)
        except OSError, err:
            if err.errno != EEXIST:
                raise
        backup = pathjoin(self.backup_dir, '%d.' %
                          time() + basename(self.builder_file))
        pickle.dump(self.builder.to_dict(), open(backup, 'wb'), protocol=2)
        print "Backed up builder too %s (%s)" % \
              (backup, self.get_md5sum(backup))

    def get_md5sum(self, filename):
        """Get the md5sum of a given file"""
        md5sum = md5()
        with open(filename, 'rb') as f:
            block = f.read(4096)
            while block:
                md5sum.update(block)
                block = f.read(4096)
        return md5sum.hexdigest()

    def is_existing_dev(self, ip, port, device_name):
        """Check if a device is currently present in the builder"""
        for dev in self.builder.devs:
            if dev is None:
                continue
            if dev['ip'] == ip and dev['port'] == port and \
                    dev['device'] == device_name:
                return True
        return False

    def add_dev(self, ip, port, device_name, zone, weight, meta):
        """Add a device to the builder"""
        next_dev_id = 0
        if self.builder.devs:
            next_dev_id = max(d['id'] for d in self.builder.devs if d) + 1
        self.builder.add_dev({'id': next_dev_id, 'zone': zone, 'ip': ip,
                              'port': int(port), 'device': device_name,
                              'weight': weight, 'meta': meta})

    def dump_builder(self):
        """Dump builder state to disk"""
        pickle.dump(self.builder.to_dict(), open(self.builder_file, 'wb'),
                    protocol=2)
        print "Success. %s updated. (%s)" % (
            self.builder_file, self.get_md5sum(self.builder_file))
        print "Rebalance still required."

    def parse_ip(self, ipaddr):
        """Parse an ip range (single ip), and return a list of validated ips"""
        #todo validate ip. regex ?
        if ipaddr.count('.') == 3:
            if ipaddr.count('-') == 0:
                return [ipaddr]
            elif ipaddr.count('-') == 1:
                prefix, iprange = ipaddr.rsplit('.', 1)
                start, stop = iprange.split('-')
                ips = []
                for last_octet in xrange(int(start), int(stop) + 1):
                    ips.append('%s.%s' % (prefix, last_octet))
                return ips
            else:
                print "Invalid ip range"
                exit(1)
        else:
            print "Malformed ip"
            exit(1)

    def scan(self, hosts, zone, meta, weight, drive_prefix='/srv/node',
             include_pattern=None, exclude_pattern=None, dry_run=False,
             confirm=True):
        """Search for and possible add devices to the ring by querying the
        recon interface on a provide iprange."""
        exclude = re.compile(exclude_pattern)
        include = re.compile(include_pattern)
        r = RingScan(pool_size=250, verbose=False, suppress_errors=True)
        found = {}
        result = r.drive_scan(hosts)
        for host in result:
            devs = []
            if result[host]['status'] != 200:
                continue
            for i in result[host]['devices']:
                if i['device']:
                    if i['path'].startswith(drive_prefix):
                        device_name = basename(i['path'])
                        if exclude_pattern and include_pattern:
                            if not exclude.match(device_name) \
                                    and include.match(device_name):
                                devs.append(device_name)
                        elif exclude_pattern and \
                                not exclude.match(device_name):
                            devs.append(device_name)
                        elif include_pattern and \
                                include.match(device_name):
                            devs.append(device_name)
                        else:
                            devs.append(device_name)
            if len(devs) > 0:
                found[urlparse(host).netloc] = devs
                print "%s found: %s" % (urlparse(host).netloc,
                                        found[urlparse(host).netloc])
        if len(found) == 0:
            print "no devices found"
            exit(1)
        if confirm:
            confirm_resp = raw_input('Add devices to ZONE %s: [y/n]: ' % zone)
            confirm_resp = confirm_resp.strip().lower()
            if not confirm_resp == "yes" and not confirm_resp == "y":
                print "aborting."
                exit(1)
        self.make_backup()
        for host in found:
            for device in found[host]:
                print "Adding z%s-%s/%s_%s %s" % (zone, host, device, meta,
                                                  weight)
                ip, port = host.split(':')
                port = int(port)
                if self.is_existing_dev(ip, port, device):
                    print "Skipped %s on %s already in ring." % (device, host)
                else:
                    self.add_dev(ip, port, device, zone, weight, meta)
        if not dry_run:
            self.dump_builder()


def cli():
    usage = '''
    usage: %prog [-v] [--suppress] [-y] [-z zone] [-w weight] [-m "meta"]
    [--swift-dir=/etc/swift] builder.file

    ex: %prog -y -r 1.1.1.1-254 -p 6000 --zone=1 -w 25 object.builder -y
    '''
    args = optparse.OptionParser(usage)
    args.add_option('--verbose', '-v', action="store_true",
                    help="Print verbose info")
    args.add_option('--dry-run', action="store_true",
                    help="Dry run don't make any changes to builder files")
    args.add_option('--suppress', action="store_true",
                    help="Suppress most connection related errors")
    args.add_option('--zone', '-z', type="int",
                    help="Add devices to given zone")
    args.add_option('--weight', '-w', type="int",
                    help="Add devices with given weight")
    args.add_option('--timeout', '-t', type="int", metavar="SECONDS",
                    help="Time to wait for a response from a server",
                    default=1)
    args.add_option('--yes', '-y', action="store_true",
                    help="Answer all questions yes")
    args.add_option('--meta', '-m', default="", help="Default = Nothing")
    args.add_option('--iprange', '-r', default="", help="")
    args.add_option('--port', '-p', default="", help="")
    args.add_option('--drive-exclude', '-e', default="",
                    help="Exclude drives matching this pattern")
    args.add_option('--drive-include', '-i', default="",
                    help="Include only drives matching this pattern")
    args.add_option('--swiftdir', default="/etc/swift",
                    help="Default = /etc/swift")
    options, arguments = args.parse_args()

    if len(argv) <= 1 or len(arguments) > 1:
        args.print_help()
        exit(0)
    if not arguments:
        args.print_help()
        print "Failed to specify a builder file"
        exit(1)
    else:
        builder_file = arguments[0]
        if not isfile(builder_file):
            print "Not a valid builder file."
            print "Perhaps you need to create it first?"
            exit(1)
    if options.drive_exclude and options.drive_include:
        print "Error: Can't specify a exclude pattern AND include pattern."
        args.print_help()
        exit(1)
    if options.iprange:
        iprange = options.iprange
    else:
        iprange = raw_input('Enter ip range to scan [ex: 10.1.1.1-254]: ')
    if options.port:
        port = options.port
    else:
        print "Enter port you wish to scan for on a recon enabled service."
        print "This port will be used when adding the device to the ring."
        port = raw_input('[ex: 6000]: ')
        if not port.isdigit():
            print "Aborting. You failed to specify a digit for a port"
            exit(1)
    if options.zone:
        zoneid = options.zone
    else:
        zoneid = raw_input('Enter zone id to use: ').strip()
        if not zoneid.isdigit():
            print "Aborting. You failed to specify a digit for a zone id."
            exit(1)
    if options.weight:
        weight = options.weight
    else:
        read_weight = raw_input('Enter weight for devices: ').strip()
        try:
            weight = float(read_weight)
        except ValueError:
            print "Aborting. Invalid weight. Must be a digit/float."
            exit(1)
        if weight < 0:
            print "Aborting. Invalid weight. Must be positive."
            exit(1)
    if options.yes:
        confirm = False
    else:
        confirm = True
    print "Scanning %s for drives to add to zone %s with metadata [%s]" % \
          (iprange, zoneid, options.meta)

    scout = RingScout(builder_file, swiftdir=options.swiftdir,
                      verbose=options.verbose)
    hosts = [(ip, port) for ip in scout.parse_ip(iprange)]

    scout.scan(hosts, zone=zoneid, meta=options.meta, weight=weight,
               exclude_pattern=options.drive_exclude,
               include_pattern=options.drive_include, dry_run=False,
               confirm=confirm)

if __name__ == '__main__':
    cli()