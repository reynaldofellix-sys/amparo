(() => {
  const root = document.documentElement;
  const body = document.body;
  const status = document.querySelector("[data-accessibility-status]");

  const announce = (message) => {
    if (!status) return;
    status.textContent = "";
    window.setTimeout(() => { status.textContent = message; }, 30);
  };

  const fontOrder = ["normal", "large", "extra"];
  const savedFont = localStorage.getItem("amparo-font-size");
  const initialFont = fontOrder.includes(savedFont)
    ? savedFont
    : (body.classList.contains("large-text") ? "large" : "normal");
  if (initialFont === "normal") delete root.dataset.fontSize;
  else root.dataset.fontSize = initialFont;
  body.dataset.fontReady = "true";

  const fontLabels = {
    normal: "Tamanho de texto normal",
    large: "Texto grande ativado",
    extra: "Texto muito grande ativado",
  };
  const updateFontButtons = (size) => {
    const index = fontOrder.indexOf(size);
    document.querySelectorAll("[data-font-decrease]").forEach((button) => {
      button.disabled = index === 0;
      button.setAttribute("aria-label", index === 0 ? "Texto já está no menor tamanho" : "Diminuir tamanho do texto");
    });
    document.querySelectorAll("[data-font-increase]").forEach((button) => {
      button.disabled = index === fontOrder.length - 1;
      button.setAttribute("aria-label", index === fontOrder.length - 1 ? "Texto já está no maior tamanho" : "Aumentar tamanho do texto");
    });
  };

  const setFontSize = (size) => {
    if (size === "normal") delete root.dataset.fontSize;
    else root.dataset.fontSize = size;
    localStorage.setItem("amparo-font-size", size);
    updateFontButtons(size);
    announce(fontLabels[size]);
  };

  const changeFontSize = (direction) => {
    const current = root.dataset.fontSize || "normal";
    const nextIndex = Math.min(fontOrder.length - 1, Math.max(0, fontOrder.indexOf(current) + direction));
    setFontSize(fontOrder[nextIndex]);
  };

  updateFontButtons(initialFont);
  document.querySelectorAll("[data-font-decrease]").forEach((button) => {
    button.addEventListener("click", () => changeFontSize(-1));
  });
  document.querySelectorAll("[data-font-increase]").forEach((button) => {
    button.addEventListener("click", () => changeFontSize(1));
  });

  document.querySelectorAll("form").forEach((form) => {
    const largeTextPreference = form.querySelector("#id_large_text");
    if (!largeTextPreference) return;
    form.addEventListener("submit", () => {
      const size = largeTextPreference.checked ? "large" : "normal";
      localStorage.setItem("amparo-font-size", size);
    });
  });

  const savedTheme = localStorage.getItem("amparo-theme") === "dark" ? "dark" : "light";
  const themeColor = document.querySelector("[data-theme-color]");
  const updateThemeButtons = (theme) => {
    const dark = theme === "dark";
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.setAttribute("aria-pressed", String(dark));
      button.setAttribute("aria-label", dark ? "Ativar modo claro" : "Ativar modo escuro");
      button.title = dark ? "Modo claro" : "Modo escuro";
    });
    if (themeColor) themeColor.content = dark ? "#09131D" : "#0B3B69";
  };

  if (savedTheme === "dark") root.dataset.theme = "dark";
  else delete root.dataset.theme;
  updateThemeButtons(savedTheme);

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      if (next === "dark") root.dataset.theme = "dark";
      else delete root.dataset.theme;
      localStorage.setItem("amparo-theme", next);
      updateThemeButtons(next);
      announce(next === "dark" ? "Modo escuro ativado" : "Modo claro ativado");
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
