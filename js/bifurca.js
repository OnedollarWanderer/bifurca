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
  // Worker上では / がルート。ローカルの file:// では動作しない点に注意。
  function siteRoot() {
    const loc = location.pathname;
    // bifurca/ 配下にデプロイされている場合はそのプレフィックスを返す
    const m = loc.match(/^(\/[^/]+\/)/);
    return (m && m[1] !== '/') ? m[1].replace(/\/$/, '') : '';
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

  // ── メイン処理 ─────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    Promise.all([
      injectComponent('header.site-header, [data-component="header"]', '/components/header.html'),
      injectComponent('footer.site-footer, [data-component="footer"]', '/components/footer.html'),
    ]).then(applyActiveNav);
  });

})();
