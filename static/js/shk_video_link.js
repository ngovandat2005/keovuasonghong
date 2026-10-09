/**
 * Chuyển một đường link video thành HTML để chèn vào nội dung bài viết.
 * Hỗ trợ: YouTube, Vimeo, Facebook video và link file trực tiếp (.mp4/.webm/.ogg/.mov).
 * Trả về chuỗi HTML, hoặc null nếu link không được hỗ trợ.
 */
function shkVideoToHtml(input) {
    var raw = (input || '').trim();
    if (!raw) return null;
    // Người dùng vẫn dán nguyên mã nhúng (<iframe ...>) thì giữ nguyên
    if (raw.charAt(0) === '<') return raw;
    if (!/^https?:\/\//i.test(raw)) raw = 'https://' + raw;

    var url;
    try { url = new URL(raw); } catch (e) { return null; }
    var host = url.hostname.replace(/^www\./, '').replace(/^m\./, '');

    function frame(src) {
        return '<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:16px 0;">' +
            '<iframe src="' + src + '" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" ' +
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen" ' +
            'allowfullscreen loading="lazy"></iframe></div>';
    }

    // YouTube
    var yt = null;
    if (host === 'youtu.be') {
        yt = url.pathname.split('/')[1];
    } else if (host === 'youtube.com' || host === 'music.youtube.com' || host === 'youtube-nocookie.com') {
        if (url.pathname === '/watch') yt = url.searchParams.get('v');
        else {
            var m = url.pathname.match(/^\/(?:embed|shorts|live|v)\/([\w-]{6,})/);
            if (m) yt = m[1];
        }
    }
    if (yt && /^[\w-]{6,}$/.test(yt)) {
        var start = parseInt(url.searchParams.get('t') || url.searchParams.get('start') || '0', 10);
        return '<p>' + frame('https://www.youtube.com/embed/' + yt + (start > 0 ? '?start=' + start : '')) + '</p>';
    }

    // Vimeo
    if (host === 'vimeo.com' || host === 'player.vimeo.com') {
        var vm = url.pathname.match(/(\d{5,})/);
        if (vm) return '<p>' + frame('https://player.vimeo.com/video/' + vm[1]) + '</p>';
    }

    // Facebook video / reel
    if (host === 'fb.watch' || (host === 'facebook.com' && /\/(videos|watch|reel|reels|share\/[vr])/.test(url.pathname))) {
        return '<p>' + frame('https://www.facebook.com/plugins/video.php?show_text=false&href=' + encodeURIComponent(url.href)) + '</p>';
    }

    // File video trực tiếp
    if (/\.(mp4|webm|ogg|mov|m4v)$/i.test(url.pathname)) {
        return '<p><video controls preload="metadata" playsinline style="max-width:100%;height:auto;" src="' + url.href + '"></video></p>';
    }

    return null;
}
