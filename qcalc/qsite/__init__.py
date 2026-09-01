__version__ = "v1.1.12.631-rc"  # @2026.09.01
__author__ = "Debasish C Saha"
__version_info__ = tuple(
    [
        int(num) if num.isdigit() else num
        for num in __version__.replace("-", ".", 1).split(".")
    ]
)
STATIC_VERSION = '1.1.01'
