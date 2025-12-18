# Maintainer: Ven0m0 <you@invalid>
pkgname=python-mc-rcon
pkgver=0.0.1
pkgrel=1
pkgdesc='RCON protocol client for a Minecraft server (sync/async + CLI + Tk GUI)'
arch=('any')
url='https://github.com/Ven0m0/mc-rcon'
license=('MIT')
depends=('python' 'python-platformdirs')
optdepends=(
  'python-orjson: faster JSON serialization (audit/gui)'
  'python-uvloop: faster asyncio event loop (non-Windows)'
)
makedepends=('python-build' 'python-installer' 'python-wheel')
source=("${url}/archive/refs/tags/v${pkgver}.tar.gz")
sha256sums=('SKIP')

build() {
  cd "mc-rcon-${pkgver}"
  python -m build --wheel --no-isolation
}

package() {
  cd "mc-rcon-${pkgver}"
  python -m installer --destdir="${pkgdir}" dist/*.whl
  # License: pyproject has license text "mit", README points to LICENSE.
  # If LICENSE exists, install it; don't fail if missing.
  if [[ -f LICENSE ]]; then
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
  fi
}
