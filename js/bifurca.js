// bifurca.js — サイト共通スクリプト

document.addEventListener('DOMContentLoaded', () => {
  // アクティブなナビリンクにクラスを付与
  const currentPath = location.pathname.replace(/\/index\.html$/, '/');
  document.querySelectorAll('.site-nav a').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    const norm = href.replace(/\/index\.html$/, '/');
    if (currentPath.endsWith(norm) || (norm !== '/' && currentPath.includes(norm.replace('../', '')))) {
      link.classList.add('active');
    }
  });
});
