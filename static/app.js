/**
 * نظام إدارة عيادة الأسنان - JavaScript
 * Dental Clinic Management System - App JS
 */

/* ═══════════════════════════════════════════════════════════════════
   Utilities
   ═══════════════════════════════════════════════════════════════════ */

/**
 * تنسيق رقم بالفواصل: 300000 → 300,000
 */
function fmtNum(v) {
  v = parseFloat(v);
  if (isNaN(v)) return '—';
  if (v === Math.floor(v)) return Math.floor(v).toLocaleString('en-US');
  return v.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
}

/**
 * تنسيق حقل إدخال المبلغ أثناء الكتابة: يضيف فواصل تلقائياً
 */
function numFmt(el) {
  let raw = el.value.replace(/,/g, '').replace(/[^\d]/g, '');
  if (raw === '') { el.value = ''; return; }
  el.value = parseInt(raw, 10).toLocaleString('en-US');
}

/**
 * إزالة الفواصل وإرجاع القيمة الرقمية من حقل
 */
function rawNum(el) {
  return parseFloat((el.value || '0').replace(/,/g, '')) || 0;
}

/**
 * إرسال طلب POST بـ FormData وإرجاع JSON
 * @param {string} url
 * @param {FormData} formData
 * @returns {Promise<Object>}
 */
async function apiPost(url, formData) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const data = await response.json();
    return data;
  } catch (err) {
    console.error('API Error:', err);
    return { success: false, message: 'حدث خطأ في الاتصال بالخادم' };
  }
}

/**
 * عرض Toast Notification
 * @param {string} message
 * @param {'success'|'error'|'warning'} type
 * @param {number} duration - مدة الظهور بالمللي ثانية
 */
function showToast(message, type = 'success', duration = 3000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = {
    success: 'fas fa-check-circle',
    error:   'fas fa-times-circle',
    warning: 'fas fa-exclamation-triangle'
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<i class="${icons[type] || icons.success}"></i> ${message}`;
  container.appendChild(toast);

  // إزالة التوست بعد المدة المحددة
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-30px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ═══════════════════════════════════════════════════════════════════
   Modals
   ═══════════════════════════════════════════════════════════════════ */

/**
 * فتح Modal
 * @param {string} modalId
 */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('open');
    // منع التمرير خلف الـ Modal
    document.body.style.overflow = 'hidden';
    // التركيز على أول حقل
    setTimeout(() => {
      const first = modal.querySelector('input, select, textarea');
      if (first) first.focus();
    }, 100);
  }
}

/**
 * إغلاق Modal
 * @param {string} modalId
 */
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// إغلاق Modal عند الضغط خارجه
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// إغلاق Modal بـ ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
});

/* ═══════════════════════════════════════════════════════════════════
   Table Search (Client Side)
   ═══════════════════════════════════════════════════════════════════ */

/**
 * البحث في الجدول من جانب العميل (اختياري)
 * @param {string} inputId - معرف حقل البحث
 * @param {string} tableId - معرف الجدول
 */
function filterTable(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;

  input.addEventListener('input', () => {
    const query = input.value.toLowerCase().trim();
    const rows  = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(query) ? '' : 'none';
    });
  });
}

/* ═══════════════════════════════════════════════════════════════════
   Number Formatting
   ═══════════════════════════════════════════════════════════════════ */

/**
 * تنسيق الأرقام بالفاصلة العشرية
 * @param {number} num
 * @returns {string}
 */
function formatCurrency(num) {
  return parseFloat(num || 0).toLocaleString('ar-IQ', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }) + ' د.ع';
}

/* ═══════════════════════════════════════════════════════════════════
   Confirm Delete Helper
   ═══════════════════════════════════════════════════════════════════ */

/**
 * طلب تأكيد قبل الحذف
 * @param {string} name - اسم العنصر المراد حذفه
 * @returns {boolean}
 */
function confirmDelete(name) {
  return confirm(`هل أنت متأكد من حذف "${name}"؟\nلا يمكن التراجع عن هذا الإجراء.`);
}

/* ═══════════════════════════════════════════════════════════════════
   Auto-dismiss Alerts
   ═══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  // إخفاء رسائل Flash بعد 5 ثوانٍ
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.5s ease';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });

  // تفعيل البحث في الجداول إذا وُجد
  filterTable('tableSearch', 'patientsTable');
});
