from pysnmp import hlapi


def get_sys_description(target: str, port: int = 161, community_string: str = 'tpc1n0c') -> None:
    """
    Prints (in json format) the sysDescription of target by performing a SNMP query

    Similar to SNMPWALK although this function only retrieves the sysDescriptions.
    Was made to be use for Velocloud. OID might be different for Silverpeak. Will have to find out later on.
    Written on: 2/5/2020
    Revised on:
    """
    sys_description = '1.3.6.1.2.1.1.1.0'
    try:
        response = snmp_get(target=target, oids=[sys_description], credentials=hlapi.CommunityData(community_string), port=port)
        d = {'SNMPv2-MIB::sysDescr.0': response[sys_description]}
        print(d)
    except RuntimeError:
        print("Timeout: No Response from {}".format(target))


"""
Code below was taken from quicksnmp.py found here: https://github.com/alessandromaggio/quicksnmp/blob/master/quicksnmp.py
"""


def snmp_construct_object_types(list_of_oids):
    object_types = []
    for oid in list_of_oids:
        object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
    return object_types


def snmp_construct_value_pairs(list_of_pairs):
    pairs = []
    for key, value in list_of_pairs.items():
        pairs.append(hlapi.ObjectType(hlapi.ObjectIdentity(key), value))
    return pairs


def snmp_get(target, oids, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *snmp_construct_object_types(oids)
    )
    return snmp_fetch(handler, 1)[0]


def snmp_set(target, value_pairs, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.setCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *snmp_construct_value_pairs(value_pairs)
    )
    return snmp_fetch(handler, 1)[0]


def snmp_get_bulk(target, oids, credentials, count, start_from=0, port=161,
                  engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.bulkCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        start_from, count,
        *snmp_construct_object_types(oids)
    )
    return snmp_fetch(handler, count)


def snmp_get_bulk_auto(target, oids, credentials, count_oid, start_from=0, port=161,
                       engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    count = snmp_get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return snmp_get_bulk(target, oids, credentials, count, start_from, port, engine, context)


def snmp_cast(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value)
            except (ValueError, TypeError):
                pass
    return value


def snmp_fetch(handler, count):
    result = []
    for i in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if not error_indication and not error_status:
                items = {}
                for var_bind in var_binds:
                    items[str(var_bind[0])] = snmp_cast(var_bind[1])
                result.append(items)
            else:
                raise RuntimeError('Got SNMP error: {0}'.format(error_indication))
        except StopIteration:
            break
    return result


# if __name__ == '__main__':
#     get_sys_description(target='216.241.61.9')
