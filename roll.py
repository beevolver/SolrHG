"""
example usage: fab -H localhost 1h 1d 1m
from solr home - where example directory exists.
"""

from fabric.api import run, sudo, abort, cd, task
from fabric.operations import put
import os, re

EXAMPLE_PATH = '/mnt/apache-solr-3.5.0'
INDEXDIR = 'solr/data/index/'
MASTER_PORT = 8983
SLAVE_START_PORT = 9000
LOG_FILE = "/var/log/solrhg" 
# slices[0] would be the master where hourglass is running.
slices = []
re_ts = r"(?P<number>\d+)(?P<period>[hdwm]{1})$"

def next_time_slice(t):
    try:
        return slices[slices.index(t) + 1]
    except IndexError, ValueError:
        return None

def merge(src, dest, class_path):
    #merge src and dest into dest
    merge_tool = 'org/apache/lucene/misc/IndexMergeTool'
    redirect_logs = ">> %s 2>&1" % LOG_FILE
    run("mkdir -p %s" % dest)   # make dest dir if it doesn't exist
    return run('java -cp %(class_path)s/lucene-core-3.5.0.jar:%(class_path)s/lucene-misc-3.5.0.jar %(merge_tool)s %(dest)s %(src)s %(dest)s' % locals())

def get_subdirs(path):
    return [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x)) and not x.startswith('.')]

@task
def merge_slices(ts1, ts2):
    get_index_path = lambda t: os.path.join('solr_%s' % t, 'solr/data/index')
    get_lib_path = lambda t: os.path.join('solr_%s' % t, 'solr/lib') # path to lucene-core-<version>.jar and lucene-misc-<version>.jar
    src, dest = get_index_path(ts1), get_index_path(ts2)

    # if src has sub dirs (which are created by hourglass), take the subdirs
    subdirs = get_subdirs(src)
    if subdirs:
        src = ' '.join([os.path.join(src, subdir) for subdir in subdirs])
    # there's nothing to merge if the timeslice is logically the last
    # todo: should remove the index in that case
    return merge(src, dest, class_path=get_lib_path(ts1))

@task
def manage_solr(path, action='start'):
    if action not in ('start', 'stop', 'restart'):
        print >> sys.stderr, "solr to be %sed ? - failing to do so." % action
        return 1
    script_name = os.path.basename(path)
    upstart_script = "/etc/init/%s.conf" % (script_name)
    # make an upstart script from the template solr.conf, if it doesn't exist
    if not os.path.exists(upstart_script):
        java_home = os.path.join(run('pwd'), path)
        sudo('bash solr.conf.sh %s > %s' % (java_home, upstart_script))

    sudo('service %s %s' % (script_name, action))

def create_cron_jobs():
    def create_cron_line(ts):
        d = dict(min='0', hour='*', day='*', month='*', dow='*')
        cmd = "fab -H localhost -f %s/roll.py merge_slices:%s,%s" % (run('pwd'), ts, next_time_slice(ts))
        redirect_logs = ">> %s 2>&1" % LOG_FILE
        user = 'root'
        a = re.match(re_ts, ts)
        number, period = a.group('number'), a.group('period')
        if period == 'h':
            d['hour'] = '*/%s' % number
        else:
            d['hour'] = '0'
            if period == 'd':
                d['day'] = '*/%s' % number
            elif period == 'm':
                d['day'] = '1'
                d['month'] = '*/%s' % number
            # mulitple weeks is not supported for now
            elif ts == '1w':
                d['dow'] = '6'    #sat midnight (sun-sat 0-6)
        return ' '.join([d['min'], d['hour'], d['day'], d['month'], d['dow'], user, cmd, redirect_logs])

    for ts in slices[:-1]:
        sudo("echo '%s' > /etc/cron.d/solr_%s" % (create_cron_line(ts), ts))

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

def upload_files(path, libs=True):
    # upload all the necessary files
    put('solr.conf.sh', 'solr.conf.sh')
    put('roll.py', 'roll.py')

    solrconf_path = '%s/solr/conf/' % path
    put('conf/schema.xml', solrconf_path)
    if path.endswith(slices[0]): # master/writer solr
        put('conf/solrconfig.xml', solrconf_path)
        if libs:
            put('vendor/lib', '%s/solr/' % path)
    else:
        put('conf/non_hg_solrconfig.xml', os.path.join(solrconf_path, 'solrconfig.xml'))
        run('ln -sf solr_%s/solr/lib %s/solr/lib' % (slices[0], path))

def make_solr_instance(path, port):
    master_port = MASTER_PORT
    run('mkdir -p %s' % path)
    run('cp -R example/* %s' % path)
    run('perl -pi -e s/%(master_port)d/%(port)d/g %(path)s/etc/jetty.xml' % locals())
    upload_files(path)
    return manage_solr(path, action='start')

@task
def make_rolling_index(*argv):
    global slices
    slices = get_timeslices(argv)
    with cd(EXAMPLE_PATH):
        make_solr_instance('solr_' + slices[0], MASTER_PORT)
        port = SLAVE_START_PORT
        for ts in slices[1:]:
            make_solr_instance('solr_' + ts, port)
            port += 1
        create_cron_jobs()

if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        usage()
        abort(1)
    make_rolling_index(sys.argv[1:])
