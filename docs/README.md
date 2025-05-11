# Daily Digest Assistant

A serverless application that delivers personalized morning briefings via email at 6:30 AM Sydney time.

## 🔧 Setup

### Prerequisites
- Python 3.9 or later
- Git
- AWS CLI configured with appropriate credentials
- Motion API credentials
- Weather API credentials
- SMTP server access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/daily-digest.git
cd daily-digest
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Set up configuration:
```bash
# Create environment template
python scripts/create_env_template.py

# Copy template to .env and edit with your values
cp .env.template .env
```

5. Edit `.env` with your credentials and settings:
- Add your Motion API credentials
- Add your Weather API credentials
- Configure your SMTP settings
- Set your email addresses
- Adjust other settings as needed

### Development Setup

1. Install pre-commit hooks:
```bash
pre-commit install
```

2. Run tests:
```bash
pytest
```

## 🔍 Monitoring

### Health Checks
- Email delivery status
- API response times
- Error rates
- System metrics

### Logging
- CloudWatch Logs
- Error tracking
- Performance metrics
- Security events

## 🛠️ Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_api.py
```

### Code Style
- Follow PEP 8
- Use type hints
- Document all functions
- Write unit tests

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Integration Guide](docs/API_INTEGRATION.md)
- [Contributing Guide](docs/CONTRIBUTING.md)
- [Security Policy](docs/SECURITY.md)
- [Changelog](docs/CHANGELOG.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 🔒 Security

- API keys stored in AWS Secrets Manager
- Regular key rotation
- Secure email delivery
- No PII storage

See [SECURITY.md](docs/SECURITY.md) for security details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Motion API for calendar integration
- Weather API for weather data
- AWS for infrastructure
- Contributors and maintainers

## 📞 Support

For support, please:
1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/your-org/daily-digest/issues)
3. Create a new issue if needed

## 🔄 Updates

- Regular updates via GitHub releases
- Security patches as needed
- Feature updates monthly
- Bug fixes weekly

See [CHANGELOG.md](docs/CHANGELOG.md) for version history.

---

Made with ☕ and 🎩 in Sydney, Australia
