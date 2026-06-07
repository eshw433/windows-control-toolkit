from __future__ import annotations

import ipaddress
import bisect
from dataclasses import dataclass


@dataclass(frozen=True)
class GeoEntry:
    cidr: str
    country: str
    asn: str = ""
    organization: str = ""


_BUILTIN_RANGES: list[tuple[str, str, str, str]] = [
    ("0.0.0.0/8", "ZZ", "RESERVED", "Reserved"),
    ("10.0.0.0/8", "ZZ", "PRIVATE", "RFC 1918"),
    ("100.64.0.0/10", "ZZ", "CGNAT", "Carrier-grade NAT"),
    ("127.0.0.0/8", "ZZ", "LOOPBACK", "Loopback"),
    ("169.254.0.0/16", "ZZ", "LINKLOCAL", "Link-local"),
    ("172.16.0.0/12", "ZZ", "PRIVATE", "RFC 1918"),
    ("192.168.0.0/16", "ZZ", "PRIVATE", "RFC 1918"),
    ("224.0.0.0/4", "ZZ", "MULTICAST", "Multicast"),
    ("240.0.0.0/4", "ZZ", "RESERVED", "Reserved"),
    ("255.255.255.255/32", "ZZ", "BROADCAST", "Broadcast"),

    ("1.0.0.0/24", "US", "AS13335", "Cloudflare"),
    ("1.1.1.0/24", "US", "AS13335", "Cloudflare DNS"),
    ("4.0.0.0/8", "US", "AS3356", "Level3"),
    ("8.8.4.0/24", "US", "AS15169", "Google DNS"),
    ("8.8.8.0/24", "US", "AS15169", "Google DNS"),
    ("9.0.0.0/8", "US", "AS3356", "IBM"),
    ("13.32.0.0/15", "US", "AS16509", "Amazon CloudFront"),
    ("13.64.0.0/11", "US", "AS8075", "Microsoft Azure"),
    ("13.107.0.0/16", "US", "AS8075", "Microsoft"),
    ("17.0.0.0/8", "US", "AS714", "Apple"),
    ("20.0.0.0/8", "US", "AS8075", "Microsoft Azure"),
    ("23.32.0.0/11", "US", "AS20940", "Akamai"),
    ("31.13.0.0/16", "US", "AS32934", "Facebook"),
    ("34.0.0.0/9", "US", "AS15169", "Google Cloud"),
    ("35.0.0.0/8", "US", "AS15169", "Google Cloud"),
    ("40.64.0.0/10", "US", "AS8075", "Microsoft"),
    ("44.224.0.0/11", "US", "AS16509", "Amazon AWS"),
    ("52.0.0.0/8", "US", "AS16509", "Amazon AWS"),
    ("54.0.0.0/8", "US", "AS16509", "Amazon AWS"),
    ("64.4.0.0/16", "US", "AS8075", "Microsoft"),
    ("65.52.0.0/14", "US", "AS8075", "Microsoft"),
    ("66.220.0.0/15", "US", "AS32934", "Facebook"),
    ("66.249.0.0/16", "US", "AS15169", "Google"),
    ("68.142.0.0/15", "US", "AS10310", "Yahoo"),
    ("69.171.224.0/19", "US", "AS32934", "Facebook"),
    ("69.63.176.0/20", "US", "AS32934", "Facebook"),
    ("72.14.192.0/18", "US", "AS15169", "Google"),
    ("74.125.0.0/16", "US", "AS15169", "Google"),
    ("96.6.0.0/15", "US", "AS20940", "Akamai"),
    ("98.137.0.0/16", "US", "AS10310", "Yahoo"),
    ("104.16.0.0/12", "US", "AS13335", "Cloudflare"),
    ("104.244.42.0/24", "US", "AS13414", "Twitter"),
    ("108.160.160.0/20", "US", "AS19679", "Dropbox"),
    ("108.174.0.0/19", "US", "AS14413", "LinkedIn"),
    ("131.107.0.0/16", "US", "AS8075", "Microsoft"),
    ("142.250.0.0/15", "US", "AS15169", "Google"),
    ("151.101.0.0/16", "US", "AS54113", "Fastly"),
    ("157.240.0.0/16", "US", "AS32934", "Facebook"),
    ("162.159.0.0/16", "US", "AS13335", "Cloudflare"),
    ("172.217.0.0/16", "US", "AS15169", "Google"),
    ("173.252.64.0/18", "US", "AS32934", "Facebook"),
    ("184.24.0.0/13", "US", "AS20940", "Akamai"),
    ("185.60.216.0/22", "US", "AS32934", "Facebook"),
    ("199.16.156.0/22", "US", "AS13414", "Twitter"),
    ("199.59.148.0/22", "US", "AS13414", "Twitter"),
    ("204.79.196.0/23", "US", "AS8068", "Microsoft Bing"),
    ("205.251.192.0/19", "US", "AS16509", "Amazon AWS"),
    ("216.58.192.0/19", "US", "AS15169", "Google"),
    ("23.235.32.0/20", "US", "AS54113", "Fastly"),

    ("46.0.0.0/8", "RU", "AS8359", "MTS / Various RU"),
    ("77.88.0.0/16", "RU", "AS13238", "Yandex"),
    ("87.250.224.0/19", "RU", "AS13238", "Yandex"),
    ("93.158.0.0/16", "RU", "AS13238", "Yandex"),
    ("95.108.0.0/16", "RU", "AS13238", "Yandex"),
    ("141.8.128.0/18", "RU", "AS13238", "Yandex"),
    ("178.154.0.0/16", "RU", "AS13238", "Yandex"),
    ("213.180.192.0/19", "RU", "AS13238", "Yandex"),
    ("217.69.128.0/19", "RU", "AS47764", "Mail.ru"),
    ("94.100.176.0/20", "RU", "AS47764", "Mail.ru"),

    ("45.0.0.0/8", "CN", "AS4134", "China Telecom"),
    ("58.0.0.0/8", "CN", "AS4837", "China Unicom"),
    ("60.0.0.0/8", "CN", "AS4837", "China Unicom"),
    ("101.0.0.0/8", "CN", "AS4134", "China Telecom"),
    ("123.0.0.0/8", "CN", "AS4134", "China Telecom"),

    ("78.0.0.0/8", "FR", "AS3215", "Orange / SFR"),
    ("80.0.0.0/8", "FR", "AS5511", "Orange"),
    ("90.0.0.0/8", "FR", "AS3215", "Orange"),
    ("92.0.0.0/8", "FR", "AS3215", "Orange"),

    ("79.0.0.0/8", "IT", "AS3269", "Telecom Italia"),

    ("82.0.0.0/8", "DE", "AS3320", "Deutsche Telekom"),
    ("85.0.0.0/8", "DE", "AS3320", "Deutsche Telekom"),
    ("88.0.0.0/8", "DE", "AS3320", "Deutsche Telekom"),
    ("91.0.0.0/8", "DE", "AS6724", "Strato"),
    ("212.0.0.0/8", "DE", "AS3320", "Deutsche Telekom"),

    ("83.0.0.0/8", "GB", "AS5378", "BT"),
    ("86.0.0.0/8", "GB", "AS5378", "BT"),
    ("89.0.0.0/8", "GB", "AS5378", "BT"),

    ("103.0.0.0/8", "IN", "AS9498", "Airtel"),
    ("106.0.0.0/8", "IN", "AS9498", "Airtel"),

    ("110.0.0.0/8", "JP", "AS2516", "KDDI"),
    ("126.0.0.0/8", "JP", "AS2914", "NTT"),

    ("119.0.0.0/8", "KR", "AS4766", "Korea Telecom"),
    ("175.0.0.0/8", "KR", "AS4766", "Korea Telecom"),

    ("177.0.0.0/8", "BR", "AS27699", "Telefonica BR"),
    ("179.0.0.0/8", "BR", "AS27699", "Telefonica BR"),
    ("189.0.0.0/8", "BR", "AS27699", "Telefonica BR"),

    ("190.0.0.0/8", "AR", "AS22927", "Telefonica AR"),
    ("191.0.0.0/8", "BR", "AS27699", "Telefonica BR"),

    ("197.0.0.0/8", "ZA", "AS2018", "TENET"),
    ("196.0.0.0/8", "EG", "AS8452", "TE Data"),

    ("200.0.0.0/8", "AR", "AS6471", "ENTEL"),
    ("201.0.0.0/8", "MX", "AS8151", "Uninet"),

    ("128.0.0.0/8", "US", "AS3320", "Various academic"),
    ("130.0.0.0/8", "US", "AS3320", "Various academic"),

    ("213.232.192.0/19", "AZ", "AS29049", "Azertelecom"),
    ("85.132.0.0/16", "AZ", "AS29049", "Azertelecom"),
    ("83.151.224.0/19", "AZ", "AS29049", "Azertelecom"),
    ("194.135.0.0/16", "AZ", "AS29049", "Azertelecom"),

    ("213.184.192.0/19", "BY", "AS6697", "Beltelecom"),

    ("78.108.0.0/16", "UA", "AS25229", "Volia"),
    ("213.156.0.0/16", "UA", "AS6849", "Ukrtelecom"),

    ("194.0.0.0/8", "EU", "AS3257", "Tinet / Various"),
    ("195.0.0.0/8", "EU", "AS6939", "Hurricane Electric"),
]


