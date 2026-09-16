FROM python:3.13-slim

RUN useradd --create-home --uid 1000 appuser
USER appuser
ENV HOME=/home/appuser \
    PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /home/appuser/app

COPY --chown=appuser pyproject.toml README.md ./
COPY --chown=appuser src ./src
COPY --chown=appuser skills ./skills
RUN python -m pip install --no-cache-dir .

EXPOSE 8088
CMD ["python", "src/realestate_agent/main.py"]
