# Image Reader

## Purpose

This calculator loads an image from a file or URL and displays it in qCalc.

It can also return image metadata details and EXIF tags when requested.

## Background

### Source mode and metadata option

The reader supports File and URL source modes. You can optionally enable EXIF output to inspect technical image properties and metadata tags.

## Inputs

- Mode: Select File or URL. Initial selection is File.
- Upload Image: Used when Mode is File.
- Image URL: Used when Mode is URL.
- Show Exif Tags: If enabled, returns image format, mode, size, palette, and EXIF tag listing.

- File mode requires an uploaded image file.
- URL mode requires a non-empty image URL.

## Results

- image: Displayable image output.
- exif tags: Additional metadata text output when Show Exif Tags is enabled.

## Example

Example scenario:

- Mode: File
- Upload Image: select a JPEG photo
- Show Exif Tags: true

Expected interpretation:

- image shows the uploaded picture.
- exif tags lists technical properties and available EXIF metadata fields.

## Important Assumptions and Interpretation

- Mode must be File or URL; other values are rejected.
- URL mode depends on network access and URL validity.
- EXIF availability depends on the source image; some images may have no EXIF data.
