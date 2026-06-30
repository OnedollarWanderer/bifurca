/**
 * bifurca.js — BIFURCA サイト共通スクリプト
 *
 * 役割:
 *  1. ヘッダー・フッターを components/ から fetch して注入
 *  2. 現在URLに合わせてナビの active クラスを自動付与
 *  3. 将来的な共通処理の追加場所
 *
 * ナビ項目を追加・変更する場合は components/header.html だけを編集してください。
 */

(function () {
  'use strict';

  // ── サイトルートを自動検出 ──────────────────────────────────────
  // Worker上では / がルート。bifurca/ サブフォルダの場合はプレフィックスを返す
  function siteRoot() {
    try {
      const m = location.pathname.match(/^(\/bifurca)(\/|$)/);
      return m ? '/bifurca' : '';
    } catch(e) { return ''; }
  }

  const ROOT = siteRoot(); // 例: '' or '/bifurca'

  // ── コンポーネント注入 ─────────────────────────────────────────
  function injectComponent(selector, componentPath) {
    const placeholder = document.querySelector(selector);
    if (!placeholder) return Promise.resolve();
    return fetch(ROOT + componentPath)
      .then(function (r) {
        if (!r.ok) throw new Error('fetch failed: ' + componentPath);
        return r.text();
      })
      .then(function (html) {
        // outerHTML置換（プレースホルダー要素ごと差し替え）
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        placeholder.replaceWith(tmp.firstElementChild);
      })
      .catch(function (e) {
        console.warn('[bifurca.js]', e.message);
      });
  }

  // ── ナビ active クラス付与 ────────────────────────────────────
  function applyActiveNav() {
    const path = location.pathname.replace(/\/index\.html$/, '/');
    document.querySelectorAll('.site-nav a').forEach(function (link) {
      const href = (link.getAttribute('href') || '').replace(/\/index\.html$/, '/');
      if (!href) return;
      const abs = href.startsWith('/') ? href : '/' + href;
      if (path === abs || (abs.length > 1 && path.startsWith(abs))) {
        link.classList.add('active');
      }
    });
  }

  // ── 画像モーダル ───────────────────────────────────────────────
  function initImageModal() {
    // モーダルDOM生成（一度だけ）
    if (document.getElementById('bf-modal')) return;
    const modal = document.createElement('div');
    modal.id = 'bf-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-label', '画像拡大');
    modal.innerHTML =
      '<div id="bf-modal-backdrop"></div>' +
      '<div id="bf-modal-inner">' +
        '<button id="bf-modal-close" aria-label="閉じる">✕</button>' +
        '<img id="bf-modal-img" src="" alt="">' +
        '<p id="bf-modal-caption"></p>' +
      '</div>';
    document.body.appendChild(modal);

    const style = document.createElement('style');
    style.textContent =
      '#bf-modal{display:none;position:fixed;inset:0;z-index:9000;align-items:center;justify-content:center;}' +
      '#bf-modal.is-open{display:flex;}' +
      '#bf-modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.82);cursor:pointer;}' +
      '#bf-modal-inner{position:relative;z-index:1;max-width:92vw;max-height:92vh;display:flex;flex-direction:column;align-items:center;gap:.75rem;}' +
      '#bf-modal-img{max-width:88vw;max-height:80vh;object-fit:contain;display:block;border:1px solid rgba(255,255,255,.15);}' +
      '#bf-modal-caption{font-family:var(--font-sans,sans-serif);font-size:.72rem;letter-spacing:.1em;color:rgba(255,255,255,.55);margin:0;}' +
      '#bf-modal-close{position:absolute;top:-2rem;right:0;background:none;border:none;color:#fff;font-size:1.25rem;cursor:pointer;line-height:1;padding:.25rem .5rem;opacity:.7;}' +
      '#bf-modal-close:hover{opacity:1;}' +
      '.modal-trigger{cursor:zoom-in;}';
    document.head.appendChild(style);

    function openModal(src, alt) {
      const img = document.getElementById('bf-modal-img');
      const cap = document.getElementById('bf-modal-caption');
      img.src = src;
      img.alt = alt || '';
      cap.textContent = alt || '';
      modal.classList.add('is-open');
      document.body.style.overflow = 'hidden';
    }
    function closeModal() {
      modal.classList.remove('is-open');
      document.body.style.overflow = '';
      document.getElementById('bf-modal-img').src = '';
    }

    document.getElementById('bf-modal-backdrop').addEventListener('click', closeModal);
    document.getElementById('bf-modal-close').addEventListener('click', closeModal);
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') closeModal();
    });

    // .modal-trigger クラスの img をクリックでモーダル表示
    document.addEventListener('click', function(e) {
      const img = e.target.closest('.modal-trigger');
      if (!img) return;
      const src = img.tagName === 'IMG' ? img.src : img.querySelector('img') && img.querySelector('img').src;
      const alt = img.tagName === 'IMG' ? img.alt : (img.querySelector('img') && img.querySelector('img').alt) || '';
      if (src) openModal(src, alt);
    });
  }

  // ── アコーディオン → モーダル変換 ─────────────────────────────
  function convertCharsheetToModal() {
    document.querySelectorAll('.dict-charsheet').forEach(function(block) {
      const btn = block.querySelector('.dict-charsheet-toggle');
      const body = block.querySelector('.dict-charsheet-body');
      const img = body && body.querySelector('img');
      if (!btn || !img) return;

      // アコーディオンをサムネ+クリック拡大に置き換え
      const wrapper = document.createElement('div');
      wrapper.className = 'charsheet-thumb-wrap';
      wrapper.style.cssText = 'margin-top:1rem;';

      const label = document.createElement('p');
      label.className = 'charsheet-label';
      label.style.cssText = 'font-family:var(--font-sans,sans-serif);font-size:.72rem;letter-spacing:.15em;color:var(--muted,#888);margin-bottom:.5rem;';
      label.textContent = '📋 キャラクターシート（クリックで拡大）';

      const thumb = document.createElement('img');
      thumb.src = img.src;
      thumb.alt = img.alt;
      thumb.loading = 'lazy';
      thumb.className = 'modal-trigger';
      thumb.style.cssText = 'width:100%;max-width:480px;display:block;border:1px solid var(--rule,#444);cursor:zoom-in;';

      wrapper.appendChild(label);
      wrapper.appendChild(thumb);
      block.replaceWith(wrapper);
    });
  }

  // ── 民族ページの都市・信仰画像にもモーダルを付与 ──────────────
  function addModalToGalleryImages() {
    document.querySelectorAll('.dict-image-grid img, .dict-image-gallery img, .dict-visual img').forEach(function(img) {
      img.classList.add('modal-trigger');
      img.style.cursor = 'zoom-in';
    });
  }

  // ── メイン処理 ─────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    Promise.all([
      injectComponent('header.site-header, [data-component="header"]', '/components/header.html'),
      injectComponent('footer.site-footer, [data-component="footer"]', '/components/footer.html'),
    ]).then(applyActiveNav);

    initImageModal();
    convertCharsheetToModal();
    addModalToGalleryImages();
  });

})();
