FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# The base image can contain an obsolete Yarn APT source. CRM uses npm.
# Remove that unused source before Features run apt-get update; keep signature
# verification enabled for all repositories that we actually use.
USER root
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn.sources
