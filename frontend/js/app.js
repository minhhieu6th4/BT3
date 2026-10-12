import {api, session} from "/assets/js/api.js";

const app = document.querySelector("#app");
const dialog = document.querySelector("#remove-dialog");
const state = {user: null, competition: null, teams: [], team: null, flash: "", prefill: "", revision: 0, busy: false, remove: null};
const labels = {DRAFT: "Chuẩn bị", REGISTRATION: "Đăng ký đội", CODING: "Nộp bài", VALIDATING: "Kiểm tra Bot", PLAYING: "Thi đấu", FINISHED: "Hoàn thành"};
const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[ch]));
const canControl = () => state.competition?.mode === "DEMO" && ["DRAFT", "REGISTRATION"].includes(state.competition.status) && !state.competition.submission_open;
const landing = () => state.user?.account_type === "ADMIN" ? "/demo/quan-tri" : "/demo/doi";
let toastTimer;

function toast(message, error = false) {
  const notice = document.querySelector("#notice");
  notice.textContent = message;
  notice.classList.toggle("error", error);
  notice.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { notice.hidden = true; }, 6000);
}
function header() {
  document.querySelector("#account-nav").innerHTML = state.user
    ? `<span class="user-label">${escape(state.user.username)}</span><button class="logout" id="logout">Đăng xuất ↗</button>` : "";
  document.querySelector("#logout")?.addEventListener("click", () => {
    session.clear(); state.user = null; state.team = null;
    navigate("/demo/dang-nhap");
  });
}
function navigate(path, replace = false) {
  if (dialog.open) dialog.close();
  history[replace ? "replaceState" : "pushState"]({}, "", path);
  route();
}
document.addEventListener("click", event => {
  const link = event.target.closest("a[data-link]");
  if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
  event.preventDefault(); navigate(link.getAttribute("href"));
});
window.addEventListener("popstate", route);
window.addEventListener("session-expired", () => {
  state.user = null; state.flash = "Phiên đăng nhập đã hết hạn hoặc tài khoản đã bị vô hiệu hóa. Vui lòng đăng nhập lại.";
  if (dialog.open) dialog.close();
  navigate("/demo/dang-nhap", true);
});

function setContent(html) {
  const focusedId = document.activeElement?.id;
  app.innerHTML = html;
  app.setAttribute("aria-busy", "false");
  const focusTarget = focusedId && document.getElementById(focusedId);
  (focusTarget || document.querySelector("#main")).focus({preventScroll: true});
}
function errorScreen(message) {
  setContent(`<section class="unavailable"><span class="kicker">Kết nối hệ thống</span><h1>Chưa tải được giải</h1><p>${escape(message)}</p><button id="retry" class="button">Thử lại</button></section>`);
  document.querySelector("#retry").addEventListener("click", route);
}
function blockedMain() {
  setContent(`<section class="unavailable"><span class="kicker">Giải chính</span><h1>Không gian này chưa mở</h1><p>Đăng ký sinh viên và thể thức giải đầy đủ sẽ được bổ sung sau. Hiện bạn có thể dùng giao diện giải demo.</p><a href="/demo" data-link class="button">Đến giải demo →</a></section>`);
}

async function route() {
  const revision = ++state.revision;
  header();
  if (location.pathname === "/main") { blockedMain(); return; }
  app.setAttribute("aria-busy", "true");
  try {
    if (session.token) state.user = await api("/api/auth/me", {authenticated: true});
    else state.user = null;
    if (revision !== state.revision) return;
    header();
    state.competition = await api("/api/competition");
    if (revision !== state.revision) return;
    if (state.competition.mode !== "DEMO") {
      errorScreen("Backend đang chọn giải chính. Giao diện này cần kết nối giải có mode DEMO."); return;
    }
    const path = location.pathname;
    if (["/demo", "/demo/"].includes(path)) { navigate(state.user ? landing() : "/demo/dang-nhap", true); return; }
    if (["/demo/dang-nhap", "/demo/dang-ky"].includes(path)) {
      if (state.user) { navigate(landing(), true); return; }
      renderAuth(path.endsWith("dang-ky")); return;
    }
    if (!state.user) { navigate("/demo/dang-nhap", true); return; }
    if (path === "/demo/quan-tri") {
      if (state.user.account_type !== "ADMIN") { toast("Bạn không có quyền quản trị.", true); navigate(landing(), true); return; }
      state.teams = await api("/api/teams");
      if (revision === state.revision) renderAdmin();
    } else if (path === "/demo/doi") {
      if (state.user.account_type === "ADMIN") { navigate(landing(), true); return; }
      state.team = await api("/api/teams/me", {authenticated: true});
      if (revision === state.revision) renderTeam();
    } else navigate("/demo", true);
  } catch (error) {
    if (revision === state.revision && error.status !== 401) errorScreen(error.message);
  }
}

