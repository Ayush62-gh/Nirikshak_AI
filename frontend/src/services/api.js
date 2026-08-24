export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Helper to get authorization headers containing stored JWT token if present.
 */
export function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

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
 * Authenticate user with email and password.
 * POST /api/auth/login
 */
export async function loginUser(email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorMsg = await getErrorMessage(
        response,
        `Login failed (${response.status})`
      );
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(
        "Unable to connect to the authentication server. Please check if the API backend is running."
      );
    }
    throw error;
  }
}

/**
 * Register a new user account.
 * POST /api/auth/register
 */
export async function registerUser(email, password, fullName) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });

    if (!response.ok) {
      const errorMsg = await getErrorMessage(
        response,
        `Registration failed (${response.status})`
      );
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(
        "Unable to connect to the authentication server. Please check if the API backend is running."
      );
    }
    throw error;
  }
}

/**
 * Get current authenticated user profile.
 * GET /api/auth/me
 */
export async function getCurrentUser() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        ...getAuthHeaders(),
      },
    });

    if (!response.ok) {
      const errorMsg = await getErrorMessage(
        response,
        `Failed to fetch user profile (${response.status})`
      );
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(
        "Unable to connect to the authentication server. Please check if the API backend is running."
      );
    }
    throw error;
  }
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
      headers: {
        ...getAuthHeaders(),
      },
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
      `${API_BASE_URL}/api/scans?page=${page}&limit=${limit}`,
      {
        headers: {
          ...getAuthHeaders(),
        },
      }
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
    const response = await fetch(`${API_BASE_URL}/api/scans/${scanId}`, {
      headers: {
        ...getAuthHeaders(),
      },
    });

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
