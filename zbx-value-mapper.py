__author__ = 'aleksey.prilutskiy'

import re
import argparse
import sys
try:
    from zabbix_api import ZabbixAPI, ZabbixAPIException
except ImportError:
    sys.exit('Module zabbix_api is not installed. Please installed it with command "pip install zabbix_api"')

def error_parse(err):
        result = str(err.args[0])
        result = 'Error => ' + result[result.find('., ') + 3 : result.find('while') - 2 ]
        return result

def argument_parser():
    #Function for cli arguments parsing;
    arg_parser = argparse.ArgumentParser(description='Zabbix value map creation tool')
    sub_arg_parser = arg_parser.add_subparsers()
    arg_parser_list = sub_arg_parser.add_parser('list', help = 'List value maps to the console')
    arg_parser_list.add_argument('-m', '--mib-file', type=str, required=True, help='SNMP MIB file location')
    arg_parser_list.add_argument('-v', '--value', type=str, required=True, help='SNMP OID value to parse')
    arg_parser_list.set_defaults(func = map_list)
    arg_parser_create = sub_arg_parser.add_parser('create', help = 'Create value maps in Zabbix server')
    arg_parser_create.add_argument('-s', '--server', type=str, required=False, help='Zabbix server address/URL')
    arg_parser_create.add_argument('-u', '--user', type=str, required=False, help='Zabbix username for API access')
    arg_parser_create.add_argument('-p', '--password', type=str, required=False, help='Password for Zabbix user with API permitions')
    arg_parser_create.add_argument('-m', '--mib-file', type=str, required=True, help='SNMP MIB file location')
    arg_parser_create.add_argument('-v', '--value', type=str, required=True, help='SNMP OID value to parse')
    arg_parser_create.add_argument('-n', '--map-name', type=str, required=False, help='Value map name, use this key if value map set with "-v" key already exist')
    arg_parser_create.set_defaults(func = map_create)
    return arg_parser.parse_args()

def parse_mib(filename, value):
    #Function for MIB file parsing. It seeks for OID name and parses value maps from it;
    i = 0
    valmap = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                if re.search('^\s*' + value + '\s*::=', line):
                    i = 1
                if (i == 1):
                    val = re.search('^\s*(\S*)\((\d*)\)', line)
                    if val:
                        valmap.append({"value" : val.group(2), "newvalue" : val.group(1)})
                    if '}' in line:
                        i = 0
    except IOError:
        sys.exit('Error => File ' + filename + ' not found')
    if not valmap:
        sys.exit('Error => There is no OID with name ' + str(value) + ' in MIB file ' + str(filename))
    else:
        return valmap

def map_list(args):
    #Function outputs parced value maps to cli. It is called by list argument in cli;
    map_dict = parse_mib(args.mib_file, args.value)
    for vl in map_dict:
        print vl['value'] + ' => ' + vl['newvalue']
    return True

def map_create(args):
    #Function creates value maps in Zabbix server via API
    result = False
    value_map = parse_mib(args.mib_file, args.value)
    if args.map_name:
        name = args.map_name
    else:
        name = args.value
    value_map_rq = {
            "name": name,
            "mappings": value_map
    }
    zbx_srv = ZabbixAPI(server = args.server)
    try:
        zbx_srv.login(user = args.user, password = args.password)
        print "Zabbix API Version: %s" % zbx_srv.api_version()
        print "Logged in: %s" % str(zbx_srv.test_login())
    except ZabbixAPIException, e:
        sys.exit(error_parse(e))
    try:
        result = zbx_srv.valuemap.create(value_map_rq)
        if result:
            print 'Value map "' + name + '" created'
        else:
            print "Error => Something went wrong"
    except ZabbixAPIException, e:
        sys.exit(error_parse(e))
    return result

arguments = argument_parser()
arguments.func(arguments)