_COUNTRY_NAMES: dict[str, str] = {
    "ZZ": "Reserved/Local",
    "US": "United States",
    "RU": "Russia",
    "CN": "China",
    "FR": "France",
    "DE": "Germany",
    "GB": "United Kingdom",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "IE": "Ireland",
    "JP": "Japan",
    "KR": "Korea",
    "IN": "India",
    "BR": "Brazil",
    "AR": "Argentina",
    "MX": "Mexico",
    "EG": "Egypt",
    "ZA": "South Africa",
    "AZ": "Azerbaijan",
    "BY": "Belarus",
    "UA": "Ukraine",
    "EU": "Europe",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "TR": "Türkiye",
    "PL": "Poland",
    "CZ": "Czechia",
    "SE": "Sweden",
    "NO": "Norway",
    "FI": "Finland",
    "DK": "Denmark",
    "BE": "Belgium",
    "PT": "Portugal",
    "GR": "Greece",
    "AT": "Austria",
    "CH": "Switzerland",
    "IL": "Israel",
    "SA": "Saudi Arabia",
    "AE": "UAE",
    "VN": "Vietnam",
    "TH": "Thailand",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "SG": "Singapore",
    "HK": "Hong Kong",
    "TW": "Taiwan",
}


def _normalize(rows: list[tuple[str, str, str, str]]) -> list[tuple[int, int, str, str, str]]:
    result: list[tuple[int, int, str, str, str]] = []
    for cidr, country, asn, org in rows:
        try:
            net = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            continue
        if isinstance(net, ipaddress.IPv4Network):
            start = int(net.network_address)
            end = int(net.broadcast_address)
            result.append((start, end, country, asn, org))
    result.sort(key=lambda r: r[0])
    return result


