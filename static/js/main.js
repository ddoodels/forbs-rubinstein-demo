(() => {
  const body = document.body;
  const header = document.querySelector("[data-header]");
  const bookingForm = document.querySelector("[data-booking-form]");
  const statusNode = document.querySelector("[data-form-status]");
  const lightbox = document.querySelector("[data-lightbox]");
  const lightboxImage = document.querySelector("[data-lightbox-image]");

  const setHeaderState = () => {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 24);
  };

  const formatPhone = (value) => {
    let digits = value.replace(/\D/g, "");
    if (!digits) return "";
    if (digits.startsWith("77") && digits.length > 11) digits = digits.slice(1);
    if (digits[0] === "8") digits = `7${digits.slice(1)}`;
    if (digits[0] !== "7") digits = `7${digits}`;
    digits = digits.slice(0, 11);

    let result = "+7";
    if (digits.length > 1) result += ` (${digits.slice(1, 4)}`;
    if (digits.length >= 4) result += ")";
    if (digits.length > 4) result += ` ${digits.slice(4, 7)}`;
    if (digits.length > 7) result += `-${digits.slice(7, 9)}`;
    if (digits.length > 9) result += `-${digits.slice(9, 11)}`;
    return result;
  };

  const setStatus = (message, type = "") => {
    if (!statusNode) return;
    statusNode.textContent = message;
    statusNode.classList.toggle("is-error", type === "error");
    statusNode.classList.toggle("is-success", type === "success");
  };

  const formatGuestCount = (value) => {
    const count = Number.parseInt(value, 10);
    if (!Number.isFinite(count)) return value;
    const last = count % 10;
    const lastTwo = count % 100;
    if (last === 1 && lastTwo !== 11) return `${count} гость`;
    if (last >= 2 && last <= 4 && (lastTwo < 12 || lastTwo > 14)) return `${count} гостя`;
    return `${count} гостей`;
  };

  const normalizeDate = (value) => {
    const text = String(value || "").trim();
    const dotted = text.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
    if (dotted) return `${dotted[3]}-${dotted[2]}-${dotted[1]}`;
    return text;
  };

  const formatTime = (value) => {
    const digits = String(value || "").replace(/\D/g, "").slice(0, 4);
    if (digits.length <= 2) return digits;
    return `${digits.slice(0, 2)}:${digits.slice(2)}`;
  };

  const serializeForm = (form) => {
    const formData = new FormData(form);
    return {
      name: String(formData.get("name") || "").trim(),
      phone: String(formData.get("phone") || "").trim(),
      date: normalizeDate(formData.get("date")),
      time: String(formData.get("time") || "").trim(),
      guests: String(formData.get("guests") || "").trim(),
      source: String(formData.get("source") || "").trim(),
      comment: String(formData.get("comment") || "").trim(),
      occasion: String(formData.get("occasion") || "").trim(),
      zone: String(formData.get("zone") || "").trim(),
      contact_method: String(formData.get("contact_method") || "").trim(),
      booking_context: String(formData.get("booking_context") || "").trim(),
      consent: formData.get("consent") === "on",
      company: String(formData.get("company") || "").trim()
    };
  };

  const dateValue = (offsetDays = 0) => {
    const value = new Date();
    value.setDate(value.getDate() + offsetDays);
    return value.toISOString().slice(0, 10);
  };

  const displayDate = (isoDate) => {
    const [year, month, day] = isoDate.split("-");
    if (!year || !month || !day) return isoDate;
    return `${day}.${month}.${year}`;
  };

  const submitBooking = async (event) => {
    event.preventDefault();
    if (!bookingForm) return;

    const submitButton = bookingForm.querySelector('button[type="submit"]');
    const payload = serializeForm(bookingForm);

    if (!payload.name || !payload.phone || !payload.date || !payload.time || !payload.guests || !payload.consent) {
      setStatus("Заполните имя, телефон, дату, время, гостей и согласие. После этого отправим заявку.", "error");
      return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Отправляем заявку...";
    setStatus("Передаём заявку администратору...");

    if (window.__FORBS_STATIC_DEMO || window.location.hostname.endsWith("github.io")) {
      bookingForm.reset();
      setStatus("Заявка принята. Администратор скоро свяжется с вами для подтверждения.", "success");
      initBookingDefaults();
      submitButton.disabled = false;
      submitButton.textContent = "Забронировать стол";
      return;
    }

    try {
      const response = await fetch("/api/booking", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const result = await response.json().catch(() => ({}));

      if (!response.ok || !result.ok) {
        throw new Error(result.error || "Не получилось отправить заявку.");
      }

      bookingForm.reset();
      const success = `Заявка отправлена. Администратор скоро подтвердит стол на ${payload.time}. Компания: ${formatGuestCount(payload.guests)}.`;
      setStatus(success, "success");
      initBookingDefaults();
    } catch (error) {
      setStatus("Не получилось отправить заявку. Напишите в Telegram или позвоните, мы быстро поможем.", "error");
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Забронировать стол";
    }
  };

  const initBookingDefaults = () => {
    if (!bookingForm) return;
    const dateInput = bookingForm.querySelector("#date");
    const timeInput = bookingForm.querySelector("#time");
    const guestsInput = bookingForm.querySelector("#guests");
    const occasionInput = bookingForm.querySelector("[data-hidden-occasion]");
    const contactInput = bookingForm.querySelector("[data-hidden-contact]");
    if (dateInput && !dateInput.value) dateInput.value = displayDate(dateValue(0));
    if (timeInput && !timeInput.value) timeInput.value = "20:00";
    if (guestsInput && !guestsInput.value) guestsInput.value = "2";
    if (contactInput && !contactInput.value) contactInput.value = "Позвонить";

    const params = new URLSearchParams(window.location.search);
    const intent = params.get("intent");
    if (occasionInput) occasionInput.value = intent === "early" ? "Кальян 1500 с 17:00 до 20:00" : "";
  };

  const initReveal = () => {
    const items = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      items.forEach((item) => item.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });

    items.forEach((item) => observer.observe(item));
  };

  const initMap = () => {
    const iframe = document.querySelector("[data-map-src]");
    if (!iframe || !("IntersectionObserver" in window)) {
      if (iframe?.dataset.mapSrc) iframe.src = iframe.dataset.mapSrc;
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      iframe.src = iframe.dataset.mapSrc;
      observer.disconnect();
    }, { rootMargin: "360px" });
    observer.observe(iframe);
  };

  const openLightbox = (src, alt) => {
    if (!lightbox || !lightboxImage) return;
    lightboxImage.src = src;
    lightboxImage.alt = alt || "Фото FORBS";
    lightbox.hidden = false;
    body.classList.add("lightbox-open");
  };

  const closeLightbox = () => {
    if (!lightbox || !lightboxImage) return;
    lightbox.hidden = true;
    lightboxImage.src = "";
    body.classList.remove("lightbox-open");
  };

  bookingForm?.addEventListener("submit", submitBooking);

  const phoneInput = document.getElementById("phone");
  phoneInput?.addEventListener("focus", () => {
    if (!phoneInput.value) phoneInput.value = "+7";
  });
  phoneInput?.addEventListener("input", () => {
    phoneInput.value = formatPhone(phoneInput.value);
  });

  const timeInput = document.getElementById("time");
  timeInput?.addEventListener("input", () => {
    timeInput.value = formatTime(timeInput.value);
  });

  document.querySelectorAll("[data-lightbox-src]").forEach((button) => {
    button.addEventListener("click", () => {
      const img = button.querySelector("img");
      openLightbox(button.dataset.lightboxSrc, img?.alt);
    });
  });

  document.querySelector("[data-lightbox-close]")?.addEventListener("click", closeLightbox);
  lightbox?.addEventListener("click", (event) => {
    if (event.target === lightbox) closeLightbox();
  });

  window.addEventListener("scroll", setHeaderState, { passive: true });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeLightbox();
    }
  });

  setHeaderState();
  initReveal();
  initMap();
  initBookingDefaults();
})();
