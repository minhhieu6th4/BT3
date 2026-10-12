const TOKEN_KEY = "bt3-demo-token";
export const session = {
  get token() { return sessionStorage.getItem(TOKEN_KEY); },
  save(token) { sessionStorage.setItem(TOKEN_KEY, token); },
  clear() { sessionStorage.removeItem(TOKEN_KEY); },
};

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

export async function api(path, {method = "GET", body, authenticated = false} = {}) {
  const headers = {Accept: "application/json"};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (authenticated && session.token) headers.Authorization = `Bearer ${session.token}`;
  let response;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    response = await fetch(path, {method, headers, body: body === undefined ? undefined : JSON.stringify(body), cache: "no-store", signal: controller.signal});
  } catch { throw new ApiError("Không kết nối được máy chủ hoặc yêu cầu quá lâu. Hãy thử lại.", 0); }
  finally { clearTimeout(timeout); }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && authenticated) {
      session.clear();
      window.dispatchEvent(new Event("session-expired"));
    }
    let message = typeof data.detail === "string" ? data.detail : "Không thực hiện được yêu cầu. Vui lòng thử lại.";
    if (Array.isArray(data.detail)) {
      message = data.detail.map(item => {
        const field = item.loc?.at(-1);
        if (field === "password") return "Mật khẩu cần có từ 8 đến 128 ký tự.";
        if (field === "username") return "Tên đăng nhập cần 3–64 ký tự, dùng a-z, 0-9, _ hoặc -.";
        return "Dữ liệu chưa hợp lệ. Hãy kiểm tra các trường thông tin.";
      }).join(" ");
    }
    throw new ApiError(message, response.status);
  }
  return data;
}