_TABLE = _normalize(_BUILTIN_RANGES)
_TABLE_STARTS = [r[0] for r in _TABLE]


def lookup(ip: str) -> GeoEntry | None:
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if not isinstance(addr, ipaddress.IPv4Address):
        return None
    value = int(addr)
    idx = bisect.bisect_right(_TABLE_STARTS, value) - 1
    if idx < 0:
        return None
    start, end, country, asn, org = _TABLE[idx]
    if start <= value <= end:
        return GeoEntry(cidr=f"{ipaddress.IPv4Address(start)}-{ipaddress.IPv4Address(end)}",
                        country=country, asn=asn, organization=org)
    return None


def country_for(ip: str) -> str:
    entry = lookup(ip)
    return entry.country if entry else ""


def org_for(ip: str) -> str:
    entry = lookup(ip)
    return entry.organization if entry else ""


def asn_for(ip: str) -> str:
    entry = lookup(ip)
    return entry.asn if entry else ""


def country_name(code: str) -> str:
    return _COUNTRY_NAMES.get(code, code)


def is_local(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return addr.is_loopback or addr.is_private or addr.is_link_local or addr.is_multicast


def is_known_cloud(ip: str) -> bool:
    org = org_for(ip).lower()
    return any(k in org for k in (
        "amazon", "google", "microsoft", "cloudflare", "akamai", "fastly", "azure"
    ))


def is_known_social(ip: str) -> bool:
    org = org_for(ip).lower()
    return any(k in org for k in ("facebook", "twitter", "linkedin", "yahoo"))


def all_countries() -> list[str]:
    seen: set[str] = set()
    for _, _, country, _, _ in _TABLE:
        seen.add(country)
    return sorted(seen)


def flag_emoji(code: str) -> str:
    if len(code) != 2 or not code.isalpha():
        return ""
    return chr(0x1F1E6 + ord(code[0].upper()) - ord("A")) + \
           chr(0x1F1E6 + ord(code[1].upper()) - ord("A"))


def describe(ip: str) -> str:
    entry = lookup(ip)
    if not entry:
        return ""
    name = country_name(entry.country)
    if entry.organization:
        return f"{name} · {entry.organization}"
    return name
