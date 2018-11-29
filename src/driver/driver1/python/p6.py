from snmpinterface import get_snmp_interface_name, get_snmp_interface_name_by_index
from snmputil import walk_snmp_oid_value, snmp_get_multi_from_ip, \
    getsuboid, getfulloid, is_valid_snmp_result, snmp_walk_from_ip
from routingtableutil import get_snmp_alg, g_snmp_routing_type_invalid, \
    gettitle, get_empty_entry, g_col_alg, g_col_index, g_col_outif, g_col_destip,\
    g_col_destmask, g_col_nexthop, g_col_timestamp
from csvparser import toCSV
from function import getmaskaddressbylen,  get_maxmask_by_ip, bytes2str

dest_oid = "1.3.6.1.2.1.4.24.4.1.1"
mask_oid = "1.3.6.1.2.1.4.24.4.1.2"
routeifindex_oid = "1.3.6.1.2.1.4.24.4.1.5"
nexthop_oid = "1.3.6.1.2.1.4.24.4.1.4"
routetype_oid = "1.3.6.1.2.1.4.24.4.1.6"
routeprot_oid = "1.3.6.1.2.1.4.24.4.1.7"
time_stamp_oid = "1.3.6.1.2.1.4.24.4.1.8"


def get_valid_sub_oid(destip, minmask):
    maxmask = int(get_maxmask_by_ip(destip))
    return ['.'.join([destip, getmaskaddressbylen(i)]) for i in range(minmask, maxmask - 1, -1)]


def get_snmproutingtable(device, ip, vrfname, snmpinfo, nsid, max_entries):
    if (vrfname):
        return ""
    # get out interface
    aa = snmp_walk_from_ip(ip, snmpinfo, routeifindex_oid, nsid, max_entries)
    if(not is_valid_snmp_result(aa)):
        return ""
    ifnamedict = get_snmp_interface_name(device, 0, ip, snmpinfo, nsid)
    if not ifnamedict:
        return ""
    rtdict = {}
    # get dest and out interface
    for oid in aa:
        suboid = getsuboid(oid, routeifindex_oid)
        if(suboid):
            # set out interface
            entry = get_empty_entry()
            # if bytes decode
            aa[oid] = bytes2str(aa[oid])
            if aa[oid] in ifnamedict:
                entry[g_col_outif] = ifnamedict[aa[oid]]
            oid_to_col = {}
            # dest ip
            destipoid = getfulloid(dest_oid, suboid)
            oid_to_col[destipoid] = g_col_destip
            # dest mask
            destmaskoid = getfulloid(mask_oid, suboid)
            oid_to_col[destmaskoid] = g_col_destmask
            # next hop ip
            nexthopoid = getfulloid(nexthop_oid, suboid)
            oid_to_col[nexthopoid] = g_col_nexthop
            # route type
            routetypeoid = getfulloid(routetype_oid, suboid)
            oid_to_col[routetypeoid] = g_col_index
            # protocol
            routeprotooid = getfulloid(routeprot_oid, suboid)
            oid_to_col[routeprotooid] = g_col_alg
            # time stamp
            timestampoid = getfulloid(time_stamp_oid, suboid)
            oid_to_col[timestampoid] = g_col_timestamp
            snmpdict = snmp_get_multi_from_ip(ip, snmpinfo, list(oid_to_col.keys()), nsid)
            for key, col in oid_to_col.items():
                if (key in snmpdict):
                    entry[col] = snmpdict[key]
            rtdict[suboid] = entry
    # to csv
    ss = [gettitle(device)]
    for index, ip in enumerate(rtdict):
        vlist = rtdict[ip]
        vlist[g_col_alg] = get_snmp_alg(vlist[g_col_index], vlist[g_col_alg])
        vlist[g_col_index] = index
        ss.append(toCSV(vlist))
    return '\r\n'.join(ss)


def get_snmproutingentry(device, ip, vrfname, destip, snmpinfo, nsid):
    # destip is IP/mask format like x.x.x.x/x, IP/mask are changing during path calculate dynamic.
    # mask is only used by forwarding-MIB path
    if (vrfname):
        return ""
    iptmp = destip.split('/')
    temp, suboid = False, iptmp[0]
    minmask = 0 if suboid == "0.0.0.0" else int(iptmp[1])
    for item in get_valid_sub_oid(suboid, minmask):
        temp = walk_snmp_oid_value(
            ip, dest_oid, item, snmpinfo, nsid)
        if temp:
            snmp_destip, suboid = temp, item
            break
    if not temp:
        return ""
    snmp_mask = walk_snmp_oid_value(
        ip, mask_oid, suboid, snmpinfo, nsid)
    snmp_nexthop = walk_snmp_oid_value(
        ip, nexthop_oid, suboid, snmpinfo, nsid)
    snmp_outifindex = walk_snmp_oid_value(
        ip, routeifindex_oid, suboid, snmpinfo, nsid)
    intfindex = int(snmp_outifindex) if (snmp_outifindex.isdigit()) else 0
    # if out interface index is less 1 and next hop is empty
    if (intfindex < 0 and not snmp_nexthop):
        return ""
    # get interface name
    if (intfindex >= 0):
        snmp_outintf = get_snmp_interface_name_by_index(
            device, 0, ip, snmpinfo, nsid, intfindex)
    else:
        snmp_outintf = ""
    snmp_routetype = walk_snmp_oid_value(
        ip, routetype_oid, suboid, snmpinfo, nsid)
    # if type is invalid
    if snmp_routetype == g_snmp_routing_type_invalid:
        return ""
    snmp_routealg = walk_snmp_oid_value(
        ip, routeprot_oid, suboid, snmpinfo, nsid)
    snmp_routealg = get_snmp_alg(snmp_routetype, snmp_routealg)
    entry = get_empty_entry()
    entry[g_col_destip] = snmp_destip
    entry[g_col_destmask] = snmp_mask
    entry[g_col_nexthop] = snmp_nexthop
    entry[g_col_outif] = snmp_outintf
    entry[g_col_index] = 1
    entry[g_col_alg] = snmp_routealg
    return '\r\n'.join([gettitle(device), toCSV(entry)])
