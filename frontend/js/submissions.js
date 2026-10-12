import {api} from "/assets/js/api.js";

export function submissionPage(ctx) {
  const {state, escape, setContent, phases} = ctx;
  const c = state.competition;
  const statuses = {PENDING:"Chờ kiểm tra", RUNNING:"Đang kiểm tra", VALID:"Hợp lệ", INVALID:"Không hợp lệ", SYSTEM_ERROR:"Lỗi kiểm tra"};
  const date = value => new Date(value).toLocaleString("vi-VN", {timeZone:"Asia/Ho_Chi_Minh"});
  const limit = (c.submission_max_bytes / 1048576).toLocaleString("vi-VN");
  document.title = "Nộp Bot · BT3 Demo";
  setContent(`<section class="dashboard"><div class="page-heading"><div><span class="kicker">Đội ${escape(state.team.name)}</span><h1>Nộp Bot của đội</h1><p>Mỗi lần nộp được lưu thành một phiên bản riêng.</p></div><a class="button secondary compact" href="/demo/doi" data-link>← Đội của tôi</a></div>${phases()}<div class="dashboard-grid"><section class="card"><div class="card-head"><h2>File Bot</h2><span id="submission-gate-state" class="badge ${c.submission_open ? "" : "closed"}">${c.submission_open ? "Đang mở nộp bài" : "Nộp bài đang đóng"}</span></div><form id="upload-form"><label class="upload-zone" for="bot-file"><span class="upload-icon" aria-hidden="true">↑</span><strong>Chọn file student_bot.py</strong><span>Một file Python, tối đa ${limit} MiB</span><input id="bot-file" name="file" type="file" accept=".py" required ${c.submission_open ? "" : "disabled"}></label><p id="chosen-file" class="hint">Chưa chọn file.</p><p id="upload-error" class="error-message" role="alert" hidden></p><p id="upload-success" class="success-message" role="status" hidden></p><button id="submit-bot" class="button" type="submit" ${c.submission_open ? "" : "disabled"}>Nộp bài →</button></form><p class="muted">Đã nhận file không có nghĩa Bot đã hợp lệ. Bài sẽ chờ Validator/Judge kiểm tra; hệ thống hiện chưa chạy Bot.</p></section><section class="card"><h2>Thời gian nộp</h2>${c.submission_window.mode === "SCHEDULED" ? `<div class="info-rows"><div class="info-row"><span>Mở</span><strong>${escape(date(c.submission_window.opens_at))}</strong></div><div class="info-row"><span>Đóng</span><strong>${escape(date(c.submission_window.closes_at))}</strong></div></div>` : '<p>Ban tổ chức đang điều khiển mở/đóng thủ công.</p>'}<p class="hint">Các mốc hiển thị theo giờ Việt Nam. Backend kiểm tra thời gian nhận đủ file bằng đồng hồ máy chủ.</p></section></div><section class="card submission-history"><div class="card-head"><h2>Lịch sử bài nộp</h2><button id="refresh-submissions" class="button secondary compact">Làm mới ↻</button></div>${state.submissions.length ? `<div class="table-wrap"><table><thead><tr><th>Phiên bản</th><th>Nhận lúc (giờ VN)</th><th>Dung lượng</th><th>Trạng thái</th></tr></thead><tbody>${state.submissions.map(s => `<tr><td><strong>v${s.version}</strong><p class="hint">#${s.id} · student_bot.py</p></td><td>${escape(date(s.received_at))}</td><td>${s.size_bytes == null ? "—" : `${(s.size_bytes/1024).toFixed(1)} KiB`}</td><td><span class="badge ${s.validation_status === "INVALID" ? "closed" : ""}">${escape(statuses[s.validation_status] || s.validation_status)}</span><p class="hint">${escape(s.validation_message || "")}</p></td></tr>`).join("")}</tbody></table></div>` : '<div class="empty">Chưa có bài nộp. Hãy gửi phiên bản đầu tiên khi ban tổ chức mở nộp bài.</div>'}</section></section>`);
  const input = document.querySelector("#bot-file");
  input.addEventListener("change", () => {
    const file = input.files[0];
    document.querySelector("#chosen-file").textContent = file ? `${file.name} · ${(file.size/1024).toFixed(1)} KiB` : "Chưa chọn file.";
  });
  document.querySelector("#refresh-submissions").addEventListener("click", ctx.reload);
  document.querySelector("#upload-form").addEventListener("submit", async event => {
    event.preventDefault();
    if (state.busy) return;
    const file = input.files[0];
    const errorBox = document.querySelector("#upload-error");
    const successBox = document.querySelector("#upload-success");
    errorBox.hidden = true; successBox.hidden = true;
    const fail = message => {errorBox.textContent = message; errorBox.hidden = false;};
    if (!file || file.name !== "student_bot.py") {fail("File phải có tên chính xác student_bot.py."); return;}
    if (!file.size || file.size > c.submission_max_bytes) {fail(`File phải có nội dung và không vượt ${limit} MiB.`); return;}
    state.busy = true;
    const button = document.querySelector("#submit-bot");
    button.disabled = true; button.textContent = "Đang gửi…";
    const body = new FormData(); body.append("file", file);
    try {
      const received = await api("/api/submissions", {method:"POST", body, authenticated:true});
      state.submissions.unshift(received);
      input.value = "";
      submissionPage(ctx);
      const box = document.querySelector("#upload-success");
      box.textContent = `Đã nhận phiên bản v${received.version}. Bài đang chờ kiểm tra.`; box.hidden = false;
      ctx.toast(`Đã nhận Bot phiên bản v${received.version}.`);
    } catch (error) { if (error.status !== 401) fail(error.message); }
    finally {
      state.busy = false;
      const current = document.querySelector("#submit-bot");
      if (current) {current.disabled = !state.competition.submission_open; current.textContent = "Nộp bài →";}
    }
  });
}

