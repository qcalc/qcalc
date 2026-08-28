__version__ = "v1.0.16.628-rc"  # @2026.08.28
__author__ = "Debasish C Saha"
__version_info__ = tuple(
    [
        int(num) if num.isdigit() else num
        for num in __version__.replace("-", ".", 1).split(".")
    ]
)
STATIC_VERSION = '1.0.28'
