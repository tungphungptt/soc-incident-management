import random, hashlib, datetime as dt, unicodedata, collections, math

R = random.Random(20261021)
NOW = dt.datetime(2026, 10, 21, 12, 0, 0)
def M(m): return dt.timedelta(minutes=m)
def fmt(d): return d.strftime('%Y-%m-%d %H:%M:%S')
def q(s):
    assert '\\' not in s
    return "'" + str(s).replace("'", "''") + "'"
def wchoice(pop, w): return R.choices(pop, weights=w, k=1)[0]
def wsample(pop, w, k):
    pop, w, out = list(pop), list(w), []
    k = min(k, len(pop))
    for _ in range(k):
        i = R.choices(range(len(pop)), weights=w, k=1)[0]
        out.append(pop.pop(i)); w.pop(i)
    return out
def adjust(counts, target, lo, his):
    guard = 0
    while sum(counts) < target and guard < 100000:
        guard += 1; i = R.randrange(len(counts))
        if counts[i] < his[i]: counts[i] += 1
    while sum(counts) > target and guard < 200000:
        guard += 1; i = R.randrange(len(counts))
        if counts[i] > lo: counts[i] -= 1
    return counts
def ascii_(s):
    s = s.replace('đ', 'd').replace('Đ', 'D')
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower().replace(' ', '')

SEV = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
SLA_MIN = {'CRITICAL': 60, 'HIGH': 240, 'MEDIUM': 720, 'LOW': 1440}

# ------------------------------------------------------------------ ORGS
ORG_DEF = [
 ('Ngân hàng Thương mại Việt Thịnh Phát', 'Hà Nội', 'Ngân hàng - Tài chính', 4200, 'CRITICAL', 10),
 ('Bệnh viện Đa khoa Hòa Bình Xanh', 'Đà Nẵng', 'Y tế', 3100, 'CRITICAL', 9),
 ('Công ty Viễn thông Sao Việt Net', 'TP. Hồ Chí Minh', 'Viễn thông', 8500, 'CRITICAL', 9),
 ('Cổng Dịch vụ công Thành phố Bình An', 'Hải Phòng', 'Cơ quan dịch vụ công', 1800, 'CRITICAL', 8),
 ('Công ty Tài chính Tín Lộc', 'TP. Hồ Chí Minh', 'Ngân hàng - Tài chính', 950, 'HIGH', 7),
 ('Sàn thương mại điện tử Chợ Số', 'Hà Nội', 'Thương mại điện tử', 1200, 'HIGH', 7),
 ('Công ty Công nghệ Thông tin Nam Dương', 'Đà Nẵng', 'Công nghệ thông tin', 650, 'HIGH', 6),
 ('Công ty Logistics Hải Vân Express', 'Hải Phòng', 'Logistics', 2400, 'HIGH', 6),
 ('Bệnh viện Nhi đồng Ánh Dương', 'Cần Thơ', 'Y tế', 1500, 'HIGH', 6),
 ('Công ty Điện tử Sản xuất Kim Long', 'Bình Dương', 'Sản xuất', 5200, 'HIGH', 5),
 ('Đại học Kỹ thuật Phương Nam', 'Cần Thơ', 'Giáo dục', 2100, 'MEDIUM', 5),
 ('Chuỗi bán lẻ Siêu thị Tâm An', 'TP. Hồ Chí Minh', 'Bán lẻ', 3600, 'MEDIUM', 5),
 ('Công ty Cơ khí Chế tạo Đại Phong', 'Đồng Nai', 'Sản xuất', 1800, 'MEDIUM', 5),
 ('Công ty Vận tải Biển Đông Á', 'Hải Phòng', 'Logistics', 780, 'MEDIUM', 4),
 ('Học viện Đào tạo Nghề Tân Tiến', 'Huế', 'Giáo dục', 420, 'MEDIUM', 4),
 ('Công ty Phần mềm Mây Xanh', 'Hà Nội', 'Công nghệ thông tin', 310, 'MEDIUM', 4),
 ('Cửa hàng Điện máy Phúc Lộc', 'Nghệ An', 'Bán lẻ', 140, 'LOW', 5),
 ('Trường THPT Chuyên Hồng Lĩnh', 'Hà Tĩnh', 'Giáo dục', 180, 'LOW', 5),
 ('Phòng khám Đa khoa An Tâm', 'Quảng Ngãi', 'Y tế', 95, 'LOW', 5),
 ('Công ty Giao nhận Gió Đông', 'Quảng Ninh', 'Logistics', 120, 'LOW', 5),
]
ORG_ORDER = list(range(20)); R.shuffle(ORG_ORDER)  # shuffle IDs so importance is not sorted by ID
orgs = []
for newidx, oi in enumerate(ORG_ORDER):
    n, city, sector, nv, imp, na = ORG_DEF[oi]
    orgs.append(dict(id='TC%03d' % (newidx + 1), idx=newidx + 1, name=n,
                     addr='%d Đường %s, %s' % (R.randint(10, 199), R.choice(['Lê Lợi', 'Trần Phú', 'Nguyễn Huệ', 'Hoàng Diệu', 'Lý Thường Kiệt', 'Phan Chu Trinh']), city),
                     sector=sector, nv=nv, imp=imp, na=na))
ORG = {o['id']: o for o in orgs}

# ------------------------------------------------------------------ EMPLOYEES
HO = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Ngô']
NAMES = [('Nguyễn Minh Quân', 1), ('Trần Thu Hà', 1)]
ROLE_PLAN = (['SOC Manager'] * 2 + ['SOC Analyst L3'] * 3 + ['SOC Analyst L2'] * 9 +
             ['Incident Responder'] * 4 + ['Threat Hunter'] * 3 + ['SOC Analyst L1'] * 9)
FULLNAMES = [
 'Nguyễn Minh Quân', 'Trần Thu Hà', 'Lê Hoàng Nam', 'Phạm Quỳnh Anh', 'Vũ Đức Thịnh',
 'Đặng Thanh Tùng', 'Bùi Ngọc Lan', 'Hoàng Gia Bảo', 'Ngô Phương Thảo', 'Đỗ Văn Khánh',
 'Trần Quốc Huy', 'Lê Thị Mai', 'Phạm Anh Dũng', 'Nguyễn Hải Yến', 'Vũ Tuấn Kiệt',
 'Bùi Minh Châu', 'Đặng Khánh Linh', 'Hoàng Việt Anh', 'Ngô Thanh Sơn', 'Đỗ Thùy Dương',
 'Lê Quang Vinh', 'Trần Bảo Ngọc', 'Phạm Đình Phúc', 'Nguyễn Thị Hồng', 'Vũ Hoàng Long',
 'Bùi Anh Thư', 'Đặng Trọng Nghĩa', 'Hoàng Mai Phương', 'Ngô Công Minh', 'Đỗ Hải Đăng']
EXPR = {'SOC Manager': (10, 16), 'SOC Analyst L3': (7, 12), 'SOC Analyst L2': (3, 6),
        'Incident Responder': (4, 9), 'Threat Hunter': (5, 10), 'SOC Analyst L1': (1, 3)}
emps = []
for i, (nm, role) in enumerate(zip(FULLNAMES, ROLE_PLAN)):
    exp = R.randint(*EXPR[role]); age = 22 + exp + R.randint(0, 5)
    parts = nm.split(); ten, ho = ascii_(parts[-1]), ascii_(parts[0])
    emps.append(dict(id='NV%03d' % (i + 1), cmt='DEMO-ID-%08d' % (i + 1), name=nm,
                     dob=dt.date(2026 - age, R.randint(1, 12), R.randint(1, 28)),
                     phone='09%d%07d' % (R.choice([0, 1, 3, 4, 6, 7, 8]), R.randint(1000000, 9999999)),
                     email='%s.%s%02d@soc-demo.example' % (ten, ho, i + 1), exp=exp, role=role))
