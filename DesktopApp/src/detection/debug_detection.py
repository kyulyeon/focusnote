import psutil
import time
from datetime import datetime

def check_all_processes():
    """Check what's running and their CPU usage"""
    
    target_apps = {
        'discord': ['discord.exe', 'discord'],
        'zoom': ['zoom.exe', 'zoom.us', 'zoom'],
        'teams': ['teams.exe', 'teams'],
        'slack': ['slack.exe', 'slack'],
        'skype': ['skype.exe', 'skype']
    }
    
    print("=" * 70)
    print(f"🔍 Scanning processes at {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)
    
    found_processes = {}
    
    for proc in psutil.process_iter(['name', 'cpu_percent', 'num_threads']):
        try:
            proc_name = proc.info['name'].lower()
            
            # Check if it matches our target apps
            for app_name, variations in target_apps.items():
                if any(var.lower() in proc_name for var in variations):
                    cpu = proc.cpu_percent(interval=0.1)
                    threads = proc.info['num_threads']
                    
                    if app_name not in found_processes:
                        found_processes[app_name] = []
                    
                    found_processes[app_name].append({
                        'name': proc.info['name'],
                        'cpu': cpu,
                        'threads': threads,
                        'pid': proc.pid
                    })
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Display results
    if not found_processes:
        print("❌ No target apps found running")
    else:
        for app_name, processes in found_processes.items():
            print(f"\n📱 {app_name.upper()}:")
            for p in processes:
                status = "🟢 ACTIVE" if p['cpu'] > 3.0 else "⚪ IDLE"
                print(f"   {status} {p['name']}")
                print(f"      CPU: {p['cpu']:.1f}% | Threads: {p['threads']} | PID: {p['pid']}")
                
                # Check network connections for Discord
                if 'discord' in app_name:
                    try:
                        proc = psutil.Process(p['pid'])
                        connections = proc.net_connections(kind='inet')
                        udp_count = len([c for c in connections if c.type == 2])
                        tcp_count = len([c for c in connections if c.type == 1])
                        print(f"      Network: {udp_count} UDP, {tcp_count} TCP connections")
                        
                        if udp_count > 2:
                            print(f"      ✅ Likely in voice call (UDP active)")
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        print(f"      ⚠️  Cannot check network (permission denied)")
    
    print("\n" + "=" * 70)
    
    # Check thresholds
    print("\n📊 DETECTION LOGIC:")
    print(f"   CPU Threshold: 3.5%")
    print(f"   Discord CPU Threshold: 5.0%")
    
    for app_name, processes in found_processes.items():
        max_cpu = max([p['cpu'] for p in processes])
        if max_cpu > 3.5:
            print(f"   ✅ {app_name.upper()} would be detected (CPU: {max_cpu:.1f}%)")
        else:
            print(f"   ❌ {app_name.upper()} below threshold (CPU: {max_cpu:.1f}%)")
    
    print("=" * 70)


def monitor_continuous():
    """Monitor continuously and show when detection would trigger"""
    print("\n🎯 CONTINUOUS MONITORING MODE")
    print("Press Ctrl+C to stop\n")
    
    call_count = 0
    in_simulated_call = False
    
    try:
        while True:
            # Clear previous line (optional, for cleaner output)
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Checking...", end='', flush=True)
            
            # Check for Discord
            discord_active = False
            zoom_active = False
            max_cpu = 0
            
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                try:
                    proc_name = proc.info['name'].lower()
                    
                    if 'discord' in proc_name:
                        cpu = proc.cpu_percent(interval=0.1)
                        if cpu > max_cpu:
                            max_cpu = cpu
                        if cpu > 5.0:
                            discord_active = True
                    
                    if 'zoom' in proc_name:
                        cpu = proc.cpu_percent(interval=0.1)
                        if cpu > 3.5:
                            zoom_active = True
                            max_cpu = cpu
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Simulate detection logic
            if discord_active or zoom_active:
                call_count += 1
                platform = "Discord" if discord_active else "Zoom"
                print(f"\n🔍 Call detected! ({call_count}/3) - {platform} @ {max_cpu:.1f}% CPU")
                
                if call_count >= 3 and not in_simulated_call:
                    print(f"\n✅ WOULD START RECORDING NOW")
                    print(f"   Platform: {platform}")
                    print(f"   🔕 DND would be enabled")
                    in_simulated_call = True
            else:
                call_count = 0
                if in_simulated_call:
                    print(f"\n❌ Call ended - WOULD STOP RECORDING")
                    print(f"   🔔 DND would be disabled")
                    in_simulated_call = False
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Stopped monitoring")


if __name__ == "__main__":
    import sys
    
    print("🔬 FocusNote Debug Tool")
    print("=" * 70)
    print("\nOptions:")
    print("1. Quick scan (one-time check)")
    print("2. Continuous monitoring (see live detection)")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        check_all_processes()
        print("\n💡 TIP: Join a call and run this again to see the difference!")
    elif choice == "2":
        monitor_continuous()
    else:
        print("Invalid choice")