# low-pass


# OSIM C++
For autocomplete to work:
```bash
cd opensimLowPass
cmake . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=on
```
# Python
Setup
```bash
cd pythonLowPass
uv venv
source .venv/bin/activate
uv tool install pre-commit --with pre-commit-uv
uv pip install -r pyproject.toml
```
# Matlab