E = {e['id']: e for e in emps}
OVERLOADED = ['NV006', 'NV007', 'NV015']
assert [E[x]['role'] for x in OVERLOADED] == ['SOC Analyst L2', 'SOC Analyst L2', 'Incident Responder']
ALT = {'SOC Analyst L2': ['Incident Responder'], 'SOC Analyst L3': ['Incident Responder', 'Threat Hunter']}
POS = {'SOC Analyst L1': 'Triage Analyst', 'SOC Analyst L2': 'Investigation Analyst', 'SOC Analyst L3': 'Senior Investigator',
       'Incident Responder': 'Containment Responder', 'Threat Hunter': 'Threat Hunting Support', 'SOC Manager': 'Escalation Manager'}

# ------------------------------------------------------------------ ASSETS
TYPES = ['Server', 'Workstation', 'Firewall', 'Router', 'Database', 'Web Server', 'Cloud Service']
PRE = dict(zip(TYPES, ['SRV', 'WS', 'FW', 'RTR', 'DB', 'WEB', 'CLD']))
ROLEN = {'Server': ['Máy chủ ứng dụng', 'Máy chủ tệp', 'Máy chủ AD', 'Máy chủ sao lưu'],
         'Workstation': ['Máy trạm kế toán', 'Máy trạm quản trị', 'Máy trạm nhân sự', 'Máy trạm phòng IT'],
         'Firewall': ['Tường lửa biên', 'Tường lửa nội bộ'], 'Router': ['Router WAN', 'Router chi nhánh'],
         'Database': ['CSDL khách hàng', 'CSDL giao dịch', 'CSDL nhân sự'],
         'Web Server': ['Cổng web công khai', 'Web portal nội bộ', 'API Gateway'],
         'Cloud Service': ['Dịch vụ lưu trữ đám mây', 'Máy ảo đám mây', 'Kho dữ liệu đám mây']}
OSN = {'Server': ['Ubuntu Server 22.04 LTS', 'Windows Server 2022', 'Red Hat Enterprise Linux 9'],
       'Workstation': ['Windows 11 Pro', 'Windows 10 Enterprise', 'Ubuntu Desktop 22.04'],
       'Firewall': ['FortiOS 7.4', 'PAN-OS 11.1'], 'Router': ['Cisco IOS XE 17.9', 'JunOS 23.2'],
       'Database': ['Ubuntu Server 22.04 LTS', 'Windows Server 2019', 'Red Hat Enterprise Linux 9'],
       'Web Server': ['Ubuntu Server 22.04 LTS', 'Debian 12', 'Windows Server 2022'],
       'Cloud Service': ['Cloud-managed (Linux)', 'Cloud-managed (Windows)']}
LOC = {'Server': ['Data Center - Rack A%02d', 'Data Center - Rack B%02d'], 'Database': ['Data Center - Rack C%02d'],
       'Workstation': ['Văn phòng tầng %d'], 'Firewall': ['Phòng mạng - Tủ rack %02d'], 'Router': ['Phòng mạng - Tủ rack %02d'],
       'Web Server': ['DMZ - Rack D%02d'], 'Cloud Service': ['Cloud - Region Singapore', 'Cloud - Region Hồng Kông']}
TW = {'Server': 3, 'Workstation': 3, 'Firewall': 1.2, 'Router': 1, 'Database': 1.6, 'Web Server': 1.6, 'Cloud Service': 1.2}
LEVEL = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
BASEIMP = {'Database': 2.6, 'Firewall': 2, 'Server': 1.8, 'Web Server': 1.8, 'Cloud Service': 1.6, 'Router': 1.2, 'Workstation': 0.6}
assets = []; counters = collections.Counter(); cloud_n = [10]
for o in orgs:
    for k in range(o['na']):
        t = wchoice(TYPES, [TW[x] for x in TYPES])
        assets.append(dict(org=o['id'], type=t))
# hot assets (open-only, many alerts): first asset of 3 first CRITICAL orgs -> Database
crit_orgs = [o['id'] for o in orgs if o['imp'] == 'CRITICAL']
hot_idx = []
for oid in crit_orgs[:3]:
    i = next(j for j, a in enumerate(assets) if a['org'] == oid); assets[i]['type'] = 'Database'; hot_idx.append(i)
for t in TYPES:  # guarantee each type exists
    if not any(a['type'] == t for a in assets):
        j = R.choice([j for j, a in enumerate(assets) if j not in hot_idx]); assets[j]['type'] = t
for j, a in enumerate(assets):
    o = ORG[a['org']]; t = a['type']; counters[(o['id'], t)] += 1; n = counters[(o['id'], t)]
    a['id'] = 'TS%03d' % (j + 1)
    code = '%s-%s-%02d' % (PRE[t], o['id'], n)
    a['name'] = '%s %s' % (R.choice(ROLEN[t]), code)
    if t == 'Server': ip = '10.%d.10.%d' % (o['idx'] + 10, 10 + n)
    elif t == 'Workstation': ip = '10.%d.20.%d' % (o['idx'] + 10, 10 + n)
    elif t == 'Database': ip = '10.%d.30.%d' % (o['idx'] + 10, 10 + n)
    elif t == 'Firewall': ip = '10.%d.0.%d' % (o['idx'] + 10, 1 + n)
    elif t == 'Router': ip = '10.%d.0.%d' % (o['idx'] + 10, 200 + n)
    elif t == 'Web Server': ip = '172.16.%d.%d' % (o['idx'], 10 + n)
    else: ip = '192.0.2.%d' % cloud_n[0]; cloud_n[0] += 1
    a['ip'] = ip; a['os'] = R.choice(OSN[t])
    pat = R.choice(LOC[t]); a['loc'] = pat % R.randint(1, 12) if '%' in pat else pat
    lv = BASEIMP[t] + {'CRITICAL': 0.9, 'HIGH': 0.4, 'MEDIUM': 0, 'LOW': -0.6}[o['imp']] + R.uniform(-0.5, 0.5)
    a['imp'] = LEVEL[max(0, min(3, int(round(lv))))]
    if j in hot_idx: a['imp'] = 'CRITICAL'
assert len({a['ip'] for a in assets}) == 120 and len({a['name'] for a in assets}) == 120
A = {a['id']: a for a in assets}
HOT = {assets[i]['id'] for i in hot_idx}
asset_by_org = collections.defaultdict(list)
for a in assets: asset_by_org[a['org']].append(a['id'])
aw = {}
for oid, lst in asset_by_org.items():
    order = lst[:]; R.shuffle(order)
    for h in [x for x in order if x in HOT]: order.remove(h); order.insert(0, h)
    for r, aid in enumerate(order): aw[aid] = 1 / ((r + 1) ** 0.9)

