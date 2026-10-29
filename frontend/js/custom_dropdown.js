/**
 * Custom Dropdown Component for Dark Theme
 * Replaces native <select> with accessible custom dropdown
 */

class CustomDropdown {
  constructor(selectElement) {
    this.selectElement = selectElement;
    this.options = Array.from(selectElement.options).map(opt => ({
      value: opt.value,
      text: opt.textContent,
      selected: opt.selected
    }));
    this.selectedIndex = selectElement.selectedIndex;
    this.isOpen = false;
    this.focusedIndex = this.selectedIndex;

    this.createCustomDropdown();
    this.attachEventListeners();
  }

  createCustomDropdown() {
    // Create container
    this.container = document.createElement('div');
    this.container.className = 'custom-dropdown-container';
    this.container.style.cssText = this.selectElement.style.cssText;

    // Create selected display
    this.selected = document.createElement('div');
    this.selected.className = 'custom-dropdown-selected';
    this.selected.setAttribute('tabindex', '0');
    this.selected.setAttribute('role', 'button');
    this.selected.setAttribute('aria-haspopup', 'listbox');
    this.selected.setAttribute('aria-expanded', 'false');

    const selectedText = document.createElement('span');
    selectedText.className = 'custom-dropdown-text';
    selectedText.textContent = this.options[this.selectedIndex].text;

    const arrow = document.createElement('span');
    arrow.className = 'custom-dropdown-arrow';
    arrow.innerHTML = '▼';

    this.selected.appendChild(selectedText);
    this.selected.appendChild(arrow);

    // Create options dropdown
    this.dropdown = document.createElement('div');
    this.dropdown.className = 'custom-dropdown-options';
    this.dropdown.setAttribute('role', 'listbox');
    this.dropdown.style.display = 'none';

    this.options.forEach((option, index) => {
      const optionEl = document.createElement('div');
      optionEl.className = 'custom-dropdown-option';
      optionEl.setAttribute('role', 'option');
      optionEl.setAttribute('data-value', option.value);
      optionEl.setAttribute('data-index', index);
      optionEl.textContent = option.text;

      if (index === this.selectedIndex) {
        optionEl.classList.add('selected');
        optionEl.setAttribute('aria-selected', 'true');
      }

      this.dropdown.appendChild(optionEl);
    });

    this.container.appendChild(this.selected);
    this.container.appendChild(this.dropdown);

    // Replace select with custom dropdown
    this.selectElement.style.display = 'none';
    this.selectElement.parentNode.insertBefore(this.container, this.selectElement);
  }

  attachEventListeners() {
    // Toggle dropdown
    this.selected.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggle();
    });

    // Keyboard navigation on selected
    this.selected.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.toggle();
      } else if (e.key === 'ArrowDown' && !this.isOpen) {
        e.preventDefault();
        this.open();
      } else if (e.key === 'ArrowUp' && !this.isOpen) {
        e.preventDefault();
        this.open();
      }
    });

    // Option selection
    this.dropdown.addEventListener('click', (e) => {
      const option = e.target.closest('.custom-dropdown-option');
      if (option) {
        const index = parseInt(option.getAttribute('data-index'), 10);
        this.selectOption(index);
      }
    });

    // Keyboard navigation in dropdown
    this.dropdown.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.focusNext();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.focusPrevious();
      } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.selectOption(this.focusedIndex);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        this.close();
        this.selected.focus();
      }
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
      if (!this.container.contains(e.target)) {
        this.close();
      }
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
        this.selected.focus();
      }
    });
  }

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    this.isOpen = true;
    this.dropdown.style.display = 'block';
    this.selected.setAttribute('aria-expanded', 'true');
    this.selected.classList.add('open');

    // Position dropdown
    const rect = this.container.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const dropdownHeight = this.dropdown.offsetHeight;

    if (spaceBelow < dropdownHeight && rect.top > dropdownHeight) {
      // Open upward
      this.dropdown.style.bottom = '100%';
      this.dropdown.style.top = 'auto';
      this.dropdown.classList.add('open-upward');
    } else {
      // Open downward (default)
      this.dropdown.style.top = '100%';
      this.dropdown.style.bottom = 'auto';
      this.dropdown.classList.remove('open-upward');
    }

    // Focus current option
    this.focusOption(this.selectedIndex);
  }

  close() {
    this.isOpen = false;
    this.dropdown.style.display = 'none';
    this.selected.setAttribute('aria-expanded', 'false');
    this.selected.classList.remove('open');
  }

  selectOption(index) {
    if (index < 0 || index >= this.options.length) return;

    // Update selected index
    const oldIndex = this.selectedIndex;
    this.selectedIndex = index;
    this.focusedIndex = index;

    // Update UI
    this.selected.querySelector('.custom-dropdown-text').textContent = this.options[index].text;

    // Update option classes
    const options = this.dropdown.querySelectorAll('.custom-dropdown-option');
    options[oldIndex].classList.remove('selected');
    options[oldIndex].setAttribute('aria-selected', 'false');
    options[index].classList.add('selected');
    options[index].setAttribute('aria-selected', 'true');

    // Update native select
    this.selectElement.selectedIndex = index;

    // Trigger change event on native select
    const event = new Event('change', { bubbles: true });
    this.selectElement.dispatchEvent(event);

    // Close dropdown
    this.close();
    this.selected.focus();
  }

  focusOption(index) {
    if (index < 0 || index >= this.options.length) return;

    this.focusedIndex = index;
    const options = this.dropdown.querySelectorAll('.custom-dropdown-option');

    // Remove focus from all
    options.forEach(opt => opt.classList.remove('focused'));

    // Add focus to target
    options[index].classList.add('focused');

    // Scroll into view
    options[index].scrollIntoView({ block: 'nearest' });
  }

  focusNext() {
    const nextIndex = Math.min(this.focusedIndex + 1, this.options.length - 1);
    this.focusOption(nextIndex);
  }

  focusPrevious() {
    const prevIndex = Math.max(this.focusedIndex - 1, 0);
    this.focusOption(prevIndex);
  }

  destroy() {
    this.container.remove();
    this.selectElement.style.display = '';
  }
}

// Auto-initialize all selects with data-custom-dropdown attribute
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('select[data-custom-dropdown]').forEach(select => {
    new CustomDropdown(select);
  });
});

window.CustomDropdown = CustomDropdown;
