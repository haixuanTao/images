# CI/CD Setup for images-rs

This document explains the automated CI/CD pipeline for building and distributing `images-rs`.

## Workflows

### 1. **CI (`ci.yml`)**
- **Triggers**: Push to main/develop, Pull Requests
- **Purpose**: Test the code on multiple platforms and Python versions
- **Matrix**: 
  - OS: Ubuntu, macOS, Windows
  - Python: 3.8, 3.9, 3.10, 3.11, 3.12
- **Steps**:
  - Install system dependencies (dav1d, NASM)
  - Install Rust toolchain
  - Build with maturin
  - Run comprehensive tests

### 2. **Build Wheels (`wheels.yml`)**
- **Triggers**: Git tags (`v*`), Releases, Manual dispatch
- **Purpose**: Build binary wheels for distribution
- **Platforms**: Linux, macOS, Windows
- **Special Features**:
  - Uses Zig for better cross-compilation and static linking
  - Bundles dav1d dependencies for standalone wheels
  - NASM optimizations enabled
- **Outputs**: 
  - Binary wheels for all supported Python versions
  - Source distribution (sdist)
  - Automatic PyPI upload on release

### 3. **Release (`release.yml`)**
- **Trigger**: Manual workflow dispatch
- **Purpose**: Automate version bumps and releases
- **Steps**:
  - Update version in `Cargo.toml` and `pyproject.toml`
  - Create git tag
  - Create GitHub release with changelog
  - Trigger wheel building

### 4. **Test Wheels (`test-wheels.yml`)**
- **Triggers**: After release, Manual dispatch
- **Purpose**: Verify published wheels work correctly
- **Tests**: Install from PyPI and run basic functionality tests

## Setup Requirements

### GitHub Repository Secrets

You'll need to add these secrets to your GitHub repository:

1. **`PYPI_API_TOKEN`**: 
   - Go to [PyPI](https://pypi.org/account/login/)
   - Generate an API token
   - Add to GitHub repo secrets

### PyPI Project Setup

1. **Reserve project name**:
   ```bash
   # First time only - reserve the name
   pip install twine
   python setup.py sdist
   twine upload --repository testpypi dist/*  # Test first
   twine upload dist/*  # Upload to real PyPI
   ```

2. **Configure trusted publisher** (recommended):
   - Go to PyPI project settings
   - Add GitHub as trusted publisher
   - Repository: `your-username/images-rs`
   - Workflow: `wheels.yml`
   - Environment: Not set

## Usage

### Regular Development
1. Push code → CI runs automatically
2. Create PR → CI runs on PR

### Creating a Release
1. Go to GitHub Actions
2. Run "Release" workflow
3. Enter version (e.g., `0.1.1`)
4. This will:
   - Update version files
   - Create git tag
   - Create GitHub release  
   - Build and upload wheels to PyPI

### Manual Wheel Building
```bash
# Trigger wheel building manually
gh workflow run wheels.yml
```

## Platform Support

| Platform | Architecture | Python Versions | Status |
|----------|-------------|-----------------|--------|
| Linux    | x86_64      | 3.8-3.12       | ✅     |
| macOS    | x86_64      | 3.8-3.12       | ✅     |
| macOS    | arm64       | 3.8-3.12       | ✅     |
| Windows  | x86_64      | 3.8-3.12       | ✅     |

## Dependencies

### System Dependencies
- **Linux**: `libdav1d-dev`, `nasm`
- **macOS**: `dav1d`, `nasm` (via Homebrew)  
- **Windows**: `nasm` (via Chocolatey), dav1d (static linking)

### Build Tools
- **Rust**: Latest stable toolchain
- **Zig**: For cross-compilation and static linking (PyPI releases only)
- **cargo-zigbuild**: Cross-compilation tool
- **Python**: maturin, numpy for building
- **CI**: Pillow for testing

## Troubleshooting

### Common Issues

1. **dav1d linking errors**:
   - Ensure system dependencies are installed
   - Check static linking configuration

2. **NASM not found**:
   - Install NASM on the build system
   - Add to PATH

3. **Wheel compatibility**:
   - Check manylinux compatibility
   - Verify architecture targets

### Debug Tips

- Check CI logs for build failures
- Test locally with `maturin build --release`
- Use `auditwheel show` to inspect Linux wheels
- Test wheels before releasing: `pip install dist/wheel_name.whl`

## Performance Optimization

The CI builds include:
- **Release mode**: `--release` flag for optimized binaries
- **NASM assembly**: Hardware-optimized routines where available
- **Static linking**: Reduce runtime dependencies
- **sccache**: Faster rebuilds in CI

### Zig Integration Benefits

For PyPI wheel builds, Zig provides:

1. **Better Cross-Compilation**: 
   - Consistent toolchain across platforms
   - Better handling of different architectures (Intel/Apple Silicon)

2. **Static Linking**:
   - Bundles dav1d dependency into wheels
   - Reduces installation requirements for end users
   - No need for system dav1d installation

3. **Smaller Binaries**:
   - Better dead code elimination
   - Optimized linking process

4. **Reliability**:
   - More predictable builds across different CI environments
   - Reduces platform-specific linking issues

This setup ensures high-quality, performant wheels are automatically built and distributed for all supported platforms.