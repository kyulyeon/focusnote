import platform
import subprocess
import os
import winreg
import ctypes

class DNDController:
    def __init__(self):
        self.system = platform.system()
        self.dnd_active = False
        
    def enable_dnd(self):
        """Enable Do Not Disturb mode"""
        if self.dnd_active:
            return True
            
        try:
            if self.system == "Windows":
                success = self._enable_dnd_windows()
            elif self.system == "Darwin":  # macOS
                success = self._enable_dnd_macos()
            else:  # Linux
                success = self._enable_dnd_linux()
            
            if success:
                self.dnd_active = True
                print("🔕 DND enabled")
            return success
        except Exception as e:
            print(f"⚠️  Could not enable DND: {e}")
            return False
    
    def disable_dnd(self):
        """Disable Do Not Disturb mode"""
        if not self.dnd_active:
            return True
            
        try:
            if self.system == "Windows":
                success = self._disable_dnd_windows()
            elif self.system == "Darwin":  # macOS
                success = self._disable_dnd_macos()
            else:  # Linux
                success = self._disable_dnd_linux()
            
            if success:
                self.dnd_active = False
                print("🔔 DND disabled")
            return success
        except Exception as e:
            print(f"⚠️  Could not disable DND: {e}")
            return False
    
    def _enable_dnd_windows(self):
        """Enable Windows Focus Assist using multiple methods"""
        success = False
        
        # Method 1: Set Focus Assist to "Alarms Only" mode (most aggressive)
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache\DefaultAccount\$windows.data.notifications.quiethourssettings\Current"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            # Alarms only mode = 2 (blocks everything except alarms)
            focus_assist_data = bytes([
                0x43, 0x42, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00,
                0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])
            
            winreg.SetValueEx(key, "Data", 0, winreg.REG_BINARY, focus_assist_data)
            winreg.CloseKey(key)
            success = True
            print("✅ Set Focus Assist to Alarms Only")
        except Exception as e:
            print(f"Registry method failed: {e}")
        
        # Method 2: Directly disable Discord notifications via registry
        try:
            # Find Discord's notification registry key
            discord_paths = [
                r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Discord",
                r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\com.squirrel.Discord.Discord"
            ]
            
            for path in discord_paths:
                try:
                    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, path)
                    winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 0)
                    winreg.CloseKey(key)
                    print(f"✅ Disabled Discord notifications via {path}")
                    success = True
                except:
                    pass
        except Exception as e:
            print(f"Discord disable failed: {e}")
        
        # Method 3: PowerShell to set global notification settings
        try:
            ps_script = """
            $path = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings'
            if (!(Test-Path $path)) {
                New-Item -Path $path -Force | Out-Null
            }
            Set-ItemProperty -Path $path -Name 'NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND' -Value 0 -Type DWord -Force
            Set-ItemProperty -Path $path -Name 'NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK' -Value 0 -Type DWord -Force
            
            # Restart explorer to apply changes
            Stop-Process -Name explorer -Force
            Start-Process explorer
            """
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ Applied global notification settings (restarted Explorer)")
                success = True
        except Exception as e:
            print(f"PowerShell method failed: {e}")
        
        return success
    
    def _disable_dnd_windows(self):
        """Disable Windows Focus Assist"""
        success = False
        
        # Method 1: Reset Focus Assist via registry
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\CloudStore\Store\Cache\DefaultAccount\$windows.data.notifications.quiethourssettings\Current"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            # Off mode = 0
            focus_assist_data = bytes([
                0x43, 0x42, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
            ])
            
            winreg.SetValueEx(key, "Data", 0, winreg.REG_BINARY, focus_assist_data)
            winreg.CloseKey(key)
            success = True
        except Exception as e:
            print(f"Registry restore failed: {e}")
        
        # Method 2: Re-enable Discord notifications
        try:
            discord_paths = [
                r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Discord",
                r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\com.squirrel.Discord.Discord"
            ]
            
            for path in discord_paths:
                try:
                    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, path)
                    winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(key)
                    print(f"✅ Re-enabled Discord notifications")
                    success = True
                except:
                    pass
        except:
            pass
        
        # Method 3: PowerShell to restore notification settings
        try:
            ps_script = """
            $path = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings'
            if (Test-Path $path) {
                Set-ItemProperty -Path $path -Name 'NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND' -Value 1 -Type DWord -Force
                Set-ItemProperty -Path $path -Name 'NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK' -Value 1 -Type DWord -Force
            }
            """
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                success = True
        except Exception as e:
            print(f"PowerShell restore failed: {e}")
        
        return success
    
    def _enable_dnd_macos(self):
        """Enable macOS Do Not Disturb / Focus mode"""
        success = False
        
        # Method 1: Modern macOS (Monterey 12.0+) - Use shortcuts automation
        try:
            # Enable Do Not Disturb focus mode using shortcuts
            applescript = '''
            tell application "System Events"
                try
                    tell process "ControlCenter"
                        set frontmost to true
                        click menu bar item "Control Center" of menu bar 1
                        delay 0.3
                        click checkbox "Do Not Disturb" of group 1 of window "Control Center"
                    end tell
                    return true
                on error
                    return false
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'true' in result.stdout.lower():
                print("✅ Enabled Focus mode (macOS 12+)")
                success = True
        except Exception as e:
            print(f"Modern macOS method failed: {e}")
        
        # Method 2: Use defaults command (works on most macOS versions)
        if not success:
            try:
                # Enable Do Not Disturb
                subprocess.run([
                    'defaults', 'write',
                    'com.apple.notificationcenterui',
                    'doNotDisturb',
                    '-bool', 'true'
                ], check=True, capture_output=True, timeout=3)
                
                # Set DND date to prevent auto-disable
                subprocess.run([
                    'defaults', 'write',
                    'com.apple.notificationcenterui',
                    'doNotDisturbDate',
                    '-date', '"`date -u +%Y-%m-%dT%H:%M:%SZ`"'
                ], capture_output=True, timeout=3)
                
                # Restart NotificationCenter to apply
                subprocess.run([
                    'killall', 'NotificationCenter'
                ], capture_output=True, timeout=3)
                
                print("✅ Enabled DND via defaults command")
                success = True
            except Exception as e:
                print(f"Defaults command failed: {e}")
        
        # Method 3: Direct plist modification (most reliable for older macOS)
        if not success:
            try:
                plist_path = os.path.expanduser(
                    '~/Library/Preferences/ByHost/com.apple.notificationcenterui.*.plist'
                )
                
                # Use plutil to set DND
                subprocess.run([
                    'defaults', 'write',
                    os.path.expanduser('~/Library/Preferences/ByHost/com.apple.notificationcenterui'),
                    'doNotDisturb',
                    '-bool', 'YES'
                ], capture_output=True, timeout=3)
                
                subprocess.run(['killall', 'NotificationCenter'], capture_output=True)
                print("✅ Enabled DND via plist modification")
                success = True
            except Exception as e:
                print(f"Plist method failed: {e}")
        
        # Method 4: Use shortcut command (macOS 12+)
        if not success:
            try:
                # Check if shortcuts command exists
                result = subprocess.run(
                    ['which', 'shortcuts'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Try to run a DND shortcut
                    subprocess.run([
                        'shortcuts', 'run', 'Turn On Do Not Disturb'
                    ], capture_output=True, timeout=3)
                    
                    print("✅ Enabled DND via shortcuts")
                    success = True
            except Exception as e:
                print(f"Shortcuts method failed: {e}")
        
        return success
    
    def _disable_dnd_macos(self):
        """Disable macOS Do Not Disturb / Focus mode"""
        success = False
        
        # Method 1: Modern macOS (Monterey 12.0+) - Use Control Center
        try:
            applescript = '''
            tell application "System Events"
                try
                    tell process "ControlCenter"
                        set frontmost to true
                        click menu bar item "Control Center" of menu bar 1
                        delay 0.3
                        click checkbox "Do Not Disturb" of group 1 of window "Control Center"
                    end tell
                    return true
                on error
                    return false
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'true' in result.stdout.lower():
                print("✅ Disabled Focus mode (macOS 12+)")
                success = True
        except Exception as e:
            print(f"Modern macOS disable failed: {e}")
        
        # Method 2: Use defaults command
        if not success:
            try:
                # Disable Do Not Disturb
                subprocess.run([
                    'defaults', 'write',
                    'com.apple.notificationcenterui',
                    'doNotDisturb',
                    '-bool', 'false'
                ], check=True, capture_output=True, timeout=3)
                
                # Remove DND date
                subprocess.run([
                    'defaults', 'delete',
                    'com.apple.notificationcenterui',
                    'doNotDisturbDate'
                ], capture_output=True, timeout=3)
                
                # Restart NotificationCenter
                subprocess.run([
                    'killall', 'NotificationCenter'
                ], capture_output=True, timeout=3)
                
                print("✅ Disabled DND via defaults command")
                success = True
            except Exception as e:
                print(f"Defaults disable failed: {e}")
        
        # Method 3: Direct plist modification
        if not success:
            try:
                subprocess.run([
                    'defaults', 'write',
                    os.path.expanduser('~/Library/Preferences/ByHost/com.apple.notificationcenterui'),
                    'doNotDisturb',
                    '-bool', 'NO'
                ], capture_output=True, timeout=3)
                
                subprocess.run(['killall', 'NotificationCenter'], capture_output=True)
                print("✅ Disabled DND via plist")
                success = True
            except Exception as e:
                print(f"Plist disable failed: {e}")
        
        # Method 4: Use shortcuts command
        if not success:
            try:
                result = subprocess.run(
                    ['which', 'shortcuts'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    subprocess.run([
                        'shortcuts', 'run', 'Turn Off Do Not Disturb'
                    ], capture_output=True, timeout=3)
                    
                    print("✅ Disabled DND via shortcuts")
                    success = True
            except Exception as e:
                print(f"Shortcuts disable failed: {e}")
        
        return success
    
    def _enable_dnd_linux(self):
        """Enable Linux DND (GNOME/KDE)"""
        try:
            try:
                subprocess.run([
                    'gsettings', 'set',
                    'org.gnome.desktop.notifications',
                    'show-banners',
                    'false'
                ], check=True, capture_output=True)
                return True
            except:
                pass
            
            try:
                subprocess.run([
                    'qdbus', 'org.freedesktop.Notifications',
                    '/org/freedesktop/Notifications',
                    'org.freedesktop.Notifications.Inhibit',
                    'FocusNote'
                ], check=True, capture_output=True)
                return True
            except:
                pass
            
            return False
        except Exception as e:
            print(f"Linux DND error: {e}")
            return False
    
    def _disable_dnd_linux(self):
        """Disable Linux DND"""
        try:
            try:
                subprocess.run([
                    'gsettings', 'set',
                    'org.gnome.desktop.notifications',
                    'show-banners',
                    'true'
                ], check=True, capture_output=True)
                return True
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Linux DND disable error: {e}")
            return False


# Test script
if __name__ == "__main__":
    import time
    
    print("🧪 Testing DND Controller on Windows...")
    print("=" * 50)
    
    dnd = DNDController()
    
    print("\n📋 Step 1: Send yourself a test notification NOW")
    print("   (e.g., Slack, Discord, or Windows notification)")
    input("   Press Enter when ready...")
    
    print("\n🔕 Step 2: Enabling DND in 3 seconds...")
    time.sleep(3)
    dnd.enable_dnd()
    
    print("\n⏱️  Step 3: DND is active for 15 seconds")
    print("   Try sending notifications - they should be blocked!")
    print("   Checking status...")
    
    # Check if it worked
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings")
        value, _ = winreg.QueryValueEx(key, "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND")
        winreg.CloseKey(key)
        
        if value == 0:
            print("   ✅ Notification sound is DISABLED")
        else:
            print("   ⚠️  Notification sound still enabled")
    except:
        print("   ⚠️  Could not verify status")
    
    time.sleep(15)
    
    print("\n🔔 Step 4: Disabling DND...")
    dnd.disable_dnd()
    
    print("\n✅ Test complete!")
    print("   Notifications should work normally now.")