from __future__ import annotations


_WELL_KNOWN_PORTS: dict[int, tuple[str, str]] = {
    20: ("ftp-data", "FTP data"),
    21: ("ftp", "FTP control"),
    22: ("ssh", "SSH"),
    23: ("telnet", "Telnet"),
    25: ("smtp", "SMTP"),
    53: ("dns", "DNS"),
    67: ("dhcp", "DHCP server"),
    68: ("dhcp", "DHCP client"),
    69: ("tftp", "TFTP"),
    80: ("http", "HTTP"),
    88: ("kerberos", "Kerberos"),
    110: ("pop3", "POP3"),
    111: ("rpcbind", "RPCBind"),
    119: ("nntp", "NNTP"),
    123: ("ntp", "NTP"),
    135: ("rpc", "MS RPC"),
    137: ("netbios", "NetBIOS name"),
    138: ("netbios", "NetBIOS datagram"),
    139: ("netbios", "NetBIOS session"),
    143: ("imap", "IMAP"),
    161: ("snmp", "SNMP"),
    162: ("snmptrap", "SNMP trap"),
    179: ("bgp", "BGP"),
    194: ("irc", "IRC"),
    220: ("imap3", "IMAP3"),
    389: ("ldap", "LDAP"),
    443: ("https", "HTTPS"),
    445: ("smb", "SMB"),
    465: ("smtps", "SMTPS"),
    500: ("isakmp", "IPsec"),
    514: ("syslog", "Syslog"),
    515: ("printer", "LPR/Printer"),
    520: ("rip", "RIP"),
    546: ("dhcpv6", "DHCPv6 client"),
    547: ("dhcpv6", "DHCPv6 server"),
    554: ("rtsp", "RTSP"),
    563: ("nntps", "NNTPS"),
    587: ("submission", "Mail submission"),
    593: ("rpc-http", "MS RPC over HTTP"),
    631: ("ipp", "Printing"),
    636: ("ldaps", "LDAPS"),
    993: ("imaps", "IMAPS"),
    995: ("pop3s", "POP3S"),
    1080: ("socks", "SOCKS"),
    1194: ("openvpn", "OpenVPN"),
    1234: ("vlc", "VLC stream"),
    1433: ("mssql", "Microsoft SQL"),
    1434: ("mssql", "Microsoft SQL Monitor"),
    1500: ("nfs-ha", "NFS HA"),
    1521: ("oracle", "Oracle DB"),
    1701: ("l2tp", "L2TP"),
    1723: ("pptp", "PPTP"),
    1812: ("radius", "RADIUS auth"),
    1813: ("radius", "RADIUS acct"),
    1883: ("mqtt", "MQTT"),
    1900: ("upnp", "UPnP/SSDP"),
    2049: ("nfs", "NFS"),
    2082: ("cpanel", "cPanel"),
    2083: ("cpanel-s", "cPanel SSL"),
    2181: ("zookeeper", "Zookeeper"),
    2375: ("docker", "Docker daemon"),
    2376: ("docker-s", "Docker TLS"),
    2483: ("oracle", "Oracle Net Listener"),
    2484: ("oracle-s", "Oracle Net SSL"),
    3000: ("dev", "Dev server"),
    3128: ("squid", "Squid proxy"),
    3306: ("mysql", "MySQL"),
    3389: ("rdp", "RDP"),
    3478: ("stun", "STUN/TURN"),
    3690: ("svn", "Subversion"),
    4000: ("dev", "Dev server"),
    4500: ("ipsec-nat", "IPsec NAT-T"),
    4567: ("custom", "Custom service"),
    4848: ("glassfish", "GlassFish admin"),
    5000: ("upnp/flask", "UPnP / Flask dev"),
    5060: ("sip", "SIP"),
    5061: ("sips", "SIPS"),
    5222: ("xmpp-c", "XMPP client"),
    5269: ("xmpp-s", "XMPP server"),
    5353: ("mdns", "mDNS"),
    5432: ("postgres", "PostgreSQL"),
    5500: ("vnc", "VNC server"),
    5601: ("kibana", "Kibana"),
    5672: ("amqp", "AMQP / RabbitMQ"),
    5900: ("vnc", "VNC"),
    5984: ("couchdb", "CouchDB"),
    6379: ("redis", "Redis"),
    6443: ("k8s-api", "Kubernetes API"),
    6660: ("irc", "IRC"),
    6661: ("irc", "IRC"),
    6667: ("irc", "IRC"),
    6881: ("torrent", "BitTorrent"),
    6969: ("torrent", "BitTorrent tracker"),
    7000: ("cassandra", "Cassandra"),
    7077: ("spark", "Spark master"),
    8000: ("http-alt", "HTTP alt"),
    8001: ("http-alt", "HTTP alt"),
    8008: ("http-alt", "HTTP alt"),
    8009: ("ajp", "AJP"),
    8080: ("http-proxy", "HTTP proxy / web"),
    8081: ("http-alt", "HTTP alt"),
    8088: ("http-alt", "HTTP alt"),
    8089: ("splunk", "Splunk mgmt"),
    8090: ("http-alt", "HTTP alt"),
    8161: ("activemq", "ActiveMQ"),
    8200: ("vault", "Vault"),
    8443: ("https-alt", "HTTPS alt"),
    8500: ("consul", "Consul"),
    8530: ("wsus", "WSUS HTTP"),
    8531: ("wsus", "WSUS HTTPS"),
    8800: ("dev", "Dev server"),
    8888: ("http-alt", "HTTP alt"),
    9000: ("php-fpm", "PHP-FPM / SonarQube"),
    9001: ("portainer", "Portainer / tor"),
    9042: ("cassandra", "Cassandra CQL"),
    9090: ("prometheus", "Prometheus"),
    9092: ("kafka", "Kafka"),
    9100: ("printer-direct", "Printer (JetDirect)"),
    9200: ("elasticsearch", "Elasticsearch"),
    9300: ("elasticsearch", "Elasticsearch cluster"),
    9418: ("git", "Git daemon"),
    9999: ("dev", "Dev server"),
    10000: ("webmin", "Webmin"),
    11211: ("memcache", "Memcached"),
    12345: ("netbus", "NetBus (legacy)"),
    13720: ("nbu", "NetBackup"),
    13721: ("nbu", "NetBackup"),
    15672: ("rabbitmq-ui", "RabbitMQ management"),
    16080: ("http-alt", "HTTP alt"),
    19132: ("minecraft-be", "Minecraft Bedrock"),
    19133: ("minecraft-be", "Minecraft Bedrock"),
    19999: ("netdata", "Netdata"),
    20000: ("dnp3", "DNP3"),
    25565: ("minecraft", "Minecraft"),
    27015: ("steam", "Steam game"),
    27016: ("steam", "Steam game"),
    27017: ("mongodb", "MongoDB"),
    27018: ("mongodb-shard", "MongoDB shard"),
    27019: ("mongodb-config", "MongoDB config"),
    28015: ("rethinkdb", "RethinkDB"),
    28017: ("mongodb-web", "MongoDB web"),
    29292: ("dev", "Dev server"),
    32400: ("plex", "Plex"),
    32768: ("ephemeral", "Ephemeral"),
    33848: ("jenkins", "Jenkins"),
    35357: ("openstack", "Keystone admin"),
    37777: ("dahua", "Dahua DVR"),
    44818: ("ethernet/ip", "EtherNet/IP"),
    47808: ("bacnet", "BACnet"),
    50000: ("sap", "SAP"),
    51820: ("wireguard", "WireGuard"),
    54321: ("dev", "Dev server"),
    55443: ("yeelight", "Yeelight"),
    61613: ("stomp", "STOMP / ActiveMQ"),
    62078: ("apple-itunes", "Apple sync"),
}


