__version__ = "v1.0.5.620-rc"  # @2026.08.20
__author__ = "Debasish C Saha"
__version_info__ = tuple(
    [
        int(num) if num.isdigit() else num
        for num in __version__.replace("-", ".", 1).split(".")
    ]
)
STATIC_VERSION = '0.99.19'
