# Node.js and Bun side by side in one image, plus hyperfine (timing) and wrk (HTTP load).
FROM debian:trixie-slim
RUN apt-get update -qq && apt-get install -y -qq curl xz-utils unzip ca-certificates hyperfine wrk libatomic1 bc >/dev/null && rm -rf /var/lib/apt/lists/*
RUN curl -fsSLo /tmp/node.tar.xz https://nodejs.org/dist/v26.13.1/node-v26.13.1-linux-x64.tar.xz \
 && echo "5c063e46bab0fbc1c17cc445d7ff129cbdcd0471be6ed83b6ab864f8143bc864  /tmp/node.tar.xz" | sha256sum -c - \
 && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 && rm /tmp/node.tar.xz
RUN curl -fsSLo /tmp/bun.zip https://github.com/oven-sh/bun/releases/download/bun-v1.4.5/bun-linux-x64.zip \
 && unzip -q /tmp/bun.zip -d /tmp && mv /tmp/bun-linux-x64/bun /usr/local/bin/bun && rm -rf /tmp/bun*
WORKDIR /w