# ------------------------------------------------------------------ MITRE
MITRE = [
 ('T1110', 'Brute Force', 'Credential Access', 'Đối thủ thử nhiều mật khẩu hoặc khóa để giành quyền truy cập tài khoản.'),
 ('T1059', 'Command and Scripting Interpreter', 'Execution', 'Lạm dụng trình thông dịch lệnh và script như PowerShell, cmd hoặc bash để thực thi mã.'),
 ('T1003', 'OS Credential Dumping', 'Credential Access', 'Trích xuất thông tin xác thực từ hệ điều hành như LSASS hoặc SAM.'),
 ('T1021', 'Remote Services', 'Lateral Movement', 'Dùng dịch vụ từ xa như RDP, SSH, SMB với tài khoản hợp lệ để di chuyển ngang.'),
 ('T1071', 'Application Layer Protocol', 'Command and Control', 'Giao tiếp C2 qua giao thức tầng ứng dụng như HTTP, HTTPS, DNS để hòa lẫn vào lưu lượng thường.'),
 ('T1053', 'Scheduled Task/Job', 'Execution', 'Lạm dụng tác vụ định kỳ để thực thi mã hoặc duy trì hiện diện.'),
 ('T1562', 'Impair Defenses', 'Defense Evasion', 'Vô hiệu hóa hoặc làm suy yếu công cụ phòng thủ và ghi log.'),
 ('T1105', 'Ingress Tool Transfer', 'Command and Control', 'Tải công cụ hoặc tệp độc hại từ bên ngoài vào hệ thống nạn nhân.'),
 ('T1566', 'Phishing', 'Initial Access', 'Gửi thư hoặc tin nhắn lừa đảo để chiếm quyền truy cập ban đầu.'),
 ('T1190', 'Exploit Public-Facing Application', 'Initial Access', 'Khai thác lỗ hổng của ứng dụng hướng ra Internet.'),
 ('T1078', 'Valid Accounts', 'Defense Evasion', 'Sử dụng tài khoản hợp lệ bị đánh cắp để truy cập và né tránh phát hiện.'),
 ('T1046', 'Network Service Discovery', 'Discovery', 'Quét tìm dịch vụ đang chạy trên các máy từ xa trong mạng.'),
 ('T1055', 'Process Injection', 'Defense Evasion', 'Chèn mã vào tiến trình đang chạy để né tránh phòng thủ hoặc nâng quyền.'),
 ('T1486', 'Data Encrypted for Impact', 'Impact', 'Mã hóa dữ liệu của nạn nhân để gián đoạn hoạt động, thường gặp ở ransomware.'),
 ('T1041', 'Exfiltration Over C2 Channel', 'Exfiltration', 'Đánh cắp dữ liệu qua chính kênh chỉ huy và điều khiển.'),
 ('T1048', 'Exfiltration Over Alternative Protocol', 'Exfiltration', 'Đánh cắp dữ liệu qua giao thức khác với kênh C2 chính.'),
 ('T1027', 'Obfuscated Files or Information', 'Defense Evasion', 'Làm rối tệp hoặc thông tin để gây khó khăn cho phát hiện và phân tích.'),
 ('T1547', 'Boot or Logon Autostart Execution', 'Persistence', 'Cấu hình hệ thống để mã tự chạy khi khởi động hoặc đăng nhập.'),
 ('T1068', 'Exploitation for Privilege Escalation', 'Privilege Escalation', 'Khai thác lỗ hổng phần mềm để nâng quyền.'),
 ('T1082', 'System Information Discovery', 'Discovery', 'Thu thập thông tin chi tiết về hệ điều hành và phần cứng.'),
 ('T1018', 'Remote System Discovery', 'Discovery', 'Liệt kê các hệ thống khác trong mạng để chuẩn bị di chuyển ngang.'),
 ('T1136', 'Create Account', 'Persistence', 'Tạo tài khoản mới để duy trì quyền truy cập.'),
 ('T1204', 'User Execution', 'Execution', 'Dựa vào việc người dùng mở tệp hoặc liên kết độc hại để thực thi mã.'),
 ('T1567', 'Exfiltration Over Web Service', 'Exfiltration', 'Đánh cắp dữ liệu qua dịch vụ web hợp pháp như lưu trữ đám mây.'),
 ('T1595', 'Active Scanning', 'Reconnaissance', 'Quét chủ động hạ tầng của nạn nhân để thu thập thông tin trinh sát.'),
]
assert len(MITRE) == 25 and len({m[0] for m in MITRE}) == 25

# ------------------------------------------------------------------ SCENARIOS
SC = {
 'brute': dict(w=16, alerts=['Brute Force', 'Credential Access', 'Privilege Escalation'], mitre=['T1110', 'T1078', 'T1003'],
               ioc=['IP'], acts=['Block IP', 'Reset Password', 'Disable Account', 'Collect Evidence'],
               desc='Chuỗi đăng nhập thất bại hàng loạt dẫn tới nghi ngờ tài khoản bị chiếm quyền'),
 'powershell': dict(w=16, alerts=['Suspicious PowerShell', 'Malware Detection', 'Credential Access'], mitre=['T1059', 'T1027', 'T1105', 'T1204', 'T1055'],
               ioc=['Hash', 'URL', 'Domain'], acts=['Kill Process', 'Isolate Host', 'Scan Malware', 'Collect Evidence'],
               desc='PowerShell bị làm rối chạy bất thường và tải thành phần độc hại'),
 'ransom': dict(w=11, alerts=['Malware Detection', 'Privilege Escalation', 'Suspicious PowerShell'], mitre=['T1486', 'T1562', 'T1055', 'T1021', 'T1547'],
               ioc=['Hash', 'IP', 'Domain'], acts=['Isolate Host', 'Kill Process', 'Scan Malware', 'Collect Evidence', 'Block IP'],
               desc='Dấu hiệu ransomware mã hóa tệp và vô hiệu hóa công cụ bảo vệ'),
 'web': dict(w=16, alerts=['Port Scanning', 'Web Attack', 'Privilege Escalation'], mitre=['T1595', 'T1046', 'T1190', 'T1068', 'T1082'],
               ioc=['IP', 'URL'], acts=['Block IP', 'Collect Evidence', 'Scan Malware'],
               desc='Quét cổng rồi tấn công ứng dụng web hướng ra Internet'),
 'exfil': dict(w=14, alerts=['Suspicious Outbound Traffic', 'Credential Access'], mitre=['T1041', 'T1048', 'T1567', 'T1071', 'T1105'],
               ioc=['Domain', 'IP', 'URL'], acts=['Block IP', 'Isolate Host', 'Collect Evidence'],
               desc='Lưu lượng ra ngoài bất thường nghi ngờ rò rỉ dữ liệu'),
 'phish': dict(w=15, alerts=['Malware Detection', 'Suspicious PowerShell', 'Credential Access', 'Suspicious Outbound Traffic'], mitre=['T1566', 'T1204', 'T1078', 'T1136', 'T1059'],
               ioc=['Email', 'URL', 'Domain', 'Hash'], acts=['Reset Password', 'Disable Account', 'Scan Malware', 'Collect Evidence'],
               desc='Chiến dịch lừa đảo qua thư điện tử dẫn tới lộ thông tin xác thực'),
 'lateral': dict(w=12, alerts=['Privilege Escalation', 'Credential Access', 'Port Scanning', 'Suspicious Outbound Traffic'], mitre=['T1053', 'T1021', 'T1018', 'T1003', 'T1136', 'T1547', 'T1082'],
               ioc=['IP', 'Hash'], acts=['Disable Account', 'Isolate Host', 'Kill Process', 'Collect Evidence', 'Reset Password'],
               desc='Nâng quyền và di chuyển ngang giữa các máy trong mạng nội bộ'),
}
SRC = {'Brute Force': ['Wazuh', 'Firewall', 'SIEM correlation rule', 'Microsoft Defender'],
       'Suspicious PowerShell': ['Microsoft Defender', 'EDR', 'Wazuh'],
       'Malware Detection': ['EDR', 'Microsoft Defender', 'Wazuh'],
       'Port Scanning': ['Suricata', 'Zeek', 'Firewall', 'IDS/IPS'],
       'Privilege Escalation': ['Wazuh', 'EDR', 'SIEM correlation rule'],
       'Suspicious Outbound Traffic': ['Zeek', 'Suricata', 'Firewall', 'SIEM correlation rule'],
       'Credential Access': ['EDR', 'Microsoft Defender', 'SIEM correlation rule'],
       'Web Attack': ['Suricata', 'IDS/IPS', 'Firewall']}