function statusHtml() {
  const c = state.competition;
  const available = c.registration_available;
  const text = available ? "Đang mở đăng ký" : c.team_count >= c.max_teams ? "Đã đủ đội tham gia" : "Đăng ký đang đóng";
  return `<div class="status-strip ${available ? "" : "closed"}"><span>${text}</span><strong>${c.team_count}/${c.max_teams} đội</strong></div>`;
}
function hero() {
  const pieces = {6: "●", 8: "▲", 16: "■", 18: "●"};
  const board = Array.from({length: 25}, (_, i) => `<span ${pieces[i] ? `class="${i < 10 ? "piece" : "opponent"}"` : ""}>${pieces[i] || ""}</span>`).join("");
  return `<aside class="hero"><div class="eyebrow">UET Algorithm Battle</div><h1>Chiến thuật của bạn.<br><span>Đấu trường của Bot.</span></h1><p>Đăng ký đội để bắt đầu hành trình xây dựng một người chơi tự động.</p><div class="board-art" aria-hidden="true">${board}</div><div class="hero-foot"><span>01 — ĐĂNG KÝ ĐỘI</span><span>GIẢI DEMO · ${state.competition.max_teams} ĐỘI</span></div></aside>`;
}
function passwordField(id, label, autocomplete) {
  return `<div class="field"><label for="${id}">${label}</label><div class="input-wrap"><input id="${id}" name="${id}" type="password" data-password required minlength="8" maxlength="128" autocomplete="${autocomplete}"><button type="button" class="password-toggle" data-toggle="${id}" aria-label="Hiện ${label.toLowerCase()}" aria-pressed="false">Hiện</button></div></div>`;
}
function renderAuth(register) {
  document.title = `${register ? "Đăng ký đội" : "Đăng nhập"} · BT3 Demo`;
  const flash = state.flash; state.flash = "";
  setContent(`<section class="auth-layout">${hero()}<div class="form-panel"><span class="kicker">Không gian giải demo</span><h2>${register ? "Tạo đội của bạn" : "Chào mừng trở lại"}</h2><p class="intro">${register ? "Một tên đội, một tài khoản. Bắt đầu từ đây." : "Đăng nhập bằng tài khoản đội hoặc tài khoản quản trị viên của giải."}</p><nav class="tabs" aria-label="Tài khoản"><a href="/demo/dang-nhap" data-link class="${register ? "" : "active"}" ${register ? "" : 'aria-current="page"'}>Đăng nhập</a><a href="/demo/dang-ky" data-link class="${register ? "active" : ""}" ${register ? 'aria-current="page"' : ""}>Đăng ký đội</a></nav><div id="registration-status">${statusHtml()}</div>${flash ? `<p class="success-message" role="status">${escape(flash)}</p>` : ""}<form id="auth-form"><div class="field"><label for="username">${register ? "Tên đội / tên đăng nhập" : "Tên đăng nhập"}</label><input id="username" name="username" required minlength="3" maxlength="64" pattern="[A-Za-z0-9_-]{3,64}" autocomplete="username" autocapitalize="none" spellcheck="false" value="${escape(state.prefill)}" placeholder="Ví dụ: team_alpha">${register ? '<p class="hint">3–64 ký tự: chữ không dấu, số, dấu gạch dưới hoặc gạch ngang. Tên không được trùng.</p>' : ""}</div>${passwordField("password", "Mật khẩu", register ? "new-password" : "current-password")}${register ? passwordField("confirm-password", "Nhập lại mật khẩu", "new-password") : ""}<p id="form-error" class="error-message" role="alert" hidden></p><button id="submit-auth" type="submit" class="button wide" ${register && !state.competition.registration_available ? "disabled" : ""}><span>${register ? "Đăng ký đội" : "Đăng nhập"}</span><span aria-hidden="true">→</span></button></form><p class="form-note">${register ? "Mật khẩu cần 8–128 ký tự. Đăng ký thành công giữ một suất cho đội trong giải demo." : "Dành cho <strong>đội thi và ban tổ chức</strong>. Hệ thống đưa bạn đến đúng không gian sau khi đăng nhập."}</p></div></section>`);
  state.prefill = "";
  document.querySelectorAll("[data-toggle]").forEach(button => button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.toggle);
    const shown = input.type === "password";
    input.type = shown ? "text" : "password";
    button.textContent = shown ? "Ẩn" : "Hiện";
    button.setAttribute("aria-pressed", String(shown));
    button.setAttribute("aria-label", `${shown ? "Ẩn" : "Hiện"} mật khẩu`);
  }));
  document.querySelector("#auth-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = document.querySelector("#submit-auth");
    if (button.disabled) return;
    const errorBox = document.querySelector("#form-error");
    errorBox.hidden = true;
    const username = form.elements.username.value.trim().toLowerCase();
    const password = form.elements.password.value;
    if (register && password !== form.elements["confirm-password"].value) {
      errorBox.textContent = "Hai mật khẩu chưa khớp. Vui lòng kiểm tra lại."; errorBox.hidden = false; return;
    }
    button.disabled = true; button.querySelector("span").textContent = "Đang xử lý…";
    try {
      if (register) {
        await api("/api/teams", {method: "POST", body: {username, password}});
        form.reset(); state.prefill = username;
        state.flash = "Đăng ký đội thành công. Hãy đăng nhập để vào không gian đội.";
        navigate("/demo/dang-nhap");
      } else {
        const result = await api("/api/auth/login", {method: "POST", body: {username, password}});
        if (!["TEAM", "ADMIN"].includes(result.user.account_type)) throw new Error("Tài khoản này không thuộc giao diện đội/admin của demo.");
        session.save(result.access_token); state.user = result.user; form.reset();
        navigate(landing());
      }
    } catch (error) {
      errorBox.textContent = error.message; errorBox.hidden = false;
      button.disabled = false; button.querySelector("span").textContent = register ? "Đăng ký đội" : "Đăng nhập";
    }
  });
}
function phases() {
  const c = state.competition;
  const current = ["DRAFT", "REGISTRATION"].includes(c.status) ? 0 : ["CODING", "VALIDATING"].includes(c.status) ? 1 : 2;
  return `<div class="phase-bar" aria-label="Giai đoạn giải">${["Đăng ký đội", "Nộp Bot", "Thi đấu"].map((name, i) => `<div class="phase ${i === current ? "current" : ""}"><b>${String(i + 1).padStart(2, "0")}</b><span>${name}</span></div>`).join("")}</div>`;
}
function countCard() {
  const c = state.competition;
  return `<section class="card"><span class="kicker">Suất tham gia</span><div class="count">${c.team_count}<span> / ${c.max_teams} đội</span></div><div class="progress" role="progressbar" aria-label="Số đội đăng ký" aria-valuemin="0" aria-valuemax="${c.max_teams}" aria-valuenow="${c.team_count}"><span style="width:${Math.min(100, c.team_count / c.max_teams * 100)}%"></span></div><p>${Math.max(0, c.max_teams - c.team_count)} suất còn lại trong giải demo.</p></section>`;
}
function renderTeam() {
  document.title = "Đội của tôi · BT3 Demo";
  const t = state.team;
  setContent(`<section class="dashboard"><div class="page-heading"><div><span class="kicker">Không gian đội thi</span><h1>Sẵn sàng cho thử thách.</h1><p>Thông tin đăng ký của đội trong giải demo.</p></div><span class="meta-label">${escape(state.competition.name)}</span></div>${phases()}<div class="dashboard-grid"><section class="card"><div class="card-head"><h2>Đội của tôi</h2><span class="badge">Đã đăng ký</span></div><div class="team-profile"><div class="avatar">${escape(t.name.slice(0, 2).toUpperCase())}</div><div><h2>${escape(t.name)}</h2><span class="muted">Đội #${t.id}</span></div></div><div class="info-rows"><div class="info-row"><span>Tài khoản đội</span><strong>${escape(state.user.username)}</strong></div><div class="info-row"><span>Trạng thái đội</span><strong>${escape(({REGISTERED: "Đã đăng ký", APPROVED: "Đã duyệt", DISQUALIFIED: "Không đủ điều kiện", WITHDRAWN: "Đã rút"})[t.status] || t.status)}</strong></div><div class="info-row"><span>Giai đoạn giải</span><strong>${escape(labels[state.competition.status] || state.competition.status)}</strong></div></div><div class="upcoming"><strong>Tiếp theo: nộp Bot của đội</strong><p>Chức năng nộp bài sẽ được bổ sung ở bước tiếp theo. Hiện bạn đã có thể kiểm tra đăng ký và đăng nhập.</p></div></section><div class="side-stack">${countCard()}<section class="card"><h2>Trạng thái đăng ký</h2><div id="registration-status">${statusHtml()}</div><p>Ban tổ chức điều khiển việc mở và đóng đăng ký. Suất của bạn đã được ghi nhận.</p><button id="refresh-team" class="button secondary compact">Làm mới thông tin ↻</button></section></div></div></section>`);
  document.querySelector("#refresh-team").addEventListener("click", route);
}
function tableHtml() {
  if (!state.teams.length) return `<div class="empty"><div class="empty-mark" aria-hidden="true">＋</div><strong>Chưa có đội đăng ký</strong><br>Mở đăng ký để các đội tạo tài khoản tham gia.</div>`;
  return `<div class="table-wrap"><table><thead><tr><th>Đội</th><th>Mã đội</th><th>Trạng thái</th><th><span class="sr-only">Thao tác</span></th></tr></thead><tbody>${state.teams.map(team => `<tr><td><div class="team-cell"><span class="avatar">${escape(team.name.slice(0, 2).toUpperCase())}</span><strong>${escape(team.name)}</strong></div></td><td>#${team.id}</td><td><span class="badge">${escape(({REGISTERED: "Đã đăng ký", APPROVED: "Đã duyệt", DISQUALIFIED: "Không đủ điều kiện"})[team.status] || team.status)}</span></td><td><button class="delete-button" data-remove="${team.id}" ${!canControl() || state.busy ? "disabled" : ""} aria-label="Xóa đội ${escape(team.name)}">Xóa đội</button></td></tr>`).join("")}</tbody></table></div>`;
}
function renderAdmin() {
  document.title = "Quản trị giải · BT3 Demo";
  const c = state.competition;
  setContent(`<section class="dashboard"><div class="page-heading"><div><span class="kicker">Ban tổ chức · Giải demo</span><h1>Điều hành giải đấu</h1><p>Quản lý đăng ký và các đội tham gia, tại một nơi.</p></div><button id="refresh-admin" class="button secondary compact">Làm mới ↻</button></div>${phases()}<div class="dashboard-grid"><section class="card"><div class="card-head"><h2>Các đội tham gia</h2><span class="badge">${state.teams.length} đội</span></div>${tableHtml()}<p class="hint">Xóa đội để giải phóng suất và đăng ký lại. Chỉ áp dụng trước khi bắt đầu nộp bài.</p></section><div class="side-stack"><section class="card"><div class="card-head"><h2>Đăng ký đội</h2><span class="badge ${c.registration_open ? "" : "closed"}">${c.registration_open ? "Đang mở" : "Đang đóng"}</span></div><p>Bạn quyết định thời điểm các đội được tạo tài khoản tham gia giải demo.</p><div class="control-buttons"><button id="open-registration" class="button" ${!canControl() || c.registration_open || state.busy ? "disabled" : ""}>Mở đăng ký</button><button id="close-registration" class="button secondary" ${!canControl() || !c.registration_open || state.busy ? "disabled" : ""}>Đóng đăng ký</button></div><p class="hint">${canControl() ? "Đăng nhập vẫn hoạt động khi đăng ký đóng. Giới hạn đội được kiểm tra bởi hệ thống." : "Đăng ký đã khóa theo giai đoạn của giải."}</p></section>${countCard()}<section class="card"><span class="kicker">Bước tiếp theo</span><p>Nộp Bot, chạy giải và công bố kết quả sẽ được bổ sung sau.</p></section></div></div></section>`);
  document.querySelector("#refresh-admin").addEventListener("click", route);
  document.querySelector("#open-registration").addEventListener("click", () => control(true));
  document.querySelector("#close-registration").addEventListener("click", () => control(false));
  document.querySelectorAll("[data-remove]").forEach(button => button.addEventListener("click", () => {
    state.remove = state.teams.find(t => t.id === Number(button.dataset.remove));
    document.querySelector("#remove-description").textContent = `Bạn đang xóa đội “${state.remove.name}” (#${state.remove.id}) khỏi danh sách tham gia.`;
    document.querySelector("#remove-error").hidden = true;
    dialog.showModal();
    document.querySelector("#cancel-remove").focus();
  }));
}
async function refreshAdmin() {
  const [competition, teams] = await Promise.all([api("/api/competition"), api("/api/teams")]);
  state.competition = competition; state.teams = teams;
}
async function control(open) {
  if (state.busy) return;
  state.busy = true; renderAdmin();
  try {
    await api("/api/admin/registration", {method: "PUT", body: {open}, authenticated: true});
    await refreshAdmin();
    toast(open ? "Đã mở đăng ký đội." : "Đã đóng đăng ký đội.");
  } catch (error) { if (error.status !== 401) toast(error.message, true); }
  finally { state.busy = false; if (location.pathname === "/demo/quan-tri" && state.user?.account_type === "ADMIN") renderAdmin(); }
}
document.querySelector("#cancel-remove").addEventListener("click", () => dialog.close());
dialog.addEventListener("cancel", event => { if (state.busy) event.preventDefault(); });
document.querySelector("#confirm-remove").addEventListener("click", async () => {
  if (state.busy || !state.remove) return;
  const target = state.remove;
  const button = document.querySelector("#confirm-remove");
  state.busy = true; button.disabled = true;
  document.querySelector("#cancel-remove").disabled = true;
  try {
    await api(`/api/admin/teams/${target.id}`, {method: "DELETE", authenticated: true});
    dialog.close();
    await refreshAdmin();
    toast(`Đã xóa đội ${target.name}. Có thể đăng ký lại tên này.`);
  } catch (error) {
    if (error.status !== 401) {
      const errorBox = document.querySelector("#remove-error");
      errorBox.textContent = error.message; errorBox.hidden = false;
      if (!dialog.open) toast(error.message, true);
    }
  } finally {
    state.busy = false; button.disabled = false;
    document.querySelector("#cancel-remove").disabled = false;
    if (location.pathname === "/demo/quan-tri" && state.user?.account_type === "ADMIN") renderAdmin();
  }
});

// Refresh only visible, stable screens; do not erase a form being edited or a modal.
setInterval(async () => {
  if (document.hidden || state.busy || dialog.open || location.pathname === "/main" || app.getAttribute("aria-busy") === "true") return;
  const revision = state.revision;
  try {
    if (state.user) await api("/api/auth/me", {authenticated: true});
    const competition = await api("/api/competition");
    if (revision !== state.revision) return;
    state.competition = competition;
    if (competition.mode !== "DEMO") { errorScreen("Backend không còn chọn giải demo."); return; }
    if (location.pathname === "/demo/quan-tri") {
      state.teams = await api("/api/teams");
      if (revision === state.revision) renderAdmin();
    } else if (location.pathname === "/demo/doi") {
      renderTeam();
    } else {
      const strip = document.querySelector("#registration-status");
      if (strip) strip.innerHTML = statusHtml();
      if (location.pathname === "/demo/dang-ky") {
        const submit = document.querySelector("#submit-auth");
        if (submit && submit.querySelector("span").textContent !== "Đang xử lý…") submit.disabled = !competition.registration_available;
      }
    }
  } catch { /* Explicit user actions surface errors; polling never shows repeating alerts. */ }
}, 15000);
route();
