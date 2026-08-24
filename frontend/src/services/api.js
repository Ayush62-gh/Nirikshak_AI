export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Helper to parse error detail from backend API response or fallback to generic message.
 */
async function getErrorMessage(response, fallbackMsg) {
  try {
    const errorData = await response.json();
    if (errorData && errorData.detail) {
      return errorData.detail;
    }
    if (errorData && errorData.error) {
      return errorData.error;
    }
  } catch {
    if (response.statusText) {
      return response.statusText;
    }
  }
  return fallbackMsg || `Request failed with status ${response.status}`;
}

/**
 * Submit an image file for compliance scan.
 * POST /api/scan (multipart/form-data with "image" field)
 */
export async function submitScan(imageFile) {
  const formData = new FormData();
  formData.append("image", imageFile);

  try {
    const response = await fetch(`${API_BASE_URL}/api/scan`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorMsg = await getErrorMessage(
        response,
        `Scan submission failed (${response.status})`
      );
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error("Unable to connect to the backend server. Please check if the API service is running.");
    }
    throw error;
  }
}

/**
 * Get paginated list of scans.
 * GET /api/scans?page={page}&limit={limit}
 */
export async function getScans(page = 1, limit = 20) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/scans?page=${page}&limit=${limit}`
    );

    if (!response.ok) {
      const errorMsg = await getErrorMessage(
        response,
        `Failed to fetch scans (${response.status})`
      );
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error("Unable to connect to the backend server. Please check if the API service is running.");
    }
    throw error;
  }
}

/**
 * Get scan details by ID.
 * GET /api/scans/{scanId}
 */
export async function getScanById(scanId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/scans/${scanId}`);

    if (!response.ok) {
      const fallbackMsg =
        response.status === 404
          ? `Scan with ID "${scanId}" not found.`
          : `Failed to fetch scan details (${response.status})`;
      const errorMsg = await getErrorMessage(response, fallbackMsg);
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error("Unable to connect to the backend server. Please check if the API service is running.");
    }
    throw error;
  }
}
