export function formatFontSize(extractedFields) {
  if (
    extractedFields?.font_size_mm !== undefined &&
    extractedFields?.font_size_mm !== null &&
    extractedFields?.font_size_mm !== ""
  ) {
    return `≈ ${extractedFields.font_size_mm} mm`;
  }

  const px = extractedFields?.font_readability_px;
  if (px && typeof px === "object") {
    const { smallest, largest, median } = px;
    return `Relative: ${smallest}-${largest} px (median ${median}), no mm calibration`;
  }

  return "Not Detected";
}

export default formatFontSize;
