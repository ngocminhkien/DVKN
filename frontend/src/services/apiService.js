import { API_BASE_URL } from '../config';

/* ==========================================================================
   OLD MOCK/VPN CODE REMOVED
   We completely disabled and removed the old logic:
   - const API_IP_BASE = 'http://26.70.59.176:8000'; // IP cũ của nhóm: 26.21.187.230
   - Dynamic targetUrl fallback based on window.location.port or VPN IP checks.
   - fetchDashboardSummary which was unused in the application.
   ========================================================================== */

/**
 * Lấy dữ liệu phân tích trực tiếp (Live Data & Ping checks) từ BFF API B5.
 * @param {string} timeRange - 'today' | '7days' | '30days'
 */
export const fetchDashboardLive = async (timeRange = 'today') => {
  const targetUrl = `${API_BASE_URL}/api/v1/dashboard/live?range=${timeRange}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 4000); // 4 giây timeout vì ping check có thể cần thời gian

  try {
    const response = await fetch(targetUrl, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Yêu cầu thất bại với mã trạng thái ${response.status}`);
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text();
      throw new Error(`Phản hồi từ API không phải là JSON hợp lệ. Nhận được HTML/Text: ${text.substring(0, 100)}...`);
    }

    return await response.json();
  } catch (error) {
    console.error("Lỗi khi gọi API live từ BFF tại URL:", targetUrl, error);
    throw error;
  }
};

/**
 * Lấy danh sách 50 log mới nhất theo loại từ BFF API.
 * @param {string} category - 'access' | 'temp' | 'alerts' | 'camera'
 */
export const fetchDashboardLogs = async (category) => {
  const apiCategory = category === 'students' ? 'access' : category;
  const targetUrl = `${API_BASE_URL}/api/v1/dashboard/logs/${apiCategory}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 4000);

  try {
    const response = await fetch(targetUrl, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Yêu cầu thất bại với mã trạng thái ${response.status}`);
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text();
      throw new Error(`Phản hồi từ API không phải là JSON hợp lệ. Nhận được HTML/Text: ${text.substring(0, 100)}...`);
    }

    return await response.json();
  } catch (error) {
    console.error("Lỗi khi gọi API logs từ BFF tại URL:", targetUrl, error);
    throw error;
  }
};
