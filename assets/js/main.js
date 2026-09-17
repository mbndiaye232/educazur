/* Groupe Scolaire Educazur — interactions du site */
(function () {
  'use strict';

  /* --- Menu mobile ------------------------------------------------------- */
  var burger = document.querySelector('.burger');
  var nav = document.querySelector('.nav');

  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = burger.getAttribute('aria-expanded') === 'true';
      burger.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('is-open', !open);
    });

    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) {
        burger.setAttribute('aria-expanded', 'false');
        nav.classList.remove('is-open');
      }
    });
  }

  /* --- Ombre de l'en-tête au défilement --------------------------------- */
  var header = document.querySelector('.header');

  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-stuck', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* --- Apparition des blocs au défilement ------------------------------- */
  var revealables = document.querySelectorAll('.reveal');

  if (revealables.length) {
    if (!('IntersectionObserver' in window)) {
      revealables.forEach(function (el) { el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in');
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

      revealables.forEach(function (el) { io.observe(el); });
    }
  }

  /* --- Barres de progression des taux ----------------------------------- */
  var bars = document.querySelectorAll('.rate__bar i[data-rate]');

  if (bars.length) {
    var fill = function (bar) {
      bar.style.transition = 'width 1.1s cubic-bezier(.2,.7,.3,1)';
      bar.style.width = Math.min(100, parseFloat(bar.dataset.rate)) + '%';
    };

    if (!('IntersectionObserver' in window)) {
      bars.forEach(fill);
    } else {
      var barObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            fill(entry.target);
            barObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.3 });

      bars.forEach(function (bar) {
        bar.style.width = '0%';
        barObserver.observe(bar);
      });
    }
  }

  /* --- Visionneuse de la galerie ---------------------------------------- */
  var items = Array.prototype.slice.call(
    document.querySelectorAll('.gallery__item, .doccard'));

  if (items.length) {
    var box = document.createElement('div');
    box.className = 'lightbox';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'Visionneuse de photos');
    box.innerHTML =
      '<button class="lightbox__btn lightbox__close" type="button" aria-label="Fermer">&times;</button>' +
      '<button class="lightbox__btn lightbox__prev" type="button" aria-label="Photo précédente">&#8249;</button>' +
      '<button class="lightbox__btn lightbox__next" type="button" aria-label="Photo suivante">&#8250;</button>' +
      '<div><img alt=""><p class="lightbox__cap"></p></div>';
    document.body.appendChild(box);

    var bigImg = box.querySelector('img');
    var cap = box.querySelector('.lightbox__cap');
    var current = 0;
    var opener = null;

    var show = function (i) {
      current = (i + items.length) % items.length;
      var src = items[current].querySelector('img');
      var text = items[current].querySelector('figcaption');
      // data-full pointe la version pleine résolution quand la vignette est réduite
      bigImg.src = src.dataset.full || src.currentSrc || src.src;
      bigImg.alt = src.alt || '';
      cap.textContent = text ? text.textContent.trim() : '';
    };

    var open = function (i) {
      opener = document.activeElement;
      show(i);
      box.classList.add('is-open');
      document.body.classList.add('no-scroll');
      box.querySelector('.lightbox__close').focus();
    };

    var close = function () {
      box.classList.remove('is-open');
      document.body.classList.remove('no-scroll');
      if (opener && opener.focus) { opener.focus(); }
    };

    items.forEach(function (item, i) {
      item.addEventListener('click', function () { open(i); });
    });

    box.querySelector('.lightbox__close').addEventListener('click', close);
    box.querySelector('.lightbox__prev').addEventListener('click', function () { show(current - 1); });
    box.querySelector('.lightbox__next').addEventListener('click', function () { show(current + 1); });

    box.addEventListener('click', function (e) {
      if (e.target === box) { close(); }
    });

    document.addEventListener('keydown', function (e) {
      if (!box.classList.contains('is-open')) { return; }
      if (e.key === 'Escape') { close(); }
      if (e.key === 'ArrowLeft') { show(current - 1); }
      if (e.key === 'ArrowRight') { show(current + 1); }
    });
  }

  /* --- Formulaire (envoi via Web3Forms, sans rechargement de page) ------- */
  var form = document.querySelector('form[data-ajax-form]');

  if (form) {
    var status = form.querySelector('.form-status');
    var submit = form.querySelector('button[type="submit"]');
    var submitLabel = submit ? submit.textContent : '';

    var say = function (msg, ok) {
      if (!status) { return; }
      status.textContent = msg;
      status.className = 'form-status is-visible ' + (ok ? 'is-ok' : 'is-error');
    };

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      if (!form.reportValidity()) { return; }

      var key = form.querySelector('input[name="access_key"]');

      if (!key || !key.value || key.value.indexOf('VOTRE_CLE') === 0) {
        say('Le formulaire n’est pas encore relié à sa boîte de réception. '
          + 'En attendant, appelez le 77 657 42 31 — nous répondons directement.', false);
        return;
      }

      if (submit) { submit.disabled = true; submit.textContent = 'Envoi en cours…'; }

      fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(Object.fromEntries(new FormData(form)))
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success) {
            form.reset();
            say('Merci, votre demande est bien arrivée. Le secrétariat vous rappelle sous 48 heures ouvrées.', true);
          } else {
            say('L’envoi a échoué. Merci d’appeler le 77 657 42 31.', false);
          }
        })
        .catch(function () {
          say('Connexion impossible. Vérifiez votre réseau ou appelez le 77 657 42 31.', false);
        })
        .then(function () {
          if (submit) { submit.disabled = false; submit.textContent = submitLabel; }
        });
    });
  }

  /* --- Année courante dans le pied de page ------------------------------ */
  var year = document.querySelector('[data-year]');
  if (year) { year.textContent = String(new Date().getFullYear()); }
})();
