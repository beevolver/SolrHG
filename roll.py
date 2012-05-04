"""
example usage: fab -H localhost 1h 3h 6h 1d
from solr home - where example directory exists.
"""

from fabric.api import run, sudo
import os

INDEXDIR = 'solr/data/index/'
MASTER_PORT = 8983
SLAVE_START_PORT = 9000
upstart_prefix = 'solr_'
# slices[0] would be the master where hourglass is running.
slices = []
re_ts = r"(?P<number>\d+)(?P<period>[hdwm]{1})$"

def next_time_slice(t):
    try:
        return slices[slices.index(t) + 1]
    except IndexError, ValueError:
        return None

def merge(src, dest):
    #merge src and dest into dest
    class_path = 'solr/lib' # path to lucene-core-<version>.jar and lucene-misc-<version>.jar
    merge_tool = 'org/apache/lucene/misc/IndexMergeTool'
    run("mkdir -p %s" % dest)   # make dest dir if it doesn't exist
    return run('java -cp %(classpath)s/lucene-core-3.5.0.jar:%(classpath)s/lucene-misc-3.5.0.jar %(merge_tool)s %(dest)s %(src)s %(dest)s' % locals())

def merge_after(ts):
    get_index_path = lambda t: os.path.join('solr_%s' % t, 'solr/data/index')
    src = get_index_path(ts)
    dest = get_index_path(next_time_slice(ts))

    if ts == slices[0]:
        #if the slice is the master solr, take all subdirs of index to merge.
        src = os.path.join(src, '*')
    # there's nothing to merge if the timeslice is logically the last
    # todo: should remove the index in that case
    if ts != slices[-1]:
        return merge(src, dest)

def manage_solr(path, action='start'):
    if action not in ('start', 'stop', 'restart'):
        print >> sys.stderr, "solr to be %sed ? - failing to do so." % action
        return 1
    script_name = upstart_prefix + os.path.basename(path)
    upstart_script = "/etc/init/%s.conf" % (script_name)
    # make an upstart script from the template solr.conf, if it doesn't exist
    if not os.path.exists(upstart_script):
        java_home = os.path.join(os.path.abspath(os.path.curdir), path)
        sudo('bash solr.conf.sh %s >> %s' % (java_home, upstart_script))

    if action == 'restart':
        sudo('service stop %s' % script_name)
        sudo('service start %s' % script_name)
    else:
        sudo('service %s %s' % (action, script_name))

def create_cron_jobs():
    def create_cron_line(ts):
        d = dict(min='0', hour='*', day='*', month='*', dow='*')
        cmd = "fab -H localhost /path/to/this/file merge_after:%s" % ts
        a = re.match(ts)
        number, period = a.group('number'), a.group('period')
        if period == 'h':
            d['hour'] = '*/%d' % number
        else:
            d['hour'] = 0
            if period == 'd':
                d['day'] = '*/%d' % number
            elif period == 'm':
                d['day'] = '1'
                d['month'] = '*/%d' % number
            # mulitple weeks is not supported for now
            elif ts == '1w':
                d['dow'] = 6    #sat midnight (sun-sat 0-6)
        return ' '.join([d['min'], d['hour'], d['day'], d['month'], d['dow'], cmd)

        for ts in slices[:-1]:
            hash_bang = '#!/bin/bash\n'
            sudo("echo %s >> /etc/cron.d/cron_%s", hash_bang + create_cron_line(ts), ts)

def usage():
    print >> sys.stderr, 'Usage: %s arg1 arg2 [arg3...]' % sys.argv[0]
    print >> sys.stderr, 'where is argument is of the form <N><h/d/w/m>'
    print >> sys.stderr, 'N an integer and "h" for hour, "d" for "day", "w" for week, "m" for month'
    print >> sys.stderr, 'example: %s 1h 6h 12h 1d 1w' % sys.argv[0]
    return 1

def get_timeslices(args):
    for arg in args:
        matched = re.match(re_ts, arg)
        if not matched or matched.group(0) is not arg:
            return usage()
    return args

def make_solr_instance(path, port):
    master_port = MASTER_PORT
    run('mkdir -p %s' % path)
    run('cp -r example %s' % path)
    run('perl -pi -e s/%(master_port)d/%(port)d/g %(path)s/solr/etc/jetty.xml' % locals())
    if port == master_port:
        run('cp conf/solrconfig.xml %s/solr/conf/solrconfig.xml' % path)
    else:
        run('cp conf/non_hg_solrconfig.xml %s/solr/conf/solrconfig.xml' % path)
    return manage_solr(path, action='start')
    
def make_rolling_index():
    make_solr_instance('solr_' + slices[0], master_port)
    port = SLAVE_START_PORT
    for ts in slices[1:]:
        make_solr_instance('solr_' + ts, port)
        port += 1

if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        return usage()
    
    global slices
    slices = get_timeslices(sys.argv[1:])
    return make_rolling_index() 
