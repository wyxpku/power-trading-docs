(function () {
  const sidebar = document.querySelector('aside#sidebar nav.toc-nav');
  const content = document.querySelector('article.reading-content');
  if (!sidebar || !content) return;

  const headingSelectors = ['h2', 'h3', 'h4'];
  const headings = Array.from(content.querySelectorAll(headingSelectors.join(',')));
  if (!headings.length) return;

  function slugify(text) {
    return text
      .trim()
      .toLowerCase()
      .replace(/。|，|、|；|：|“|”|‘|’|【|】|（|）|《|》|·|\/|\\|\?|!|\.|,|\(|\)|\[|\]|\{|\}|:|;|"|'|`|\s+/g, '-')
      .replace(/^-+|-+$/g, '')
      .replace(/--+/g, '-');
  }

  const existingIds = new Set();
  let idCounter = 0;
  headings.forEach((heading) => {
    if (!heading.id) {
      let base = slugify(heading.textContent || `section-${++idCounter}`) || `section-${++idCounter}`;
      let id = base;
      let suffix = 1;
      while (existingIds.has(id) || document.getElementById(id)) {
        id = `${base}-${suffix++}`;
      }
      heading.id = id;
      existingIds.add(id);
    }

    const anchor = document.createElement('a');
    anchor.className = 'heading-anchor';
    anchor.href = `#${heading.id}`;
    anchor.title = '定位到本节';
    anchor.innerHTML = '§';
    heading.appendChild(anchor);
  });

  const navGroup = document.createElement('div');
  navGroup.className = 'section-nav';
  navGroup.innerHTML = `
    <div class="section-nav-title">章节小节导航</div>
    <ul class="toc-list section-list"></ul>
  `;

  const sectionList = navGroup.querySelector('.section-list');
  let lastLevel2Item = null;

  headings.forEach((heading) => {
    const level = Number(heading.tagName.replace('H', ''));
    const link = document.createElement('a');
    link.className = `toc-link level-${level}`;
    link.href = `#${heading.id}`;
    link.textContent = heading.textContent.trim();

    const listItem = document.createElement('li');
    listItem.className = `toc-item section-item level-${level}`;
    listItem.appendChild(link);

    if (level === 2) {
      sectionList.appendChild(listItem);
      lastLevel2Item = listItem;
    } else if (level === 3 && lastLevel2Item) {
      let sublist = lastLevel2Item.querySelector('.subsection-list');
      if (!sublist) {
        sublist = document.createElement('ul');
        sublist.className = 'toc-list subsection-list';
        lastLevel2Item.appendChild(sublist);
      }
      sublist.appendChild(listItem);
    } else {
      sectionList.appendChild(listItem);
    }
  });

  const activeChapter = sidebar.querySelector('.toc-link.active');
  if (activeChapter) {
    const currentGroup = activeChapter.closest('.toc-group');
    if (currentGroup) {
      currentGroup.appendChild(navGroup);
    } else {
      sidebar.appendChild(navGroup);
    }
  } else {
    sidebar.appendChild(navGroup);
  }

  function activateSectionLink() {
    const offset = window.scrollY + 140;
    let current = headings[0];
    for (const heading of headings) {
      if (heading.offsetTop <= offset) {
        current = heading;
      } else {
        break;
      }
    }

    sidebar.querySelectorAll('.section-list .toc-link').forEach((link) => {
      link.classList.toggle('active', link.hash === `#${current.id}`);
    });
  }

  activateSectionLink();
  window.addEventListener('scroll', activateSectionLink);

  window.addEventListener('DOMContentLoaded', () => {
    if (window.location.hash) {
      const target = document.querySelector(window.location.hash);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  });
})();