export function windowCards(c, escape) {
  function localTime(value) {
    if (!value) return "";
    // Controls explicitly use Vietnam time, independent of browser timezone.
    const d = new Date(new Date(value).getTime() + 7 * 3600000);
    return d.toISOString().slice(0, 19);
  }
  return ["registration", "submission"].map(kind => {
    const w = c[`${kind}_window`];
    const title = kind === "registration" ? "Đăng ký đội" : "Nộp Bot";
    return `<section class="card"><div class="card-head"><h2>${title}</h2><span data-window-status="${kind}" class="badge ${w.open ? "" : "closed"}">${w.open ? "Đang mở" : "Đang đóng"}</span></div><p>${w.mode === "SCHEDULED" ? "Đang tự động mở/đóng theo lịch đã lưu." : "Đang điều khiển thủ công."}</p><div class="control-buttons"><button class="button" data-window="${kind}" data-open="true" ${w.mode === "MANUAL" && w.open ? "disabled" : ""}>Mở ngay</button><button class="button secondary" data-window="${kind}" data-open="false" ${w.mode === "MANUAL" && !w.open ? "disabled" : ""}>Đóng ngay</button></div><details class="schedule-details" ${w.mode === "SCHEDULED" ? "open" : ""}><summary>Hẹn giờ tự động</summary><form class="window-form" data-kind="${kind}"><label for="${kind}-start">Mở lúc · giờ Việt Nam</label><input id="${kind}-start" name="opens_at" type="datetime-local" step="1" required value="${escape(localTime(w.opens_at))}"><label for="${kind}-end">Đóng lúc · giờ Việt Nam</label><input id="${kind}-end" name="closes_at" type="datetime-local" step="1" required value="${escape(localTime(w.closes_at))}"><button type="submit" class="button secondary compact">Lưu lịch</button></form></details><p class="hint">Mở/đóng ngay sẽ thay thế lịch của cửa này. Chỉ một cửa được mở tại một thời điểm. Lịch không được chồng nhau.</p></section>`;
  }).join("");
}
