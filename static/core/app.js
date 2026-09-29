document.addEventListener("DOMContentLoaded", () => {
  const normalize = (value) => value.toLocaleLowerCase().trim();

  document.querySelectorAll("select.form-control").forEach((select) => {
    if (select.disabled || select.dataset.searchReady === "true") return;
    select.dataset.searchReady = "true";

    const options = Array.from(select.options).filter((option) => option.value);
    const selected = options.find((option) => option.selected);
    const wrapper = document.createElement("div");
    const input = document.createElement("input");
    const menu = document.createElement("div");
    const fieldLabel = document.querySelector(`label[for="${select.id}"]`);

    wrapper.className = "search-select";
    input.className = "form-control search-select-input";
    input.type = "text";
    input.id = `${select.id}_search`;
    input.autocomplete = "off";
    input.spellcheck = false;
    input.placeholder = `Type to search ${fieldLabel ? fieldLabel.textContent.trim().toLowerCase() : "options"}...`;
    input.value = selected ? selected.textContent.trim() : "";
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-expanded", "false");
    input.setAttribute("aria-autocomplete", "list");
    menu.className = "search-select-menu";
    menu.id = `${select.id}_suggestions`;
    menu.setAttribute("role", "listbox");
    input.setAttribute("aria-controls", menu.id);

    if (fieldLabel) fieldLabel.htmlFor = input.id;

    if (select.required) {
      input.required = true;
      select.required = false;
    }

    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);
    wrapper.appendChild(input);
    wrapper.appendChild(menu);
    select.classList.add("search-select-native");
    select.tabIndex = -1;

    let visibleOptions = [];
    let activeIndex = -1;

    const closeMenu = () => {
      menu.classList.remove("open");
      input.setAttribute("aria-expanded", "false");
      activeIndex = -1;
    };

    const choose = (option) => {
      select.value = option.value;
      input.value = option.textContent.trim();
      input.setCustomValidity("");
      select.dispatchEvent(new Event("change", { bubbles: true }));
      closeMenu();
    };

    const setActive = (index) => {
      if (!visibleOptions.length) return;
      activeIndex = Math.max(0, Math.min(index, visibleOptions.length - 1));
      visibleOptions.forEach((button, buttonIndex) => {
        button.classList.toggle("active", buttonIndex === activeIndex);
      });
      visibleOptions[activeIndex].scrollIntoView({ block: "nearest" });
    };

    const renderOptions = () => {
      const query = normalize(input.value);
      const matches = options.filter((option) => normalize(option.textContent).includes(query));
      menu.replaceChildren();
      visibleOptions = [];

      matches.forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "search-select-option";
        button.textContent = option.textContent.trim();
        button.setAttribute("role", "option");
        button.addEventListener("mousedown", (event) => {
          event.preventDefault();
          choose(option);
        });
        menu.appendChild(button);
        visibleOptions.push(button);
      });

      if (!matches.length) {
        const empty = document.createElement("div");
        empty.className = "search-select-empty";
        empty.textContent = "No matching suggestion";
        menu.appendChild(empty);
      }

      menu.classList.add("open");
      input.setAttribute("aria-expanded", "true");
    };

    input.addEventListener("focus", renderOptions);
    input.addEventListener("input", () => {
      const exact = options.find(
        (option) => normalize(option.textContent) === normalize(input.value)
      );
      select.value = exact ? exact.value : "";
      input.setCustomValidity(
        input.value.trim() && !exact ? "Please choose one of the matching suggestions." : ""
      );
      renderOptions();
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        if (!menu.classList.contains("open")) renderOptions();
        setActive(activeIndex + 1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActive(activeIndex <= 0 ? visibleOptions.length - 1 : activeIndex - 1);
      } else if (event.key === "Enter" && activeIndex >= 0) {
        event.preventDefault();
        visibleOptions[activeIndex].dispatchEvent(new MouseEvent("mousedown"));
      } else if (event.key === "Escape") {
        closeMenu();
      }
    });

    input.addEventListener("blur", () => {
      const exact = options.find(
        (option) => normalize(option.textContent) === normalize(input.value)
      );
      if (exact) choose(exact);
      else if (!input.value.trim()) select.value = "";
      window.setTimeout(closeMenu, 100);
    });

    const form = select.closest("form");
    if (form) {
      form.addEventListener("submit", () => {
        if (input.required && !select.value) {
          input.setCustomValidity("Please choose one of the matching suggestions.");
        }
      });
      form.addEventListener("reset", () => {
        window.setTimeout(() => {
          const resetOption = Array.from(select.options).find((option) => option.selected);
          input.value = resetOption && resetOption.value ? resetOption.textContent.trim() : "";
        });
      });
    }
  });

  document.addEventListener("click", (event) => {
    document.querySelectorAll(".search-select-menu.open").forEach((menu) => {
      if (!menu.parentElement.contains(event.target)) {
        menu.classList.remove("open");
        menu.parentElement.querySelector(".search-select-input").setAttribute("aria-expanded", "false");
      }
    });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const normalize = (value) => value.toLocaleLowerCase().trim();

  const toggle = document.querySelector("[data-sidebar-toggle]");
  const close = document.querySelector("[data-sidebar-close]");
  if (toggle) {
    const setOpen = (open) => {
      document.body.classList.toggle("nav-open", open);
      toggle.setAttribute("aria-expanded", String(open));
    };
    toggle.addEventListener("click", () => setOpen(!document.body.classList.contains("nav-open")));
    if (close) close.addEventListener("click", () => setOpen(false));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setOpen(false);
    });
  }

  const width = document.querySelector("#id_width");
  const height = document.querySelector("#id_height");
  const unit = document.querySelector("#id_unit");
  if (width && height && unit) {
    const preview = document.createElement("div");
    preview.className = "measurement-preview";
    preview.setAttribute("aria-live", "polite");
    unit.closest(".field")?.appendChild(preview);
    const divisors = { FT: 1, IN: 12, MM: 304.8, CM: 30.48, M: 0.3048 };
    const updatePreview = () => {
      const widthValue = Number.parseFloat(width.value);
      const heightValue = Number.parseFloat(height.value);
      const divisor = divisors[unit.value];
      if (!Number.isFinite(widthValue) || !Number.isFinite(heightValue) || !divisor) {
        preview.textContent = "Enter width and height to preview the equivalent square-foot area.";
        return;
      }
      const area = (widthValue / divisor) * (heightValue / divisor);
      preview.replaceChildren();
      const label = document.createElement("span");
      const result = document.createElement("strong");
      const note = document.createElement("small");
      label.textContent = "Equivalent area";
      result.textContent = `${area.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} sq.ft.`;
      note.textContent = "Uniform per-sq.ft. rates will be used.";
      preview.append(label, result, note);
    };
    width.addEventListener("input", updatePreview);
    height.addEventListener("input", updatePreview);
    unit.addEventListener("change", updatePreview);
    updatePreview();
  }

  document.querySelectorAll("table[data-table]").forEach((table, tableIndex) => {
    const tbody = table.tBodies[0];
    if (!tbody) return;
    const rows = Array.from(tbody.rows).filter((row) => !row.querySelector(".empty"));
    if (!rows.length) return;

    const wrapper = table.closest(".table-wrap");
    if (wrapper && table.dataset.search !== "false") {
      const tools = document.createElement("div");
      const search = document.createElement("input");
      const count = document.createElement("span");
      tools.className = "table-tools";
      search.type = "search";
      search.className = "table-search";
      search.placeholder = table.dataset.searchPlaceholder || "Search this table...";
      search.setAttribute("aria-label", search.placeholder);
      count.className = "table-count";
      tools.append(search, count);
      wrapper.parentNode.insertBefore(tools, wrapper);
      const filterRows = () => {
        const query = normalize(search.value);
        let visible = 0;
        rows.forEach((row) => {
          const matches = !query || normalize(row.innerText).includes(query);
          row.hidden = !matches;
          if (matches) visible += 1;
        });
        count.textContent = `${visible} of ${rows.length} record${rows.length === 1 ? "" : "s"}`;
      };
      search.addEventListener("input", filterRows);
      filterRows();
    }

    Array.from(table.tHead?.rows[0]?.cells || []).forEach((header, columnIndex) => {
      if (!header.textContent.trim() || header.dataset.noSort === "true") return;
      const label = header.textContent.trim();
      const button = document.createElement("button");
      const indicator = document.createElement("span");
      button.type = "button";
      button.className = "sort-button";
      indicator.className = "sort-indicator";
      indicator.textContent = "\u2195";
      button.append(document.createTextNode(label), indicator);
      header.replaceChildren(button);
      button.addEventListener("click", () => {
        const direction = header.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
        Array.from(header.parentElement.cells).forEach((cell) => {
          cell.removeAttribute("aria-sort");
          const icon = cell.querySelector(".sort-indicator");
          if (icon) icon.textContent = "\u2195";
        });
        header.setAttribute("aria-sort", direction);
        indicator.textContent = direction === "ascending" ? "\u2191" : "\u2193";
        const sortType = header.dataset.sortType || "text";
        const valueFor = (row) => {
          const cell = row.cells[columnIndex];
          const raw = (cell?.dataset.sortValue || cell?.innerText || "").trim();
          if (sortType === "number") {
            const parsed = Number.parseFloat(raw.replace(/[^0-9.-]/g, ""));
            return Number.isFinite(parsed) ? parsed : Number.NEGATIVE_INFINITY;
          }
          if (sortType === "date") {
            const parsed = Date.parse(raw);
            return Number.isFinite(parsed) ? parsed : 0;
          }
          return raw.toLocaleLowerCase();
        };
        rows.sort((left, right) => {
          const a = valueFor(left);
          const b = valueFor(right);
          const comparison = typeof a === "number" ? a - b : a.localeCompare(b, undefined, { numeric: true });
          return direction === "ascending" ? comparison : -comparison;
        });
        rows.forEach((row) => tbody.appendChild(row));
      });
    });
    if (!table.id) table.id = `data-table-${tableIndex + 1}`;
  });
});
