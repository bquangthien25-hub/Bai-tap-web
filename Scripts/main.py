import time, os, threading, requests
from scapy.all import sniff, IP, TCP, ICMP
from flask import Flask, render_template_string

# --- CẤU HÌNH HỆ THỐNG ---
SERVER_IP = "192.168.0.200"
# Danh sách IP tin cậy (Dựa trên Radmin của cậu)
WHITELIST_IPS = ["115.73.1.102", "127.0.0.1", "192.168.0.1", "8.8.8.8", "192.168.0.101"] 
SENSITIVE_PORTS = [445, 3389, 4899] 
HONEYPOT_PORTS = [21, 22, 23, 3306, 8080]
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1494669500472365183/djcA1Sy2jkuQFhnVdXjpJwzvMKem07I2DLFp6Tsk4EdXOqC34hZUojIMzszPbFvqZyi-"
RULE_NAME = "IDS_EMERALD_PRO"

# Bộ nhớ tạm
blocked_ips = {} 
stats = {"total_blocked": 0, "logs": []}
packet_history = {} 

# --- HÀM BỔ TRỢ ---

def get_location(ip):
    """Lấy vị trí địa lý của IP truy cập"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        if response.get("status") == "success":
            return f"{response.get('country')} ({response.get('city')})"
    except: pass
    return "Unknown Location"

def notify_discord(msg):
    """Gửi thông báo về Discord khi xích được mục tiêu"""
    if not DISCORD_WEBHOOK: return
    data = {
        "embeds": [{
            "title": "💀 TARGET NEUTRALIZED",
            "description": msg,
            "color": 32768, # Màu xanh Emerald
            "footer": {"text": "IDS Emerald Active Defense System"}
        }]
    }
    try: requests.post(DISCORD_WEBHOOK, json=data, timeout=5)
    except: pass

def sync_firewall():
    """Đồng bộ danh sách đen vào Windows Firewall"""
    current_list = list(blocked_ips.keys())
    ip_string = ",".join(current_list) if current_list else "1.1.1.1"
    os.system(f'netsh advfirewall firewall set rule name="{RULE_NAME}" new remoteip={ip_string}')

def block_ip(ip, reason):
    """Thực hiện lệnh cấm vận IP"""
    if ip in blocked_ips or ip in WHITELIST_IPS: return
    
    loc = get_location(ip)
    blocked_ips[ip] = time.time()
    sync_firewall()
    
    log_entry = {
        "time": time.strftime('%d/%m/%Y %H:%M:%S'), # Fix lỗi thiếu ngày tháng
        "ip": ip,
        "loc": loc,
        "reason": reason
    }
    stats['logs'].append(log_entry)
    stats['total_blocked'] += 1
    
    print(f"\n[!!!] BANNED: {ip} | {reason}")
    notify_discord(f"**IP:** `{ip}`\n**Location:** {loc}\n**Vector:** {reason}")

def check_anomaly(ip):
    """AI phân tích hành vi bất thường (EMA)"""
    now = time.time()
    if ip not in packet_history:
        packet_history[ip] = {"last_time": now, "ema": 1.0}
        return False
    diff = max(now - packet_history[ip]["last_time"], 0.001)
    current_rate = 1.0 / diff
    packet_history[ip]["ema"] = (packet_history[ip]["ema"] * 0.9) + (current_rate * 0.1)
    packet_history[ip]["last_time"] = now
    return packet_history[ip]["ema"] > 400

# --- DASHBOARD EMERALD SHADOW V8.2 ---

app = Flask(__name__)

@app.route('/')
def dashboard():
    html = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>IDS ADAPTIVE | Smart Security Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            /* CẤU HÌNH MẶC ĐỊNH (CHẾ ĐỘ SÁNG) */
            :root {
                --bg-body: #f8f9fa;
                --bg-card: #ffffff;
                --text-main: #212529;
                --text-muted: #6c757d;
                --accent: #007bff;
                --border: #dee2e6;
                --table-head: #f1f3f5;
            }

            /* TỰ ĐỘNG CHUYỂN SANG CHẾ ĐỘ TỐI THEO HỆ ĐIỀU HÀNH */
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg-body: #0a0c10;
                    --bg-card: #161b22;
                    --text-main: #c9d1d9;
                    --text-muted: #8b949e;
                    --accent: #39ff14; /* Xanh lá Neon cho chế độ tối */
                    --border: #30363d;
                    --table-head: #21262d;
                }
            }

            body { 
                background-color: var(--bg-body) !important; 
                color: var(--text-main) !important; 
                transition: all 0.3s ease;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            .navbar { 
                background: var(--bg-card) !important; 
                border-bottom: 1px solid var(--border); 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }

            .stat-card { 
                background: var(--bg-card) !important; 
                border: 1px solid var(--border); 
                border-radius: 12px; 
                padding: 25px; 
                transition: transform 0.2s;
            }
            .stat-card:hover { transform: translateY(-5px); }

            .stat-num { 
                font-size: 3rem; 
                font-weight: 800; 
                color: var(--accent); 
                text-shadow: 0 0 10px rgba(57, 255, 20, 0.2);
            }

            .table-container { 
                background: var(--bg-card) !important; 
                border: 1px solid var(--border); 
                border-radius: 12px; 
                padding: 20px; 
                margin-top: 20px;
            }

            table { color: var(--text-main) !important; }
            th { 
                background-color: var(--table-head) !important; 
                color: var(--accent) !important; 
                border-bottom: 2px solid var(--border) !important;
                text-transform: uppercase;
                font-size: 0.85rem;
            }
            td { border-bottom: 1px solid var(--border) !important; }

            .badge-loc { 
                background: rgba(0, 123, 255, 0.1); 
                color: var(--accent); 
                border: 1px solid var(--accent);
                padding: 4px 10px; border-radius: 6px; 
            }
            
            .status-dot {
                width: 10px; height: 10px; background: var(--accent);
                border-radius: 50%; display: inline-block; margin-right: 8px;
                box-shadow: 0 0 8px var(--accent);
            }
        </style>
        <meta http-equiv="refresh" content="15">
    </head>
    <body>
        <nav class="navbar mb-4">
            <div class="container-fluid d-flex justify-content-between">
                <span class="navbar-brand fw-bold" style="color: var(--accent) !important;">
                    <i class="fas fa-shield-alt me-2"></i> IDS ADAPTIVE v1.6
                </span>
                <div class="d-flex align-items-center">
                    <span class="status-dot"></span>
                    <small class="fw-bold">HỆ THỐNG ĐANG BẢO VỆ</small>
                </div>
            </div>
        </nav>

        <div class="container-fluid px-4">
            <div class="row g-4 mb-4">
                <div class="col-md-6">
                    <div class="stat-card text-center">
                        <div class="text-muted small fw-bold">TỔNG IP BỊ XÍCH</div>
                        <div class="stat-num">{{stats['total_blocked']}}</div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="stat-card text-center">
                        <div class="text-muted small fw-bold">IP SERVER CỦA CẬU</div>
                        <div class="stat-num" style="font-size: 2rem; padding-top: 15px;">""" + SERVER_IP + """</div>
                    </div>
                </div>
            </div>

            <div class="table-container">
                <h5 class="mb-4 fw-bold"><i class="fas fa-list-ul me-2"></i> NHẬT KÝ TRUY CẬP BẤT THƯỜNG</h5>
                <div class="table-responsive">
                    <table class="table align-middle">
                        <thead>
                            <tr>
                                <th>Thời gian</th>
                                <th>Địa chỉ IP</th>
                                <th>Vị trí địa lý</th>
                                <th>Hành vi vi phạm</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for log in stats['logs']|reverse %}
                            <tr>
                                <td style="color: var(--text-muted);">{{log.time}}</td>
                                <td class="fw-bold">{{log.ip}}</td>
                                <td><span class="badge-loc">{{log.loc}}</span></td>
                                <td class="text-danger fw-bold"><i class="fas fa-exclamation-triangle me-1"></i> {{log.reason}}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, stats=stats)

# --- XỬ LÝ GÓI TIN ---

def analyze_packet(pkt):
    if not pkt.haslayer(IP): return
    src_ip = pkt[IP].src
    if src_ip in WHITELIST_IPS or src_ip == SERVER_IP: return

    if pkt.haslayer(TCP):
        dst_port = pkt[TCP].dport
        # Honeypot: Chặn ngay lập tức
        if dst_port in HONEYPOT_PORTS:
            block_ip(src_ip, f"Honeypot Triggered (Port {dst_port})")
        # Anomaly: Chặn dựa trên hành vi
        elif dst_port in SENSITIVE_PORTS:
            if check_anomaly(src_ip):
                block_ip(src_ip, f"Anomaly Detected (Port {dst_port})")

# --- MAIN ---

def start_web(): 
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Khởi tạo Firewall Rule
    os.system(f'netsh advfirewall firewall delete rule name="{RULE_NAME}"')
    os.system(f'netsh advfirewall firewall add rule name="{RULE_NAME}" dir=in action=block remoteip=1.1.1.1')
    
    # Chạy Web Dashboard
    threading.Thread(target=start_web, daemon=True).start()
    
    print("==========================================")
    print("   IDS EMERALD v8.2: SYSTEM STARTING...  ")
    print("==========================================")
    print(f"[*] Dashboard: http://localhost:5000")
    print("[*] Monitoring network traffic...")
    
    sniff(prn=analyze_packet, store=0, filter="tcp or icmp")