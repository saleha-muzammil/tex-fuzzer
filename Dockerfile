FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        sudo \
        texlive \
        texlive-latex-extra \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

RUN echo "root ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN mkdir -p /app/profiles
RUN mkdir -p /app/results

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install snakeviz memory_profiler

RUN chmod -R 755 /app/profiles /app/results

CMD ["make", "fuzz_tex"]