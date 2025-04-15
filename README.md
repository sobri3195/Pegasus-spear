# Pegasus-Spear

![Pegasus-Spear]

Pegasus-Spear is a Python-based Remote Access Tool designed for educational and authorized testing purposes only.

## ⚠️ Important Security Notice

This software is intended for educational purposes and authorized security testing only. Misuse of this software can raise legal and ethical issues which the authors do not support and cannot be held responsible for.

## Contact & Support

- **Author**: Letda Kes dr. Sobri, S.Kom
- **Email**: muhammadsobrimaulana31@gmail.com
- **GitHub**: [github.com/sobri3195](https://github.com/sobri3195)
- **Support Development**: [Donate via Lynk](https://lynk.id/muhsobrimaulana)

## Features

### Core Features
- Secure communication with end-to-end encryption
- Rate limiting and brute force protection
- Comprehensive logging and monitoring
- Cross-platform support (Windows, Linux)
- File upload/download with size limits and validation
- Screenshot capability
- Geolocation
- Screen locking
- Audio recording
- Configurable persistence options

### Advanced Features
1. **Webcam Capture**: Securely capture images from the target's webcam
2. **Keylogger**: Record keystrokes with configurable duration
3. **Clipboard Monitor**: Monitor and retrieve clipboard contents
4. **System Information**: Gather detailed system information including hardware, OS, and network details
5. **Browser Data**: Extract browser cookies and history information
6. **Network Scanner**: Scan local network for active hosts
7. **Advanced Audio Stream**: High-quality audio streaming with configurable parameters
8. **Process Monitor**: Real-time monitoring of process creation and termination
9. **Registry Monitor**: Monitor Windows Registry changes (Windows only)
10. **Screen Recorder**: Record screen activity with video output

## Security Improvements

- Updated to Python 3 with modern security practices
- End-to-end encryption for all communications
- Input validation and sanitization
- Rate limiting and brute force protection
- Secure file handling with size limits
- Environment-based configuration
- HTTPS enforcement in production
- Session security improvements
- Proper error handling and logging
- Regular security updates via requirements.txt

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)
- For audio recording: PortAudio library

### Installing PortAudio

#### Windows
```powershell
choco install portaudio
```

#### Linux
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sobri3195/Pegasus-spear.git
cd Pegasus-spear
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install the Python requirements:
```bash
pip install -r requirements.txt
```

4. Set up the environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
cd server
python pegasus.py initdb
```

## Running the Server

### Development
```bash
python pegasus.py runserver -h 127.0.0.1 -p 8080 --threaded
```

### Production
```bash
gunicorn "pegasus:create_app('prod')" -b 127.0.0.1:8080 --threads 20 --certfile cert.pem --keyfile key.pem
```

## Building the Agent

Update the agent configuration in `agent/config.py`, then build:

```bash
cd agent
python builder.py -p <platform> --server https://your-server:8080 -o payload
```

Supported platforms: Windows, Linux

### Agent Configuration Options

- `--hello-interval`: Delay between server checks (default: 5s)
- `--idle-time`: Inactivity timeout (default: 60s)
- `--max-failed-connections`: Max failed connection attempts (default: 5)
- `--persistent`: Enable persistence (use with caution)

## Command Reference

### Core Commands
- `upload <localfile>`: Upload a file to the server
- `download <url> <destination>`: Download a file from URL
- `screenshot`: Take a screenshot
- `geolocation`: Get target's location
- `lockscreen`: Lock the screen
- `help`: Show help message

### Advanced Commands
- `webcam`: Capture image from webcam
- `keylog [duration]`: Start keylogger (default: 60 seconds)
- `clipboard`: Monitor clipboard contents
- `sysinfo`: Get detailed system information
- `browser`: Extract browser data
- `network`: Scan local network
- `audio [duration]`: Stream audio (default: 10 seconds)
- `procmon [duration]`: Monitor processes (default: 60 seconds)
- `regmon [key_path]`: Monitor registry changes (Windows only)
- `record [duration]`: Record screen (default: 10 seconds)

## Security Best Practices

1. Always use HTTPS in production
2. Change default secret keys
3. Use strong passwords
4. Regularly update dependencies
5. Monitor logs for suspicious activity
6. Use rate limiting in production
7. Implement proper access controls
8. Regular security audits
9. Keep the system updated
10. Monitor system resource usage

## Logging

Logs are stored in `pegasus.log` with rotation enabled. Monitor these logs for security events and debugging.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author
Letda Kes dr. Sobri, S.Kom  
Email: muhammadsobrimaulana31@gmail.com  
GitHub: [github.com/sobri3195](https://github.com/sobri3195)

## Support Development

If you find this tool useful, consider supporting its development:  
[Donate via Lynk](https://lynk.id/muhsobrimaulana)

## Acknowledgments

- Security researchers and contributors
- Python security community
- All supporters and donors
