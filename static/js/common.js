async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || '请求失败');
  }
  return res.json();
}

function qs(id) {
  return document.getElementById(id);
}

function formToJson(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function alertMsg(msg) {
  window.alert(msg);
}

function formatMoney(v) {
  const n = Number(v || 0);
  return `¥${n.toFixed(2)}`;
}

function navHtml(active) {
  const items = [
    ['/', '首页'],
    ['/customers', '客户管理'],
    ['/rent', '租金收缴'],
    ['/parking', '停车管理'],
    ['/repairs', '报修管理'],
  ];
  return `
    <div class="navbar">
      <div><strong>德汇创新中心物业管理系统</strong></div>
      <div class="nav-links">
        ${items.map(([href, text]) => `<a class="${active === href ? 'active' : ''}" href="${href}">${text}</a>`).join('')}
      </div>
    </div>
  `;
}