INBOUND = {'Brute Force', 'Port Scanning', 'Web Attack', 'Credential Access'}

# ------------------------------------------------------------------ INCIDENT SPECS
# (sev, status, P offset from NOW in minutes, X off, C off, Rm off)
SPECIAL = [
 ('CRITICAL', 'NEW', 25, None, None, None), ('CRITICAL', 'NEW', 40, None, None, None),
 ('CRITICAL', 'NEW', 130, None, None, None), ('CRITICAL', 'NEW', 300, None, None, None),
 ('CRITICAL', 'NEW', 4320, None, None, None),
 ('CRITICAL', 'INVESTIGATING', 40, 10, None, None), ('LOW', 'INVESTIGATING', 300, 20, None, None),
 ('MEDIUM', 'INVESTIGATING', 360, 30, None, None), ('HIGH', 'CONTAINED', 150, 10, 60, None),
 ('MEDIUM', 'REMEDIATING', 540, 15, 120, 300), ('LOW', 'CONTAINED', 1200, 30, 240, None)]
sev_left = collections.Counter({'CRITICAL': 22, 'HIGH': 40, 'MEDIUM': 52, 'LOW': 36})
for s in SPECIAL: sev_left[s[0]] -= 1
st_left = collections.Counter({'CLOSED': 90, 'NEW': 14, 'INVESTIGATING': 17, 'CONTAINED': 15, 'REMEDIATING': 14})
for s in SPECIAL: st_left[s[1]] -= 1
assert sum(sev_left.values()) == sum(st_left.values()) == 139
sevpool = [s for s in SEV for _ in range(sev_left[s])]; R.shuffle(sevpool)
specs = []
newslots = st_left['NEW']
noncrit = [s for s in sevpool if s != 'CRITICAL']
chosen_new = noncrit[:newslots]
for s in chosen_new: sevpool.remove(s)
for s in chosen_new: specs.append(dict(sev=s, status='NEW', special=False))
rest_status = [st for st in st_left for _ in range(st_left[st]) if st != 'NEW']
R.shuffle(rest_status)
for sv, st in zip(sevpool, rest_status): specs.append(dict(sev=sv, status=st, special=False))
for i, s in enumerate(SPECIAL):
    specs.append(dict(sev=s[0], status=s[1], special=True, sp=s, spi=i))
assert len(specs) == 150

def clock(day):  # business-weighted time of day
    h = wchoice(list(range(24)), [2, 1, 1, 1, 1, 2, 3, 4, 6, 8, 8, 7, 5, 7, 8, 8, 7, 6, 4, 3, 3, 3, 2, 2])
    return day.replace(hour=h, minute=R.randint(0, 59), second=0)

for sp in specs:
    sev, st = sp['sev'], sp['status']
    if sp['special']:
        _, _, po, xo, co, ro = sp['sp']
        P = NOW - M(po); sp['P'] = P
        sp['B'] = P - M(R.randint(15, 90))
        sp['X'] = P + M(xo) if xo else None
        sp['stages'] = []
        if xo: sp['stages'].append((P + M(xo), 'INVESTIGATING'))
        if co: sp['stages'].append((P + M(co), 'CONTAINED'))
        if ro: sp['stages'].append((P + M(ro), 'REMEDIATING'))
        sp['D'] = None
        continue
    if st == 'CLOSED':
        base = dt.datetime(2026, 1, 5) + dt.timedelta(days=R.uniform(0, 282))
        P = clock(base); sp['P'] = P
        sla = SLA_MIN[sev]
        if R.random() < 0.62: Rm = int(sla * R.uniform(0.35, 0.95))
        else: Rm = int(sla * R.uniform(1.15, 3.5))
        sp['Rmin'] = Rm
        X = max(3, int(Rm * R.uniform(0.05, 0.2)))
        D = Rm
        path = wchoice([('C', 'R'), ('R',), ('C',), ()], [70, 12, 10, 8])
        mids = R.sample(range(X + 1, D), len(path)); mids.sort()
        stg = [(P + M(X), 'INVESTIGATING')]
        for m, p in zip(mids, path): stg.append((P + M(m), 'CONTAINED' if p == 'C' else 'REMEDIATING'))
        stg.append((P + M(D), 'CLOSED'))
        sp['stages'] = stg; sp['X'] = P + M(X); sp['D'] = P + M(D)
        sp['B'] = P - M(R.randint(15, 300))
    elif st == 'NEW':
        P = NOW - M(R.randint(290, 8600)); sp['P'] = P; sp['X'] = None; sp['D'] = None; sp['stages'] = []
        sp['B'] = P - M(R.randint(15, 200))
    else:
        P = NOW - M(R.randint(2200, 55 * 1440)); P = P.replace(second=0); sp['P'] = P
        X = R.randint(5, 90); stg = [(P + M(X), 'INVESTIGATING')]
        if st in ('CONTAINED', 'REMEDIATING'):
            skip = (st == 'REMEDIATING' and R.random() < 0.2)
            t = X
            if not skip:
                t += R.randint(30, 900); stg.append((P + M(t), 'CONTAINED'))
            if st == 'REMEDIATING':
                t += R.randint(30, 1200); stg.append((P + M(t), 'REMEDIATING'))
        sp['stages'] = stg; sp['X'] = P + M(X); sp['D'] = None
        sp['B'] = P - M(R.randint(20, 300))
    assert sp['B'] < sp['P']
specs.sort(key=lambda s: s['P'])
for i, sp in enumerate(specs):
    sp['id'] = 'INC%03d' % (i + 1)
    assert all(sp['stages'][k][0] < sp['stages'][k + 1][0] for k in range(len(sp['stages']) - 1))
    assert all(t <= NOW for t, _ in sp['stages'])
INC = {s['id']: s for s in specs}
incs = specs

# ------------------------------------------------------------------ ORG + ASSET LINKS
OW = {True: {'CRITICAL': 5, 'HIGH': 3, 'MEDIUM': 1.2, 'LOW': 0.5}, False: {'CRITICAL': 2, 'HIGH': 2, 'MEDIUM': 1.5, 'LOW': 1}}
for sp in incs:
    ch = sp['sev'] in ('CRITICAL', 'HIGH')
    sp['org'] = wchoice([o['id'] for o in orgs], [OW[ch][o['imp']] for o in orgs])
    sp['scn'] = wchoice(list(SC), [SC[k]['w'] for k in SC])
    sp['closed'] = sp['status'] == 'CLOSED'
def pool_for(org, closed):
    return [a for a in asset_by_org[org] if not (closed and a in HOT)]
