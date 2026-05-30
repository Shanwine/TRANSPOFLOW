/* Transflow — Customer JS */
'use strict';

document.addEventListener('DOMContentLoaded', () => {

  /* ── Sidebar toggle (mobile) ── */
  const sidebar = document.getElementById('customer-sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle-btn');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) &&
          !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  /* ── Auto-dismiss Django alerts after 4s ── */
  document.querySelectorAll('.tf-alert[data-auto-dismiss]').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity .4s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 4000);
  });

  /* ── Active sidebar link highlight ── */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && currentPath.startsWith(href) && href !== '/') {
      link.classList.add('active');
    }
  });

  /* ── Cancel booking confirmation (SweetAlert) ── */
  document.querySelectorAll('.cancel-booking-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const form = btn.closest('form') || document.getElementById(btn.dataset.formId);
      if (!form) return;
      if (typeof Swal !== 'undefined') {
        Swal.fire({
          title: 'Cancel Booking?',
          text: 'Are you sure you want to cancel this booking? This cannot be undone.',
          icon: 'warning',
          showCancelButton: true,
          confirmButtonColor: '#ef4444',
          cancelButtonColor: '#6366f1',
          confirmButtonText: 'Yes, cancel it!',
          cancelButtonText: 'Keep Booking',
          backdrop: 'rgba(15,23,42,0.6)',
          borderRadius: '12px',
        }).then((result) => {
          if (result.isConfirmed) form.submit();
        });
      } else {
        if (confirm('Are you sure you want to cancel this booking?')) form.submit();
      }
    });
  });

  /* ── Booking success toast ── */
  const bookingSuccess = document.querySelector('[data-booking-success]');
  if (bookingSuccess && typeof Swal !== 'undefined') {
    Swal.fire({
      title: 'Booking Submitted!',
      text: 'Your booking is pending confirmation from our team.',
      icon: 'success',
      timer: 3000,
      timerProgressBar: true,
      showConfirmButton: false,
      toast: false,
      position: 'center',
    });
  }

  /* ── Mark notification read via AJAX ── */
  document.querySelectorAll('.mark-notif-read').forEach(btn => {
    btn.addEventListener('click', () => {
      const notifId = btn.dataset.notifId;
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
      fetch(`/customer/notification/${notifId}/read/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken ? csrfToken.value : '',
          'Content-Type': 'application/json',
        },
      }).then(() => {
        const item = btn.closest('.notif-item');
        if (item) item.style.opacity = '0.4';
        btn.textContent = 'Read';
        btn.disabled = true;
      });
    });
  });

  /* ── Seat count stepper ── */
  const seatInput  = document.getElementById('id_seats');
  const seatMinus  = document.getElementById('seat-minus');
  const seatPlus   = document.getElementById('seat-plus');
  if (seatInput && seatMinus && seatPlus) {
    seatMinus.addEventListener('click', () => {
      const v = parseInt(seatInput.value) || 1;
      if (v > 1) seatInput.value = v - 1;
    });
    seatPlus.addEventListener('click', () => {
      const v = parseInt(seatInput.value) || 1;
      const max = parseInt(seatInput.max) || 50;
      if (v < max) seatInput.value = v + 1;
    });
  }

  /* ── Vehicle search live filter ── */
  const searchInput = document.getElementById('vehicle-search-input');
  const vehicleCards = document.querySelectorAll('.vehicle-card[data-name]');
  if (searchInput && vehicleCards.length) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.toLowerCase();
      vehicleCards.forEach(card => {
        const name = card.dataset.name.toLowerCase();
        card.closest('.vehicle-card-wrapper').style.display = name.includes(q) ? '' : 'none';
      });
    });
  }

});
