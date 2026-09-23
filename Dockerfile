FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Freeze the expected schema revision into a build artifact (D-PLAT-15 v2).
# The revision is derived from the Alembic graph inside this image - never from a
# Docker ARG or an environment variable - so a drifted literal cannot exist and
# the value cannot be overridden at runtime.
# Invoked as a module (-m) so the repository root - not the script directory - is
# importable: `python <path>/script.py` puts scripts/ on sys.path, which breaks
# the generator's `config.build_info` import.
RUN python -m scripts.generate_build_info \
    && python -c "from config.build_info import get_artifact_revision; r = get_artifact_revision(); assert r, 'build revision artifact missing'; print('uap.build.artifact.verified=' + r)"

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
