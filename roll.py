"""
example usage: fab -H localhost 1h 1d 1m
from solr home - where example directory exists.
"""

from fabric.api import run, sudo, abort, cd, task, local, lcd
from fabric.operations import put
import os, re
from datetime import datetime, timedelta
from config import *

# slices[0] would be the master where hourglass is running.
slices = []
re_ts = r"(?P<number>\d+)(?P<period>[hdwm]{1})$"

def log_info(msg):
    run("(date && echo %s)" >> LOG_FILE)

def set_tz():
    return "TZ=US/Eastern\n"

def next_time_slice(t):
    try:
        return slices[slices.index(t) + 1]
    except IndexError, ValueError:
        return None

def post_stop_hg(path):
    """ return the command in post-stop script to be put in the upstart script of the solr HG
    """
    fab = run('which fab')
    ts = slices[0]
    merge_cmd = "%s -f %s/roll.py merge_slices:%s,%s" % (fab, EXAMPLE_PATH, ts, next_time_slice(ts))
    redirect_logs = ">> %s 2>&1" % LOG_FILE
    path = os.path.join(EXAMPLE_PATH, path)
    # @@ todo: fix this - make 2012-* generic
    mv2archive = "mv -f %s/solr/data/index/2012-* %s/solr/data/archive/" % (path, path)
    return "%(mv2archive)s && %(merge_cmd)s %(redirect_logs)s" % locals()

def memory_to_solr():
    #/proc/meminfo has a line like - MemTotal:  509084 kB
    parts = len(slices) + 1 # give equal memory to each slice and for OS
    return run("cat /proc/meminfo | grep MemTotal | awk '{ printf " + '"%d%s", ' + "$(NF-1)/%s, $NF }' | tr -d 'B' " % parts)

def merge(src, dest, class_path):
    #merge src and dest into dest
    merge_tool = 'org/apache/lucene/misc/IndexMergeTool'
    local("mkdir -p %s" % dest)   # make dest dir if it doesn't exist
    with lcd(EXAMPLE_PATH):
        return local('sudo java -cp %(class_path)s/lucene-core-3.5.0.jar:%(class_path)s/lucene-misc-3.5.0.jar %(merge_tool)s %(dest)s %(src)s %(dest)s' % locals())

def get_subdirs(path):
    path = os.path.join(EXAMPLE_PATH, path)
    return [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x)) and not x.startswith('.')]

@task
def merge_slices(ts1, ts2):
    log_info('attempting to merge slices %s %s' % (ts1, ts2))
    get_index_path = lambda t: os.path.join('solr_%s' % t, 'solr/data/index')
    get_lib_path = lambda t: os.path.join('solr_%s' % t, 'solr/lib') # path to lucene-core-<version>.jar and lucene-misc-<version>.jar
    src, dest = get_index_path(ts1), get_index_path(ts2)

    # if there's "archive" dir in solr/data dir (created by hourglass), take subdirs as src or else solr/data/index
    get_archive_path = lambda t: os.path.join('solr_%s' % t, 'solr/data/archive')
    archive = get_archive_path(ts1)
    is_master = os.path.exists(os.path.join(EXAMPLE_PATH, archive))
    if is_master:
        subdirs = get_subdirs(archive)
        src = ' '.join([os.path.join(archive, subdir) for subdir in subdirs])
        if not src:
            log_info('nothing to be merged')
            return 1
    
    # if merge is successful, delete the source and restart the solr
    r = merge(src, dest, class_path=get_lib_path(ts1))
    if r.succeeded:
        log_info("successfully merged - now issuing " + "rm -rf %s" % src)
        local('rm -rf %s' % src)
        if not is_master:
            manage_solr('solr_' + ts1, 'restart', host='local')
        return manage_solr('solr_' + ts2, 'restart', host='local')

def make_upstart_script(path):
    script_name = os.path.basename(path)
    upstart_script = "/etc/init/%s.conf" % (script_name)
    # make an upstart script from the template solr.conf.sh, if it doesn't exist
    if not os.path.exists(upstart_script):
        java_home = os.path.join(EXAMPLE_PATH, path)
        if path.endswith(slices[0]):
            post_stop_script = post_stop_hg(path)
        else:
            post_stop_script = ''
        sudo('bash solr.conf.sh %s %s "%s" > %s' % (java_home, memory_to_solr(), post_stop_script, upstart_script))
    return script_name

