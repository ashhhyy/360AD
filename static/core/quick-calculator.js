document.addEventListener("DOMContentLoaded", () => {
  const section = document.querySelector(".quick-calculator");
  if (!section) return;

  const form = document.getElementById("qc-form");
  const product = document.getElementById("qc-product");
  const vatInput = document.getElementById("qc-vat");
  const itemsBody = document.getElementById("qc-items");
  const errorBox = document.getElementById("qc-error");
  const submitButton = form.querySelector('button[type="submit"]');
  let estimateItems = [];

  const value = (id, fallback = "0") => {
    const raw = document.getElementById(id).value.trim();
    return raw === "" ? fallback : raw;
  };
  const number = (id) => Number(value(id, "0")) || 0;
  const money = (amount) =>
    new Intl.NumberFormat("en-PH", { style: "currency", currency: "PHP" }).format(amount || 0);

  const setError = (message = "") => {
    errorBox.textContent = message;
    errorBox.hidden = !message;
  };

  const updateDimensionFields = () => {
    const option = product.selectedOptions[0];
    const isArea = option && option.dataset.pricingType === "AREA";
    section.querySelectorAll(".qc-dimension").forEach((field) => {
      field.classList.toggle("qc-hidden", !isArea);
    });
  };

  const appendCell = (row, text, className = "") => {
    const cell = document.createElement("td");
    cell.textContent = text;
    if (className) cell.className = className;
    row.appendChild(cell);
    return cell;
  };

  const renderEstimate = () => {
    itemsBody.replaceChildren();
    if (!estimateItems.length) {
      const row = document.createElement("tr");
      row.className = "qc-empty-row";
      const cell = appendCell(row, "No quick-estimate items yet.", "empty");
      cell.colSpan = 6;
      itemsBody.appendChild(row);
    } else {
      estimateItems.forEach((item, index) => {
        const row = document.createElement("tr");
        const itemCell = appendCell(row, item.product);
        const strong = document.createElement("strong");
        strong.textContent = item.product;
        itemCell.replaceChildren(strong);
        if (item.description) {
          const description = document.createElement("div");
          description.className = "muted";
          description.textContent = item.description;
          itemCell.appendChild(description);
        }
        appendCell(row, item.detail);
        appendCell(row, money(item.cost_total));
        appendCell(row, money(item.selling_total));
        appendCell(row, `${money(item.gross_profit)} (${item.gp_margin.toFixed(2)}%)`);
        const actionCell = document.createElement("td");
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "link-button danger-link qc-remove";
        remove.textContent = "Remove";
        remove.addEventListener("click", () => {
          estimateItems.splice(index, 1);
          renderEstimate();
        });
        actionCell.appendChild(remove);
        row.appendChild(actionCell);
        itemsBody.appendChild(row);
      });
    }

    const totalCost = estimateItems.reduce((sum, item) => sum + item.cost_total, 0);
    const subtotal = estimateItems.reduce((sum, item) => sum + item.selling_total, 0);
    const profit = subtotal - totalCost;
    const margin = subtotal ? (profit / subtotal) * 100 : 0;
    const vatAmount = subtotal * (number("qc-vat") / 100);
    document.getElementById("qc-total-cost").textContent = money(totalCost);
    document.getElementById("qc-subtotal").textContent = money(subtotal);
    document.getElementById("qc-profit").textContent = money(profit);
    document.getElementById("qc-margin").textContent = `${margin.toFixed(2)}% GP margin`;
    document.getElementById("qc-grand-total").textContent = money(subtotal + vatAmount);
    document.getElementById("qc-vat-amount").textContent = `VAT: ${money(vatAmount)}`;
  };

  product.addEventListener("change", updateDimensionFields);
  vatInput.addEventListener("input", renderEstimate);
  document.getElementById("qc-clear").addEventListener("click", () => {
    estimateItems = [];
    setError();
    renderEstimate();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setError();
    if (!product.value) {
      setError("Please select a product.");
      return;
    }
    const selected = product.selectedOptions[0];
    const isArea = selected.dataset.pricingType === "AREA";
    const quantity = number("qc-quantity");
    if (quantity <= 0) {
      setError("Quantity must be greater than zero.");
      return;
    }
    if (isArea && (number("qc-width") <= 0 || number("qc-height") <= 0)) {
      setError("Width and height are required for area-based products.");
      return;
    }

    const payload = {
      product_id: product.value,
      customer_type: document.getElementById("qc-customer-type").value,
      width: value("qc-width"),
      height: value("qc-height"),
      unit: document.getElementById("qc-unit").value,
      quantity: value("qc-quantity", "1"),
      extra_cost: value("qc-extra-cost"),
      other_charges: value("qc-other-charges"),
      discount: value("qc-discount"),
      selling_price_override: document.getElementById("qc-override").value.trim(),
    };
    submitButton.disabled = true;
    submitButton.textContent = "Calculating...";
    try {
      const response = await fetch(section.dataset.previewUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": form.querySelector('[name="csrfmiddlewaretoken"]').value,
        },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "The estimate could not be calculated.");

      const dimensions = isArea
        ? `${value("qc-width")} × ${value("qc-height")} ${document.getElementById("qc-unit").selectedOptions[0].textContent.toLowerCase()}`
        : "Per piece";
      estimateItems.push({
        ...result,
        description: document.getElementById("qc-description").value.trim(),
        detail: `${dimensions} · Qty ${value("qc-quantity", "1")} · Rate ${money(result.selling_rate)}`,
      });
      renderEstimate();
      document.getElementById("qc-description").value = "";
      document.getElementById("qc-width").value = "";
      document.getElementById("qc-height").value = "";
      document.getElementById("qc-quantity").value = "1";
      document.getElementById("qc-extra-cost").value = "0";
      document.getElementById("qc-other-charges").value = "0";
      document.getElementById("qc-discount").value = "0";
      document.getElementById("qc-override").value = "";
    } catch (error) {
      setError(error.message);
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Calculate & Add Item";
    }
  });

  updateDimensionFields();
  renderEstimate();
});
