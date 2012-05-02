"""
Usage: fab -H localhost day/week/month/6months
from solr home - where example directory exists.
"""

from fabric.api import run
from urllib2 import URLError, urlopen
from urlparse import urljoin
import date, datetime

INDEXDIR = 'solr/data/index/'
SOLR_SLAVE_URL = 'http://localhost:9000/'
slices = []

def next_time_slice(t):
    try:
        return slices[slices.index(t) + 1]
    except IndexError, ValueError:
        return None
    
def merge(src, dest):
    class_path = 'solr/lib' # path to lucene-core-<version>.jar and lucene-misc-<version>.jar    
    run('java -cp %(classpath)s/lucene-core-3.5.0.jar:%(classpath)s/lucene-misc-3.5.0.jar org/apache/lucene/misc/IndexMergeTool %(src)s %(dest)s' % locals())

def commit():
    run('curl %s' % urljoin(SOLR_SLAVE_URL, '/solr/update?commit=true'))

def restart():
    # should daemonize solr and put the command to restart
    #run('java -java start.jar')

def hourend():
    """ For testing purposes. 
        Merge this houroday's data with tweek's (Sun-Sat) data - before the hourglass roll happens
        call me in mid night of every day"""

def dayend():
    """ Merge today's data with this week's (Sun-Sat) data - before the hourglass roll happens
        call me in mid night of every day"""
    pass

def weekend():
    """ Merge this week's data with this month's data - before the hourglass roll happens
        Every saturday midnight, call me."""
   pass

def monthend():
    pass

def usage():
    print >> sys.stderr, 'Usage: %s arg1 arg2 [arg3...]' % sys.argv[0]
    print 'where is argument is of the form <N><h/d/w/m/y>'
    print 'N an integer and "h" for hour, "d" for "day", "w" for week, "m" for month and "y" for year'
    print 'example: %s 1h 6h 12h 1d 1w' % sys.argv[0]
    return 1

def get_timeslices(args):
    for arg in args:
        matched = re.match(r"(?P<number>\d+)(?P<period>[hdwmyHDWMY]{1})$", arg)
        if not matched or matched.group(0) is not arg or matched.group('period') not in allowed_ts:
            return usage()
    return args

def make_solr_instance(path, port):
    run('mkdir -p %s' % path)
    run('cp -r example %s' % path)
    run('perl -pi -e s/8983/%(port)d/g %(path)s/solr/etc/jetty.xml' % locals())
    run('cp non_hg_solrconfig.xml %s/solr/conf/solrconfig.xml')
    
def make_rolling_index():
    port = 9000
    for ts in slices:
        make_solr_instance(ts, port)
        port += 1

if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        return usage()
    
    global slices
    slices = get_timeslices(sys.argv[1:])
    return make_rolling_index() 