caps = [min(5, len(pool_for(sp['org'], sp['closed']))) for sp in incs]
ac = [1] * 150
extra_w = [{'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1, 'LOW': 0.6}[sp['sev']] for sp in incs]
for _ in range(100):
    for _try in range(50):
        i = R.choices(range(150), weights=extra_w, k=1)[0]
        if ac[i] < caps[i]: ac[i] += 1; break
for sp, k in zip(incs, ac):
    pool = pool_for(sp['org'], sp['closed'])
    lst = []
    if not sp['closed'] and any(a in HOT for a in asset_by_org[sp['org']]) and R.random() < 0.85:
        lst.append(next(a for a in asset_by_org[sp['org']] if a in HOT))
    rest = [a for a in pool if a not in lst]
    lst += wsample(rest, [aw[a] for a in rest], k - len(lst))
    sp['assets'] = lst
cands = [sp for sp in incs if sp['sev'] in ('CRITICAL', 'HIGH') and len(sp['assets']) >= 2]
R.shuffle(cands)
for sp in cands[:6]:
    other = [o['id'] for o in orgs if o['id'] != sp['org']]
    o2 = wchoice(other, [{'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1, 'LOW': 1}[ORG[x]['imp']] for x in other])
    pool = [a for a in pool_for(o2, sp['closed'])]
    sp['assets'][-1] = wchoice(pool, [aw[a] for a in pool]); sp['multi'] = True

# ------------------------------------------------------------------ IOC
def hexh(n, tag, i): return hashlib.sha256(('soc-demo-sample-%s-%d' % (tag, i)).encode()).hexdigest()[:n]
iocs = []
for i in range(25):
    iocs.append(('IP', ('203.0.113.%d' % (10 + i * 3)) if i < 13 else ('198.51.100.%d' % (20 + i * 4))))
W1 = ['update', 'secure', 'cdn', 'login', 'mail', 'sync', 'portal', 'cloud', 'static', 'verify', 'files', 'track', 'api', 'dl', 'auth']
W2 = ['sync', 'static', 'node', 'hub', 'relay', 'vault', 'gate', 'edge', 'mirror', 'point']
doms = []
for i in range(25):
    d = '%s-%s%d.example' % (W1[i % 15], W2[(i * 3) % 10], i + 1); doms.append(d); iocs.append(('Domain', d))
for i in range(20):
    iocs.append(('URL', 'https://%s-%s%d.example/%s' % (W1[(i * 2) % 15], W2[i % 10], 50 + i, R.choice(['payload/update.bin', 'login/verify.php', 'dl/setup.ps1', 'gate/index.php', 'files/invoice.zip']))))
for i in range(20):
    n = [64, 64, 64, 40, 32][i % 5]
    iocs.append(('Hash', hexh(n, 'h', i)))
for i in range(10):
    iocs.append(('Email', '%s@%s-%s.example' % (['billing', 'hr-notice', 'it-support', 'ceo-office', 'invoice', 'secure-mail', 'payroll', 'helpdesk', 'noreply', 'admin'][i], W1[(i * 4) % 15], 'corp%d' % i)))
assert len(iocs) == 100 and len({v for _, v in iocs}) == 100 and all(len(v) <= 100 for _, v in iocs)
iocrows = [dict(id='IOC%03d' % (i + 1), type=t, val=v) for i, (t, v) in enumerate(iocs)]
IOCT = collections.defaultdict(list)
for r in iocrows: IOCT[r['type']].append(r)
hot_ioc = set()
for t, n in [('IP', 4), ('Domain', 3), ('Hash', 3), ('URL', 2), ('Email', 1)]:
    for r in R.sample(IOCT[t], n): hot_ioc.add(r['val'])
mu = {'CRITICAL': 3.0, 'HIGH': 2.4, 'MEDIUM': 1.9, 'LOW': 1.4}
ik = [max(0, min(6, int(round(R.gauss(mu[sp['sev']], 1))))) for sp in incs]
ik = adjust(ik, 300, 0, [6] * 150)
for sp, k in zip(incs, ik):
    pool = [r for t in SC[sp['scn']]['ioc'] for r in IOCT[t]]
    sp['iocs'] = [r['val'] for r in wsample(pool, [8 if r['val'] in hot_ioc else 1 for r in pool], k)]
used = collections.Counter(v for sp in incs for v in sp['iocs'])
for r in iocrows:
    if used[r['val']] == 0:
        c = [sp for sp in incs if r['type'] in SC[sp['scn']]['ioc'] and r['val'] not in sp['iocs']]
        sp = R.choice(c)
        same = [v for v in sp['iocs'] if used[v] >= 3]
        if same:
            old = R.choice(same); sp['iocs'][sp['iocs'].index(old)] = r['val']; used[old] -= 1
        else: sp['iocs'].append(r['val'])
        used[r['val']] += 1
first_inc = {}
for sp in incs:
    for v in sp['iocs']:
        if v not in first_inc or sp['P'] < first_inc[v]['P']: first_inc[v] = sp
SRCI = ['Threat Intel Feed (giả lập)', 'MISP nội bộ (giả lập)', 'Phân tích sandbox nội bộ', 'Báo cáo ISAC đối tác (giả lập)', 'SOC Analyst phát hiện', 'Open-source feed (giả lập)']
for r in iocrows:
    f = first_inc[r['val']]
    r['time'] = min(f['P'] + M(R.randint(10, 240)) + dt.timedelta(seconds=R.randint(0, 59)), NOW - M(1))
    r['src'] = R.choice(SRCI); r['conf'] = wchoice(['HIGH', 'MEDIUM', 'LOW'], [5, 3, 2])

# ------------------------------------------------------------------ MITRE LINKS
mk = [max(1, min(5, int(round(R.gauss({'CRITICAL': 2.4, 'HIGH': 1.9, 'MEDIUM': 1.5, 'LOW': 1.2}[sp['sev']], 0.8))))) for sp in incs]
mk = adjust(mk, 250, 1, [5] * 150)
HOTM = {'T1059', 'T1110', 'T1078'}
allm = [m[0] for m in MITRE]
for sp, k in zip(incs, mk):
    core = SC[sp['scn']]['mitre']
    pool = core + [m for m in allm if m not in core]
    w = [(3 if m in HOTM else 1) * 6 if m in core else 0.15 for m in pool]
    sp['mitre'] = wsample(pool, w, k)
mused = collections.Counter(m for sp in incs for m in sp['mitre'])
for m in allm:
    if mused[m] == 0:
        c = [sp for sp in incs if m in SC[sp['scn']]['mitre'] and m not in sp['mitre']]
        sp = R.choice(c)
        same = [x for x in sp['mitre'] if mused[x] >= 3]
        if same:
            old = R.choice(same); sp['mitre'][sp['mitre'].index(old)] = m; mused[old] -= 1
        else: sp['mitre'].append(m)
        mused[m] += 1

# ------------------------------------------------------------------ ASSIGNMENTS
RW = {'SOC Manager': 0.3, 'SOC Analyst L3': 0.8, 'SOC Analyst L2': 1.4, 'Incident Responder': 1.0, 'Threat Hunter': 0.7, 'SOC Analyst L1': 1.2}
AFF = {'exfil': ['Threat Hunter'], 'lateral': ['Threat Hunter', 'Incident Responder'], 'phish': ['Threat Hunter'],
       'ransom': ['Incident Responder'], 'powershell': ['Incident Responder']}
def emp_pool(role_set): return [e for e in emps if e['role'] in role_set]
unassigned = [sp for sp in incs if sp['status'] == 'NEW' and sp['sev'] != 'CRITICAL']
assert len(unassigned) == 9
for sp in incs:
    sp['members'] = []
    if sp in unassigned: continue
    sev = sp['sev']
    n = {'CRITICAL': R.choice([3, 4, 4, 5]), 'HIGH': R.choice([2, 3, 3]), 'MEDIUM': R.choice([2, 2, 3]), 'LOW': R.choice([1, 2, 2])}[sev]
    is_open_active = sp['status'] in ('INVESTIGATING', 'CONTAINED', 'REMEDIATING')
    lead = None
    if is_open_active and R.random() < 0.65:
        lead = wchoice(OVERLOADED, [3, 3, 2])
        if sev == 'CRITICAL' and E[lead]['role'] not in ('SOC Analyst L2', 'SOC Analyst L3'): lead = None
    if lead is None:
        roles = {'CRITICAL': ['SOC Analyst L2', 'SOC Analyst L3'], 'HIGH': ['SOC Analyst L2', 'SOC Analyst L3', 'Incident Responder'],
                 'MEDIUM': ['SOC Analyst L2', 'SOC Analyst L1'], 'LOW': ['SOC Analyst L1', 'SOC Analyst L2']}[sev]
        pool = [e for e in emp_pool(roles) if e['id'] not in OVERLOADED or not is_open_active]
        lead = wchoice([e['id'] for e in pool], [RW[e['role']] for e in pool])
    sp['members'] = [lead]
    while len(sp['members']) < n:
        pool = [e for e in emps if e['id'] not in sp['members']]
        if any(E[m]['role'] == 'SOC Manager' for m in sp['members']): pool = [e for e in pool if e['role'] != 'SOC Manager']
        if is_open_active: pool = [e for e in pool if e['id'] not in OVERLOADED or R.random() < 0.35]
        w = [RW[e['role']] * (2.5 if e['role'] in AFF.get(sp['scn'], []) else 1) for e in pool]
        sp['members'].append(wchoice([e['id'] for e in pool], w))
    if sev == 'CRITICAL' and not any(E[m]['role'] in ('SOC Analyst L2', 'SOC Analyst L3') for m in sp['members']):
        sp['members'][0] = R.choice([e['id'] for e in emps if e['role'] in ('SOC Analyst L2', 'SOC Analyst L3')])
    sp['lead'] = sp['members'][0]
total = sum(len(sp['members']) for sp in incs)
guard = 0
while total < 300 and guard < 5000:
    guard += 1
    sp = R.choice([s for s in incs if s['members'] and s['sev'] != 'LOW'])
    pool = [e for e in emps if e['id'] not in sp['members'] and e['role'] != 'SOC Manager' and e['id'] not in OVERLOADED]
    sp['members'].append(R.choice(pool)['id']); total += 1
for sp in incs:
    sp['assign'] = []
    for m in sp['members']:
        role = E[m]['role']; vt = role
        crit_guard = sp['sev'] == 'CRITICAL' and role in ('SOC Analyst L2', 'SOC Analyst L3')
        if role in ALT and not crit_guard and m != sp.get('lead') and R.random() < 0.2: vt = R.choice(ALT[role])
        sp['assign'].append((m, 'Incident Lead' if m == sp.get('lead') else POS[vt], vt))

# ------------------------------------------------------------------ ALERTS
ak = [1] * 150
wsev = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 1.5, 'LOW': 0.7}
for _ in range(300):
    for _t in range(50):
        i = R.choices(range(150), weights=[wsev[sp['sev']] for sp in incs], k=1)[0]
        if ak[i] < 10: ak[i] += 1; break
doc_ips = ['203.0.113.%d' % i for i in range(100, 160)] + ['198.51.100.%d' % i for i in range(100, 160)]
for sp in incs:
    ipi = [v for v in sp['iocs'] if v in {r['val'] for r in IOCT['IP']}]
    sp['attacker'] = ipi[0] if ipi else R.choice(doc_ips)
NOISE_IPS = {}
alerts = []
LVI = {s: i for i, s in enumerate(SEV)}
for sp, k in zip(incs, ak):
    end = min(NOW - M(1), sp['D'] if sp['D'] else NOW - M(1))
    types = SC[sp['scn']]['alerts']
    for j in range(k):
        t = types[0] if j == 0 else wchoice(types, [3] + [2] * (len(types) - 1))
        if R.random() < 0.65 or end <= sp['P'] + M(5):
            lo, hi = sp['B'], sp['P']
        else:
            lo, hi = sp['P'], min(end, sp['P'] + M(360))
        secs = int((hi - lo).total_seconds())
        tm = lo + dt.timedelta(seconds=R.randint(0, max(1, secs - 1)))
        if j == 0: sev = sp['sev']
        else:
            sev = SEV[max(0, min(3, LVI[sp['sev']] + wchoice([-1, 0, 1], [25, 60, 15])))]
        asset = sp['assets'][j % len(sp['assets'])]
        a = A[asset]; att = sp['attacker']
        if R.random() < 0.3: att = att.rsplit('.', 1)[0] + '.%d' % R.randint(100, 199) if att not in {r['val'] for r in IOCT['IP']} else att
        if t in INBOUND: src, dst = att, a['ip']
        elif t == 'Privilege Escalation':
            oth = [A[x]['ip'] for x in asset_by_org[a['org']] if x != asset]
            src, dst = a['ip'], R.choice(oth)
        else: src, dst = a['ip'], att
        n = R.randint(5, 240)
        content = {
         'Brute Force': 'Phát hiện %d lần đăng nhập thất bại liên tiếp từ %s tới %s' % (n, src, a['name']),
         'Suspicious PowerShell': 'PowerShell chạy với tham số mã hóa/ẩn cửa sổ trên %s, tiến trình cha bất thường' % a['name'],
         'Malware Detection': 'Phát hiện tệp độc hại (mẫu giả lập) trên %s, kết nối tới %s' % (a['name'], dst),
         'Port Scanning': 'Quét %d cổng trong thời gian ngắn từ %s nhắm vào %s' % (n * 3, src, a['name']),
         'Privilege Escalation': 'Tiến trình trên %s yêu cầu nâng quyền bất thường, đích %s' % (a['name'], dst),
         'Suspicious Outbound Traffic': 'Lưu lượng ra ngoài %d MB bất thường từ %s tới %s' % (n * 4, a['name'], dst),
         'Credential Access': 'Truy cập vùng nhớ chứa thông tin xác thực trên %s liên quan %s' % (a['name'], src),
         'Web Attack': 'Mẫu tấn công web (SQLi/XSS giả lập) từ %s vào %s, %d yêu cầu' % (src, a['name'], n)}[t]
        alerts.append(dict(inc=sp['id'], type=t, src=src, dst=dst, time=tm, source=R.choice(SRC[t]), sev=sev, content=content, assets=[asset]))
alerts.sort(key=lambda a: (a['time'], a['inc']))
for i, a in enumerate(alerts): a['id'] = 'CB%03d' % (i + 1)
# alert -> assets
byinc = collections.defaultdict(list)
for a in alerts: byinc[a['inc']].append(a)
for iid, lst in byinc.items():
    sp = INC[iid]
    for j, a in enumerate(lst):  # re-spread so every incident asset gets an alert where possible
        a['assets'] = [sp['assets'][j % len(sp['assets'])]]
        # keep IP coherence with the final asset
        ass = A[a['assets'][0]]
        if a['type'] in INBOUND: a['dst'] = ass['ip']
        elif a['type'] == 'Privilege Escalation':
            oth = [A[x]['ip'] for x in asset_by_org[ass['org']] if x != ass['id']]; a['src'], a['dst'] = ass['ip'], R.choice(oth)
        else: a['src'] = ass['ip']
        n = R.randint(5, 240)
        a['content'] = {
         'Brute Force': 'Phát hiện %d lần đăng nhập thất bại liên tiếp từ %s tới %s' % (n, a['src'], ass['name']),
         'Suspicious PowerShell': 'PowerShell chạy với tham số mã hóa/ẩn cửa sổ trên %s, tiến trình cha bất thường' % ass['name'],
         'Malware Detection': 'Phát hiện tệp độc hại (mẫu giả lập) trên %s, kết nối tới %s' % (ass['name'], a['dst']),
         'Port Scanning': 'Quét %d cổng trong thời gian ngắn từ %s nhắm vào %s' % (n * 3, a['src'], ass['name']),
         'Privilege Escalation': 'Tiến trình trên %s yêu cầu nâng quyền bất thường, đích %s' % (ass['name'], a['dst']),
         'Suspicious Outbound Traffic': 'Lưu lượng ra ngoài %d MB bất thường từ %s tới %s' % (n * 4, ass['name'], a['dst']),
         'Credential Access': 'Truy cập vùng nhớ chứa thông tin xác thực trên %s liên quan %s' % (ass['name'], a['src']),
         'Web Attack': 'Mẫu tấn công web (SQLi/XSS giả lập) từ %s vào %s, %d yêu cầu' % (a['src'], ass['name'], n)}[a['type']]
extra_need = 500 - len(alerts)
cand = [a for a in alerts if len(INC[a['inc']]['assets']) >= 2]
R.shuffle(cand)
for a in cand[:extra_need]:
    other = [x for x in INC[a['inc']]['assets'] if x not in a['assets']]
    a['assets'].append(R.choice(other))
assert len(alerts) == 450
cba = sorted({(a['id'], x) for a in alerts for x in a['assets']})

# ------------------------------------------------------------------ HISTORY + ACTIONS
hist = []
for sp in incs:
    prev = 'NEW'; 
    for t, ns in sp['stages']:
        who = sp['lead'] if (R.random() < 0.8 or len(sp['members']) == 1) else R.choice(sp['members'])
        hist.append(dict(time=t, old=prev, new=ns, inc=sp['id'], nv=who)); prev = ns
    if sp['stages']: assert prev == sp['status']
    else: assert sp['status'] == 'NEW'
hist.sort(key=lambda h: (h['time'], h['inc']))
for i, h in enumerate(hist): h['id'] = i + 1

ORDER = ['Collect Evidence', 'Scan Malware', 'Block IP', 'Isolate Host', 'Kill Process', 'Disable Account', 'Reset Password']
OUT = [('Thành công', 55), ('Thành công một phần', 8), ('Thất bại', 7), ('Cần thực hiện lại', 8), ('Phát hiện thêm IOC', 12), ('Cần chuyển cấp', 10)]
no_action = {INC_ID for INC_ID in []}
spec_ids = {sp['spi']: sp['id'] for sp in incs if sp['special']}
no_action |= {spec_ids[5], spec_ids[7]}
gen_inv = [sp['id'] for sp in incs if not sp['special'] and sp['status'] == 'INVESTIGATING']
no_action |= set(R.sample(gen_inv, 2))
for sp in incs:
    if sp['status'] == 'NEW': no_action.add(sp['id'])
used_times = set(); actions = []
def make_actions(sp, n):
    last = sp['stages'][-1][0]
    end = sp['D'] if sp['D'] else min(NOW - M(1), last + M(720))
    start = sp['X']
    secs = int((end - start).total_seconds())
    ts = set()
    while len(ts) < n:
        tm = start + dt.timedelta(seconds=R.randint(1, max(2, secs - 1)))
        if tm not in used_times: ts.add(tm)
    for tm in ts: used_times.add(tm)
    ts = sorted(ts)
    kinds = sorted([R.choice(SC[sp['scn']]['acts']) for _ in range(n)], key=ORDER.index)
    for tm, kd in zip(ts, kinds):
        perf_pool = [m for m in sp['members'] if E[m]['role'] != 'SOC Manager'] or sp['members']
        who = R.choice(perf_pool)
        ass = A[R.choice(sp['assets'])]
        detail = {'Block IP': 'Đã chặn IP %s trên firewall' % sp['attacker'],
                  'Disable Account': 'Đã vô hiệu hóa tài khoản nghi ngờ bị chiếm quyền',
                  'Isolate Host': 'Đã cách ly %s khỏi mạng' % ass['id'],
                  'Kill Process': 'Đã dừng tiến trình đáng ngờ trên %s' % ass['id'],
                  'Reset Password': 'Đã đặt lại mật khẩu và thu hồi phiên đăng nhập',
                  'Collect Evidence': 'Đã thu thập log và bộ nhớ từ %s' % ass['id'],
                  'Scan Malware': 'Đã quét mã độc trên %s' % ass['id']}[kd]
        oc = wchoice([o for o, _ in OUT], [w for _, w in OUT])
        actions.append(dict(time=tm, kind=kd, res='%s - %s' % (oc, detail), inc=sp['id'], nv=who))
    return actions[-1]
for sp in incs:
    if sp['id'] in no_action: continue
    if sp['status'] == 'CLOSED': n = wchoice([1, 2, 3, 4, 5, 6, 8], [20, 25, 22, 15, 10, 5, 3])
    elif sp['status'] == 'INVESTIGATING': n = wchoice([1, 2, 3], [4, 3, 2])
    else: n = wchoice([1, 2, 3, 4, 5], [3, 4, 3, 2, 1])
    n0 = len(actions); make_actions(sp, n)
    if sp['status'] == 'CLOSED':  # final action of a closed incident is a success
        mine = [a for a in actions[n0:]]
        last = max(mine, key=lambda a: a['time']); last['res'] = 'Thành công - ' + last['res'].split(' - ', 1)[1]
closed_ids = [sp for sp in incs if sp['status'] == 'CLOSED']
while len(actions) < 350:
    make_actions(R.choice(closed_ids), 1)
actions.sort(key=lambda a: (a['time'], a['inc']))
for i, a in enumerate(actions): a['id'] = i + 1

# ------------------------------------------------------------------ RISK per incident
for sp in incs:
    lo, hi = {'CRITICAL': (80, 100), 'HIGH': (60, 79), 'MEDIUM': (35, 59), 'LOW': (5, 34)}[sp['sev']]
    amax = max(LVI[A[a]['imp']] for a in sp['assets'])
    sp['risk'] = max(lo, min(hi, int((lo + hi) / 2 + (3 - amax) * -3 + R.randint(-5, 5))))

# ------------------------------------------------------------------ DESCRIPTION
for sp in incs:
    o = ORG[A[sp['assets'][0]]['org']]
    sp['desc'] = '%s tại %s; liên quan %d tài sản và %d IOC.' % (SC[sp['scn']]['desc'], o['name'], len(sp['assets']), len(sp['iocs']))

# ------------------------------------------------------------------ EMIT SQL
def rows(table, cols, data, chunk=100):
    out = []
    for i in range(0, len(data), chunk):
        part = data[i:i + chunk]
        out.append('INSERT INTO `%s` (%s) VALUES\n%s;\n' % (table, ', '.join('`%s`' % c for c in cols), ',\n'.join('(' + ', '.join(r) + ')' for r in part)))
    return '\n'.join(out)
def n_(x): return 'NULL' if x is None else str(x)
S = []
S.append('''-- =====================================================================
-- seed_soc_incident_management.sql
-- Du lieu mau gia lap cho database `soc_incident_management` (MySQL 8.0+)
-- Tat ca ten to chuc, nhan vien, IP, domain, hash, email la DU LIEU GIA LAP.
-- Moc thoi gian tham chieu (NOW_REF) cua bo du lieu: 2026-10-21 12:00:00
--
-- HANH VI MAC DINH: chi INSERT, KHONG xoa du lieu hien co, KHONG DROP/ALTER.
-- Hay chay tren database dang TRONG (schema da tao). Neu bang da co du lieu,
-- khoi INSERT se loi khoa chinh trung va ROLLBACK thu cong (xem huong dan).
-- Khong dung INSERT IGNORE, khong tat FOREIGN_KEY_CHECKS.
-- Thu tu insert theo phu thuoc khoa ngoai.
-- =====================================================================
-- (TUY CHON, mac dinh TAT) Muon xoa du lieu cu truoc khi seed, bo comment:
-- DELETE FROM lich_su_trang_thai; DELETE FROM hanh_dong_xu_ly; DELETE FROM su_co_nhan_vien_soc;
-- DELETE FROM su_co_ky_thuat_mitre; DELETE FROM incident_ioc; DELETE FROM tai_san_incident;
-- DELETE FROM canh_bao_tai_san; DELETE FROM canh_bao; DELETE FROM su_co; DELETE FROM ioc;
-- DELETE FROM ky_thuat_mitre; DELETE FROM tai_san; DELETE FROM nhan_vien_soc; DELETE FROM to_chuc;

USE soc_incident_management;
SET NAMES utf8mb4;
START TRANSACTION;
''')
S.append('-- 1. to_chuc (20)\n' + rows('to_chuc', ['MaTC', 'TenTC', 'DiaChi', 'LinhVucHoatDong', 'SoLuongNhanVien', 'MucDoQuanTrong'],
    [[q(o['id']), q(o['name']), q(o['addr']), q(o['sector']), str(o['nv']), q(o['imp'])] for o in orgs]))
S.append('-- 2. nhan_vien_soc (30)\n' + rows('nhan_vien_soc', ['MaNV', 'CMT', 'HoTen', 'NgaySinh', 'SoDienThoai', 'Email', 'SoNamKinhNghiem'],
    [[q(e['id']), q(e['cmt']), q(e['name']), q(e['dob'].isoformat()), q(e['phone']), q(e['email']), str(e['exp'])] for e in emps]))
S.append('-- 3. tai_san (120)\n' + rows('tai_san', ['MaTS', 'Ten', 'LoaiTaiSan', 'DiaChiIP', 'HeDieuHanh', 'ViTri', 'MucDoQuanTrong', 'MaTC'],
    [[q(a['id']), q(a['name']), q(a['type']), q(a['ip']), q(a['os']), q(a['loc']), q(a['imp']), q(a['org'])] for a in assets]))
S.append('-- 4. ky_thuat_mitre (25) - ID/ten/tactic lay theo MITRE ATT&CK Enterprise; mo ta do nguoi viet. CAN DOI CHIEU LAI voi attack.mitre.org\n' + rows('ky_thuat_mitre', ['MaKyThuat', 'TenKyThuat', 'ChienThuat', 'MoTa'],
    [[q(m[0]), q(m[1]), q(m[2]), q(m[3])] for m in MITRE]))
S.append('-- 5. ioc (100)\n' + rows('ioc', ['GiaTriIOC', 'LoaiIOC', 'Nguon', 'ThoiGianPhatHien', 'MucDoTinCay'],
    [[q(r['val']), q(r['type']), q(r['src']), q(fmt(r['time'])), q(r['conf'])] for r in iocrows]))
S.append('-- 6. su_co (150)\n' + rows('su_co', ['MaIncident', 'ThoiGianBatDau', 'ThoiGianPhatHien', 'ThoiGianXuLy', 'ThoiGianDong', 'MucDoNghiemTrong', 'TrangThai', 'MoTa', 'DiemRuiRo'],
    [[q(s['id']), q(fmt(s['B'])), q(fmt(s['P'])), q(fmt(s['X'])) if s['X'] else 'NULL', q(fmt(s['D'])) if s['D'] else 'NULL', q(s['sev']), q(s['status']), q(s['desc']), str(s['risk'])] for s in incs]))
S.append('-- 7. canh_bao (450)\n' + rows('canh_bao', ['MaCanhBao', 'LoaiCanhBao', 'IPNguon', 'IPDich', 'ThoiGianPhatHien', 'NguonPhatHien', 'MucDoNghiemTrong', 'NoiDung', 'MaIncident'],
    [[q(a['id']), q(a['type']), q(a['src']), q(a['dst']), q(fmt(a['time'])), q(a['source']), q(a['sev']), q(a['content']), q(a['inc'])] for a in alerts]))
S.append('-- 8. canh_bao_tai_san (%d)\n' % len(cba) + rows('canh_bao_tai_san', ['MaCanhBao', 'MaTS'], [[q(a), q(b)] for a, b in cba]))
tsi = sorted({(x, sp['id']) for sp in incs for x in sp['assets']})
S.append('-- 9. tai_san_incident (%d)\n' % len(tsi) + rows('tai_san_incident', ['MaTS', 'MaIncident'], [[q(a), q(b)] for a, b in tsi]))
ii = sorted({(sp['id'], v) for sp in incs for v in sp['iocs']})
S.append('-- 10. incident_ioc (%d)\n' % len(ii) + rows('incident_ioc', ['MaIncident', 'GiaTriIOC'], [[q(a), q(b)] for a, b in ii]))
im = sorted({(sp['id'], m) for sp in incs for m in sp['mitre']})
S.append('-- 11. su_co_ky_thuat_mitre (%d)\n' % len(im) + rows('su_co_ky_thuat_mitre', ['MaIncident', 'MaKyThuat'], [[q(a), q(b)] for a, b in im]))
asg = sorted((sp['id'], m, pos, vt) for sp in incs for m, pos, vt in sp['assign'])
S.append('-- 12. su_co_nhan_vien_soc (%d)\n' % len(asg) + rows('su_co_nhan_vien_soc', ['MaIncident', 'MaNV', 'ViTri', 'VaiTro'], [[q(a), q(b), q(c), q(d)] for a, b, c, d in asg]))
S.append('-- 13. hanh_dong_xu_ly (%d) - ThoiGian = ThoiGianThucHien (gia dinh)\n' % len(actions) + rows('hanh_dong_xu_ly', ['MaHanhDong', 'ThoiGianThucHien', 'ThoiGian', 'HanhDong', 'KetQua', 'MaIncident', 'MaNV'],
    [[str(a['id']), q(fmt(a['time'])), q(fmt(a['time'])), q(a['kind']), q(a['res']), q(a['inc']), q(a['nv'])] for a in actions]))
S.append('-- 14. lich_su_trang_thai (%d)\n' % len(hist) + rows('lich_su_trang_thai', ['MaLichSu', 'ThoiDiemThayDoi', 'TrangThaiCu', 'TrangThaiMoi', 'MaIncident', 'MaNV'],
    [[str(h['id']), q(fmt(h['time'])), q(h['old']), q(h['new']), q(h['inc']), q(h['nv'])] for h in hist]))
S.append('COMMIT;\n')
open('/mnt/user-data/outputs/seed_soc_incident_management.sql', 'w', encoding='utf-8').write('\n'.join(S))
print('counts', len(orgs), len(emps), len(assets), len(incs), len(alerts), len(iocrows), len(MITRE), len(cba), len(tsi), len(ii), len(im), len(asg), len(actions), len(hist))
