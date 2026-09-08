__version__ = "v1.2.14.638-rc"  # @2026.09.08
# __version__ = "v1.1.17.635-rc"  # @2026.09.05 tagged v1.1.17-rc
__author__ = "Debasish C Saha"
__version_info__ = tuple(
    [
        int(num) if num.isdigit() else num
        for num in __version__.replace("-", ".", 1).split(".")
    ]
)
STATIC_VERSION = '1.2.58'
sitemap_lastmod = {
    "page": "2024-08-03",
    "doc": "2026-09-04",
    "cal": "2026-09-03",
    "help": "2026-09-03",
    "cat": "2024-08-03",
    "qty": "2024-08-03",
}
