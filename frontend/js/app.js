/**
 * Main Application Controller for SysPilot.
 * Coordinates UI tabs, modal dialogues, toasts, and subsystem lifecycles.
 */

class App {
  constructor() {
    this.initTabs();
    this.initModals();
    this.toastContainer = document.getElementById("toast-container");
    
    // Connect WebSocket
    window.telemetryWs.connect();
    console.log("SysPilot OS Platform Initialized.");
  }

  initTabs() {
    const tabBtns = document.querySelectorAll("#nav-tabs-container .tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetTabId = btn.getAttribute("data-tab");

        // Update buttons
        tabBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        // Switch panes
        tabPanes.forEach(p => {
          if (p.id === targetTabId) {
            p.classList.add("active");
          } else {
            p.classList.remove("active");
          }
        });
      });
    });
  }

  initModals() {
    // Close button click handlers
    document.querySelectorAll(".close-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-close");
        this.closeModal(targetId);
      });
    });

    // Close on backdrop click
    document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
      backdrop.addEventListener("click", (e) => {
        if (e.target === backdrop) {
          backdrop.classList.remove("open");
        }
      });
    });
  }

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("open");
  }

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("open");
  }

  showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let icon = "ℹ️";
    if (type === "success") icon = "✅";
    else if (type === "error") icon = "❌";

    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    this.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(50px)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
}

window.app = new App();
