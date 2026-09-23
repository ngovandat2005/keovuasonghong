// Căn cho dòng "MORTAR" có chiều rộng bằng đúng dòng "SHK" phía trên bằng cách
// tính lại letter-spacing động (kích thước chữ hai dòng đã được đặt bằng nhau trong CSS).
(function () {
    function alignBrandWidths() {
        document.querySelectorAll('.shk-admin-brand-wrap').forEach(function (wrap) {
            var main = wrap.querySelector('.shk-admin-brand-main');
            var sub = wrap.querySelector('.shk-admin-brand-sub');
            if (!main || !sub) return;

            sub.style.letterSpacing = '0px';
            var mainWidth = main.getBoundingClientRect().width;
            var subWidth = sub.getBoundingClientRect().width;
            var charCount = (sub.textContent || '').trim().length;

            if (mainWidth > 0 && subWidth > 0 && charCount > 1) {
                var extraPerGap = (mainWidth - subWidth) / (charCount - 1);
                sub.style.letterSpacing = extraPerGap + 'px';
            }
        });
    }

    document.addEventListener('DOMContentLoaded', alignBrandWidths);
    window.addEventListener('resize', alignBrandWidths);
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(alignBrandWidths);
    }
})();