_DYNAMIC_RANGES: list[tuple[int, int, str]] = [
    (32768, 60999, "ephemeral"),
    (49152, 65535, "ephemeral"),
    (5060, 5061, "sip"),
    (1024, 5000, "dynamic"),
]


def lookup(port: int) -> tuple[str, str]:
    if port in _WELL_KNOWN_PORTS:
        return _WELL_KNOWN_PORTS[port]
    for start, end, label in _DYNAMIC_RANGES:
        if start <= port <= end:
            return (label, f"{label} ({port})")
    return ("", "")


def short_label(port: int) -> str:
    s, _ = lookup(port)
    return s or str(port)


def long_label(port: int) -> str:
    s, name = lookup(port)
    if not s:
        return str(port)
    return f"{port} · {name}"


def known_ports() -> list[int]:
    return list(_WELL_KNOWN_PORTS.keys())


def is_privileged(port: int) -> bool:
    return 0 < port < 1024


def is_high_risk_listener(port: int) -> bool:
    return port in {23, 135, 139, 445, 1433, 1434, 3389, 5900, 6379, 9200, 11211,
                    27017, 27018, 27019}


def categorize(port: int) -> str:
    if port in {80, 443, 8080, 8443, 8000}:
        return "web"
    if port in {25, 465, 587, 110, 143, 993, 995}:
        return "mail"
    if port in {3306, 5432, 1433, 1521, 27017, 27018, 27019, 6379, 9042, 9200}:
        return "database"
    if port in {21, 22, 23, 3389, 5900}:
        return "remote"
    if port in {53, 67, 68, 123, 161, 162}:
        return "infra"
    if port in {1900, 5353, 5000}:
        return "discovery"
    if port in {6881, 6969, 51413}:
        return "p2p"
    if port == 0:
        return "any"
    return "other"
