(() => {
  const root = document.documentElement;
  const body = document.body;
  const status = document.querySelector("[data-accessibility-status]");

  const announce = (message) => {
    if (!status) return;
    status.textContent = "";
    window.setTimeout(() => { status.textContent = message; }, 30);
  };

  const savedFont = localStorage.getItem("amparo-font-size");
  const initialFont = savedFont || (body.classList.contains("large-text") ? "large" : "normal");
  if (initialFont !== "normal") root.dataset.fontSize = initialFont;
  body.dataset.fontReady = "true";

  const fontLabels = {
    normal: "Tamanho de texto normal",
    large: "Texto grande ativado",
    extra: "Texto muito grande ativado",
  };
  const fontOrder = ["normal", "large", "extra"];

  const updateFontButtons = (size) => {
    document.querySelectorAll("[data-font-toggle]").forEach((button) => {
      button.setAttribute("aria-pressed", size === "normal" ? "false" : "true");
      button.setAttribute("aria-label", `${fontLabels[size]}. Pressione para aumentar novamente.`);
      button.title = fontLabels[size];
    });
  };
  updateFontButtons(initialFont);

  document.querySelectorAll("[data-font-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const current = root.dataset.fontSize || "normal";
      const next = fontOrder[(fontOrder.indexOf(current) + 1) % fontOrder.length];
      if (next === "normal") delete root.dataset.fontSize;
      else root.dataset.fontSize = next;
      localStorage.setItem("amparo-font-size", next);
      updateFontButtons(next);
      announce(fontLabels[next]);
    });
  });

  document.querySelectorAll("form").forEach((form) => {
    const largeTextPreference = form.querySelector("#id_large_text");
    if (!largeTextPreference) return;
    form.addEventListener("submit", () => {
      const size = largeTextPreference.checked ? "large" : "normal";
      localStorage.setItem("amparo-font-size", size);
    });
  });

  const savedContrast = localStorage.getItem("amparo-contrast") === "high";
  if (savedContrast) root.dataset.contrast = "high";
  const updateContrastButtons = (active) => {
    document.querySelectorAll("[data-contrast-toggle]").forEach((button) => {
      button.setAttribute("aria-pressed", String(active));
      button.setAttribute("aria-label", active ? "Desativar alto contraste" : "Ativar alto contraste");
    });
  };
  updateContrastButtons(savedContrast);

  document.querySelectorAll("[data-contrast-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const active = root.dataset.contrast !== "high";
      if (active) root.dataset.contrast = "high";
      else delete root.dataset.contrast;
      localStorage.setItem("amparo-contrast", active ? "high" : "normal");
      updateContrastButtons(active);
      announce(active ? "Alto contraste ativado" : "Contraste padrão ativado");
    });
  });

  const menu = document.querySelector("#more-menu");
  const menuOpen = document.querySelector("[data-menu-open]");
  const menuClose = document.querySelector("[data-menu-close]");
  if (menu && menuOpen && menuClose) {
    menuOpen.addEventListener("click", () => menu.showModal());
    menuClose.addEventListener("click", () => menu.close());
    menu.addEventListener("click", (event) => {
      if (event.target === menu) menu.close();
    });
    menu.addEventListener("close", () => menuOpen.focus());
  }

  document.querySelectorAll("[data-single-submit]").forEach((form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector("button[type='submit']");
      if (!button) return;
      button.disabled = true;
      button.textContent = "Processando com segurança…";
    });
  });

  const chat = document.querySelector(".chat-messages");
  if (chat) chat.scrollTop = chat.scrollHeight;

  window.setTimeout(() => {
    document.querySelectorAll(".flash").forEach((message) => message.remove());
  }, 7000);

  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js"));
  }
})();
