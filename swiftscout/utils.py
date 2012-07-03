import eventlet
from eventlet import sleep, Timeout
from eventlet.green import urllib2
try:
    import simplejson as json
except ImportError:
    import json
from swift.common.exceptions import LockTimeout


class Scout(object):
    """
    Obtain swift recon information
    """

    def __init__(self, recon_type, verbose=False, suppress_errors=False,
                 timeout=5):
        self.recon_type = recon_type
        self.verbose = verbose
        self.suppress_errors = suppress_errors
        self.timeout = timeout

    def scout_host(self, base_url, recon_type):
        """
        Perform the actual HTTP request to obtain swift recon telemtry.

        :param base_url: the base url of the host you wish to check. str of the
                        format 'http://127.0.0.1:6000/recon/'
        :param recon_type: the swift recon check to request.
        :returns: tuple of (recon url used, response body, and status)
        """
        url = base_url + recon_type
        try:
            body = urllib2.urlopen(url, timeout=self.timeout).read()
            content = json.loads(body)
            if self.verbose:
                print "-> %s: %s" % (url, content)
            status = 200
        except urllib2.HTTPError as err:
            if not self.suppress_errors or self.verbose:
                print "-> %s: %s" % (url, err)
            content = err
            status = err.code
        except urllib2.URLError as err:
            if not self.suppress_errors or self.verbose:
                print "-> %s: %s" % (url, err)
            content = err
            status = -1
        return url, content, status

    def scout(self, host):
        """
        Obtain telemetry from a host running the swift recon middleware.

        :param host: host to check
        :returns: tuple of (recon url used, response body, and status)
        """
        base_url = "http://%s:%s/recon/" % (host[0], host[1])
        url, content, status = self.scout_host(base_url, self.recon_type)
        return url, content, status


class RingScan(object):

    def __init__(self, verbose=False, suppress_errors=False, pool_size=25,
                 timeout=1):
        self.verbose = verbose
        self.suppress_errors = suppress_errors
        self.timeout = timeout
        self.pool_size = pool_size
        self.pool = eventlet.GreenPool(self.pool_size)

    def drive_scan(self, hosts):
        recon = Scout('mounted', self.verbose, self.suppress_errors,
                      self.timeout)
        responses = {}
        for url, response, status in self.pool.imap(recon.scout, hosts):
            responses[url] = {'devices': response, 'status': status}
        return responses