def manage_solr(path, action='start', host=''):
    # path is like "solr_1h"
    if action not in ('start', 'stop', 'restart'):
        log_info("solr to be %sed ? - failing to do so." % action)
        return 1
    script_name = make_upstart_script(path)
    if host == 'local':
        local('sudo service %s %s' % (script_name, action))
    else:
        sudo('service %s %s' % (script_name, action))

def install_deps():
    sudo('apt-get install build-essential python-dev python-pip')
    sudo('pip install fabric')

def create_cron_jobs():
    def create_cron_line(ts):
        d = dict(min='0', hour='*', day='*', month='*', dow='*')
        fab = run('which fab')
        cmd = "%s -f %s/roll.py merge_slices:%s,%s" % (fab, EXAMPLE_PATH, ts, next_time_slice(ts))
        redirect_logs = ">> %s 2>&1" % LOG_FILE
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
        
        # add 1 hour lag for the merges so that they happen one after the other,
        # merge to the last slice being first.
        if d['hour'] == '0':
            d['hour'] = str(len(slices) - slices.index(ts))
        
        return ' '.join([d['min'], d['hour'], d['day'], d['month'], d['dow'], USER, cmd, redirect_logs])

    def get_last_slice_cron(ts):
        # returns content to be put in cron file which deletes old records every midnight
        java_home = os.path.join(EXAMPLE_PATH, 'solr_%s' % ts)
        redirect_logs = ">> %s 2>&1" % LOG_FILE
        d = dict(weeks=0, days=0, hours=0)
        number, period = int(ts[:-1]), ts[-1]
        if period == 'h':
            d['hours'] = number
        elif ts[-1] == 'd':
            d['days'] = number
        elif ts[-1] == 'w':
            d['weeks'] = number
        else:
            d['days'] = number*30
        # delete every saturday mid-night
        delete_script = os.path.join(EXAMPLE_PATH, 'delete.sh')
        cron_line = '0 0 * * 6 %s %s %s %s %s %s %s' % (USER, delete_script, java_home, d['hours'], d['days'], d['weeks'], redirect_logs)
        return cron_line
    
    for ts in slices[:-1]:
        sudo("echo '%s' > /etc/cron.d/solr_%s" % (set_tz() + create_cron_line(ts), ts))
    # run delete every mid night in the last slice
    last = slices[-1]
    sudo("echo '%s' > /etc/cron.d/solr_%s" % (set_tz() + get_last_slice_cron(last), last))

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

def upload_files(path, libs=False):
    # upload all the necessary files
    # apache-solr-3.5.0
    put('solr.conf.sh', 'solr.conf.sh')
    put('roll.py', 'roll.py')
    put('delete.sh', 'delete.sh')

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
    core_name = 'conversation_index' # default core name is "collection1"
    run('mkdir -p %s' % path)
    run('cp -R example/* %s' % path)
    run('perl -pi -e s/%(master_port)d/%(port)d/g %(path)s/etc/jetty.xml' % locals())
    run('perl -pi -e s/collection1/%(core_name)s/g %(path)s/solr/solr.xml' % locals())
    upload_files(path)
    manage_solr(path, action='start')
    # copy the zoie related libs to jetty's WEB-INF/lib to avoid IllegalAccessError
    # Jetty_blah_blah is created only while starting solr - so, copy these after solr has started.
    sudo('cp solr_%s/solr/lib/zoie-*.jar %s/work/Jetty_*_solr.war*/webapp/WEB-INF/lib/' % (slices[0], path))
    return manage_solr(path, action='restart')

@task
def make_rolling_index(*argv):
    global slices
    slices = get_timeslices(argv)
    with cd(EXAMPLE_PATH):
        #install_deps()
        make_solr_instance('solr_' + slices[0], MASTER_PORT)
        port = SLAVE_START_PORT
        for ts in slices[1:]:
            make_solr_instance('solr_' + ts, port)
            port += 1
        create_cron_jobs()
@task
def cleanup():
    solrs = [x for x in run('ls /etc/init').split() if x.startswith('solr_')]
    with cd(EXAMPLE_PATH):
        for sconf in solrs:
            s = sconf.replace('.conf', '')
            sudo('service %s stop' % s)
            sudo('rm -f /etc/init/%s' % sconf)
            sudo('rm -rf %s' % s)
            sudo('rm -f /etc/cron.d/%s' % s)
            sudo('rm -f /var/log/%s' % s)
        sudo('rm -f solrhg.log roll.py*')

if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        usage()
        abort(1)
    make_rolling_index(sys.argv[1:])
