# Contributing to Stratify

Thanks for your interest in contributing! We welcome all contributions, from bug reports to feature implementations.

## Getting Started

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/agentic-war-room.git
   cd agentic-war-room
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Style
- **Python**: Follow PEP 8
- **React/TypeScript**: Use ESLint & Prettier configs
- **Git Commits**: Use conventional commits
  - `feat:` new feature
  - `fix:` bug fix
  - `docs:` documentation
  - `refactor:` code restructure
  - `test:` tests
  - `chore:` maintenance

### Testing

Run tests before submitting:
```bash
# Python tests
pytest tests/

# Frontend tests
cd stratify-react && npm test
```

### Running Locally

Backend:
```bash
python main.py
```

Frontend:
```bash
cd stratify-react
npm install
npm run dev
```

## Submitting Changes

1. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: describe your changes"
   ```

2. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request**
   - Describe what your PR does
   - Link any relevant issues
   - Ensure all tests pass
   - Request review from maintainers

## Code Review Guidelines

All submissions go through code review. We look for:
- ✅ Code quality & consistency
- ✅ Tests covering new functionality
- ✅ Documentation updates
- ✅ No breaking changes (unless necessary)
- ✅ Clean commit history

## Reporting Bugs

Found a bug? Open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Screenshots if applicable

## Feature Requests

Have an idea? Open an issue with:
- Clear description of the feature
- Use cases & benefits
- Potential implementation approach
- Any related issues or discussions

## Questions?

- Open a discussion in the repo
- Reach out to the maintainers
- Check existing issues & PRs first

---

**Thank you for contributing to Stratify!** 🚀
