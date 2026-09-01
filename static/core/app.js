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
