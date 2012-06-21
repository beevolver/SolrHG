# solr instances will be created in parent directory of EXAMPLE_PATH and hence should be owned by USER
EXAMPLE_PATH = '/solr/apache-solr-3.5.0'
INDEXDIR = 'solr/data/index/'
MASTER_PORT = 8983
SLAVE_START_PORT = 9000
LOG_FILE = "%s/solrhg.log" % EXAMPLE_PATH
USER = 'beeadmin'
