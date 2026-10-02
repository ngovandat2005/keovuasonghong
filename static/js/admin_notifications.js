// Chuông thông báo admin: đếm đơn đăng ký đại lý / tư vấn chưa xử lý, tự làm mới mỗi 30 giây
(function () {
    var bell = document.getElementById('shk-bell');
    if (!bell) return;

    var badge = document.getElementById('shk-bell-badge');
    var body = document.getElementById('shk-bell-body');
    var url = bell.dataset.url;
    var GROUPS = [
        { key: 'dealer', label: 'Đăng ký đại lý', list: '/admin/main/dealerregistration/?is_processed__exact=0' },
        { key: 'consultation', label: 'Đăng ký tư vấn', list: '/admin/main/consultationrequest/?is_processed__exact=0' }
    ];

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text) node.textContent = text;
        return node;
    }

    function render(data) {
        badge.textContent = data.total > 99 ? '99+' : data.total;
        badge.hidden = data.total === 0;

        body.textContent = '';
        if (data.total === 0) {
            body.appendChild(el('div', 'shk-bell-empty', 'Không có đăng ký mới'));
            return;
        }

        GROUPS.forEach(function (g) {
            var group = data[g.key];
            if (!group || group.count === 0) return;

            var head = el('a', 'shk-bell-group');
            head.href = g.list;
            head.appendChild(el('span', '', g.label));
            head.appendChild(el('span', 'shk-bell-count', group.count));
            body.appendChild(head);

            group.items.forEach(function (item) {
                var row = el('a', 'shk-bell-item');
                row.href = item.url;
                row.appendChild(el('div', 'shk-bell-item-title', item.title));
                if (item.sub) row.appendChild(el('div', 'shk-bell-item-sub', item.sub));
                row.appendChild(el('div', 'shk-bell-item-time', item.time));
                body.appendChild(row);
            });
        });
    }

    function load() {
        fetch(url, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) { if (data) render(data); })
            .catch(function () { /* mất mạng: giữ nguyên số cũ */ });
    }

    load();
    setInterval(function () { if (!document.hidden) load(); }, 30000);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) load(); });
})();
