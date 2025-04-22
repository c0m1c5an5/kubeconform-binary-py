#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from os.path import basename
from textwrap import dedent

import requests
from configupdater import ConfigUpdater
from setup_logging import setup_logging

CHECKSUMS_PATTERN = 'https://github.com/yannh/kubeconform/releases/download/%s/CHECKSUMS'

URL_PATTERNS = {
    'darwin-amd64': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-darwin-amd64.tar.gz',
    'darwin-arm64': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-darwin-arm64.tar.gz',
    'linux-386': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-linux-386.tar.gz',
    'linux-amd64': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-linux-amd64.tar.gz',
    'linux-arm64': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-linux-arm64.tar.gz',
    'linux-armv6': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-linux-armv6.tar.gz',
    'windows-amd64': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-windows-amd64.zip',
    'windows-arm64': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-windows-arm64.zip',
    'windows-armv6': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-windows-armv6.zip',
    'windows-386': 'https://github.com/yannh/kubeconform/releases/download/%s/kubeconform-windows-386.zip',
}


def get_hashes_from_url(url: str) -> dict[str, str]:
    response = requests.get(url, verify=True)
    response.raise_for_status()

    result = {}
    for line in response.text.splitlines():
        sha256sum, file = line.split()
        result[file] = sha256sum

    return result


def main(argv: Sequence[str] | None = sys.argv[1:]) -> int:
    setup_logging()
    logger = logging.getLogger()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t',
        '--tag',
        type=str,
        help='kubeconform tag to generate download config for.',
    )

    args = parser.parse_args(argv)
    logger.debug('Args: %s', args.__dict__)

    config = ConfigUpdater()
    config.read('setup.cfg')

    config_version = config['metadata']['version'].value
    if not isinstance(config_version, str):
        raise ValueError('Metadata version must be of type: str')

    config_tag = 'v' + config_version.removeprefix('v').split('-')[0]

    tag: str | None = args.tag
    version = tag if tag else config_tag

    checksums_url = CHECKSUMS_PATTERN % version
    hashes = get_hashes_from_url(checksums_url)

    data: dict[str, dict[str, str]] = {}
    for platform, url_pattern in URL_PATTERNS.items():
        url = url_pattern % version
        sha256 = hashes[basename(url)]
        data[platform] = {
            'url': url,
            'sha256': sha256,
        }

    download_scripts = dedent(
        f"""
        [kubeconform]
        group = kubeconform-binary
        marker = sys_platform == "linux" and platform_machine == "armv6hf"
        marker = sys_platform == "linux" and platform_machine == "armv7l"
        url = {data["linux-armv6"]["url"]}
        sha256 = {data["linux-armv6"]["sha256"]}
        extract = tar
        extract_path = kubeconform
        [kubeconform]
        group = kubeconform-binary
        marker = sys_platform == "linux" and platform_machine == "aarch64"
        url = {data["linux-arm64"]["url"]}
        sha256 = {data["linux-arm64"]["sha256"]}
        extract = tar
        extract_path = kubeconform
        [kubeconform]
        group = kubeconform-binary
        marker = sys_platform == "linux" and platform_machine == "i386"
        marker = sys_platform == "linux" and platform_machine == "i686"
        url = {data["linux-386"]["url"]}
        sha256 = {data["linux-386"]["sha256"]}
        extract = tar
        extract_path = kubeconform
        [kubeconform]
        group = kubeconform-binary
        marker = sys_platform == "linux" and platform_machine == "x86_64"
        url = {data["linux-amd64"]["url"]}
        sha256 = {data["linux-amd64"]["sha256"]}
        extract = tar
        extract_path = kubeconform
        [kubeconform]
        group = kubeconform-binary
        marker = sys_platform == "darwin" and platform_machine == "arm64"
        url = {data["darwin-arm64"]["url"]}
        sha256 = {data["darwin-arm64"]["sha256"]}
        extract = tar
        extract_path = kubeconform
        [kubeconform]
        group = kubeconform-binary
        marker = sys_platform == "darwin" and platform_machine == "x86_64"
        url = {data["darwin-amd64"]["url"]}
        sha256 = {data["darwin-amd64"]["sha256"]}
        extract = tar
        extract_path = kubeconform
        [kubeconform.exe]
        group = kubeconform-binary
        marker = sys_platform == "win32" and platform_machine == "ARM"
        url = {data["windows-armv6"]["url"]}
        sha256 = {data["windows-armv6"]["sha256"]}
        extract = zip
        extract_path = kubeconform.exe
        [kubeconform.exe]
        group = kubeconform-binary
        marker = sys_platform == "win32" and platform_machine == "ARM64"
        url = {data["windows-arm64"]["url"]}
        sha256 = {data["windows-arm64"]["sha256"]}
        extract = zip
        extract_path = kubeconform.exe
        [kubeconform.exe]
        group = kubeconform-binary
        marker = sys_platform == "win32" and platform_machine == "x86"
        marker = sys_platform == "cygwin" and platform_machine == "i386"
        url = {data["windows-386"]["url"]}
        sha256 = {data["windows-386"]["sha256"]}
        extract = zip
        extract_path = kubeconform.exe
        [kubeconform.exe]
        group = kubeconform-binary
        marker = sys_platform == "win32" and platform_machine == "AMD64"
        marker = sys_platform == "cygwin" and platform_machine == "x86_64"
        url = {data["windows-amd64"]["url"]}
        sha256 = {data["windows-amd64"]["sha256"]}
        extract = zip
        extract_path = kubeconform.exe
        """,
    ).strip()

    config['setuptools_download']['download_scripts'].set_values(
        download_scripts.splitlines(),
    )
    config.update_file()

    return 0


if __name__ == '__main__':
    sys.exit(main())
