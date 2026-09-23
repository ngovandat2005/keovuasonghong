document.addEventListener("DOMContentLoaded", function() {
    let form = document.getElementById("changelist-form");
    if (!form) return;

    // Tìm thanh tìm kiếm / lọc để chèn nút
    let searchForm = document.getElementById("changelist-search");
    let targetContainer = null;
    
    if (searchForm && searchForm.parentElement) {
        targetContainer = searchForm.parentElement;
    } else {
        // Fallback
        targetContainer = document.querySelector(".flex.flex-col.flex-wrap.gap-3.mb-4.sm\\:flex-row");
    }

    if (!targetContainer) return;

    // Tạo nút
    let btn = document.createElement("button");
    btn.type = "button";
    btn.innerHTML = '<span class="material-symbols-outlined text-sm mr-2" style="font-size: 18px;">delete</span> Xóa mục đã chọn';
    btn.className = "flex items-center bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-md shadow-sm transition-colors text-sm ml-auto";
    btn.style.display = "none";
    btn.style.marginLeft = "auto";
    
    targetContainer.appendChild(btn);

    function updateBtn() {
        let checkboxes = document.querySelectorAll('input.action-select');
        let anyChecked = Array.from(checkboxes).some(cb => cb.checked);
        if (anyChecked) {
            btn.style.display = "flex";
            // Cố gắng ẩn thanh bên dưới
            let bottomBar = document.querySelector('.group-has-\\[input\\.action-select\\:checked\\]\\:flex');
            if (bottomBar) bottomBar.style.display = 'none';
        } else {
            btn.style.display = "none";
        }
    }

    document.addEventListener('change', function(e) {
        if (e.target && e.target.classList.contains('action-select')) {
            updateBtn();
        }
        if (e.target && e.target.id === 'action-toggle') {
            setTimeout(updateBtn, 50);
        }
    });

    btn.onclick = function() {
        if (!confirm("Bạn có chắc chắn muốn xóa các mục đã chọn?")) return;
        let actionSelect = form.querySelector('select[name="action"]');
        if (actionSelect) {
            actionSelect.value = "delete_selected";
            let goBtn = form.querySelector('button[name="index"]');
            if (goBtn) {
                goBtn.click();
            } else {
                form.submit();
            }
        }
    };
});
