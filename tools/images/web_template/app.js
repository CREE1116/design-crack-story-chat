/**
 * 크랙 스토리챗 공식 에셋 갤러리 & 쇼케이스 인터랙티브 스크립트
 * - 인물/장소/몬스터/이벤트 4대 카테고리 탭 탐색
 * - 19+ NSFW 모드 토글 (localStorage 연동)
 * - 실시간 검색, 그룹 필터, 정렬
 * - 캐릭터 상세 인스펙터 모달 & 표정 바리에이션 선택기
 * - 원클릭 프롬프트 마크다운 태그 복사 & 토스트 알림
 */

// 전역 데이터 (deploy.py가 주입하거나 기본 fallback 사용)
const CHARACTERS_DATA = window.CHARACTERS_DATA || [
  { id: "01", name: "에리카 아르덴", group: "student", type: "기사학부 · 1학년", role: "깐깐한 정석파 라이벌", quote: "기본을 무시한 검술은 검술이 아니야.", variants: ["a01", "a02", "a03", "a04", "a05", "a06", "s01", "s02"] },
  { id: "02", name: "테오 아르덴", group: "student", type: "기사학부 · 1학년", role: "호쾌한 전투광", quote: "생각은 나중에. 일단 붙자.", variants: ["a01", "a02", "a03"] },
  { id: "03", name: "셀리아 아르덴", group: "student", type: "기사학부 · 4학년", role: "차가운 완벽주의 선배", quote: "다시. 아직 부족해.", variants: ["a01", "a02", "a03", "s01"] },
  { id: "04", name: "엘리아 벨로아", group: "student", type: "마법학부 · 1학년", role: "나른한 마법 오타쿠", quote: "잠깐. 그 술식 다시 보여줘.", variants: ["a01", "a02", "a03", "s01", "s02"] },
  { id: "05", name: "루시안 벨로아", group: "student", type: "마법학부 · 4학년", role: "오만한 엘리트 선배", quote: "재현된다면 제 평가를 고치죠.", variants: ["a01", "a02"] },
  { id: "06", name: "미라 로젠펠트", group: "student", type: "상업·공통 · 3학년", role: "기술을 가치로 읽는 협상가", quote: "그래서 이 기술의 가치는 얼마일까?", variants: ["a01", "a02", "s01"] }
];

const SCENES_DATA = window.SCENES_DATA || [
  { id: "scene/a01", name: "아카데미 중앙 로비", type: "실내 · 공통", role: "교내 중심 광장", variants: ["a01"] },
  { id: "scene/a02", name: "제1 연무장", type: "훈련장", role: "기사학부 대련장", variants: ["a02"] },
  { id: "scene/a21", name: "고대 술식 연구동", type: "연구소", role: "마법학부 지하 서고", variants: ["a21"] }
];

const MOBS_DATA = window.MOBS_DATA || [
  { id: "mob/a31", name: "마력 골렘 스카우트", type: "연습용 구조체", role: "3급 기계마수", variants: ["a31"] },
  { id: "mob/a32", name: "3급 아머트론", type: "전투형 골렘", role: "실전 평가용 위협", variants: ["a32"] }
];

const EVENTS_DATA = window.EVENTS_DATA || [
  { id: "event/a01", name: "입학 선서식", type: "공식 행사", role: "전체 신입생 집합", variants: ["a01"] },
  { id: "event/s01", name: "비밀 연구실 밀회", type: "19+ 특수 씬", role: "합방 및 서약 이벤트", variants: ["s01"], isNsfw: true }
];

// 상태 관리 객체
const state = {
  currentTab: "characters", // 'characters' | 'scenes' | 'mobs' | 'events'
  currentFilter: "all",
  searchQuery: "",
  sortBy: "id-asc",
  isNsfwMode: localStorage.getItem("crack_nsfw_mode") === "true",
  activeItem: null,
  activeVariant: "a01"
};

// DOM 요소 캐시
const el = {
  grid: document.querySelector("#character-grid"),
  filterContainer: document.querySelector("#filter-container"),
  searchInput: document.querySelector("#search-input"),
  sortSelect: document.querySelector("#sort-select"),
  categoryTabs: document.querySelectorAll(".cat-tab"),
  nsfwToggle: document.querySelector("#nsfw-toggle"),
  emptyState: document.querySelector("#empty-state"),
  statCharacters: document.querySelector("#stat-characters"),
  statAssets: document.querySelector("#stat-assets"),
  toast: document.querySelector("#toast"),
  backToTop: document.querySelector("#back-to-top"),
  // 모달 요소
  modal: document.querySelector("#character-modal"),
  modalBackdrop: document.querySelector("#modal-backdrop"),
  modalClose: document.querySelector("#modal-close"),
  modalImage: document.querySelector("#modal-image"),
  modalId: document.querySelector("#modal-id"),
  modalType: document.querySelector("#modal-type"),
  modalName: document.querySelector("#modal-name"),
  modalRole: document.querySelector("#modal-role"),
  modalQuote: document.querySelector("#modal-quote"),
  modalVariants: document.querySelector("#modal-variants"),
  variantCount: document.querySelector("#variant-count"),
  modalTagInput: document.querySelector("#modal-tag-input"),
  btnCopyInput: document.querySelector("#btn-copy-input"),
  modalCopyTag: document.querySelector("#modal-copy-tag")
};

// 토스트 메시지 띄우기
function showToast(message) {
  if (!el.toast) return;
  el.toast.querySelector(".toast-message").textContent = message;
  el.toast.classList.add("show");
  clearTimeout(el.toast._timer);
  el.toast._timer = setTimeout(() => {
    el.toast.classList.remove("show");
  }, 2200);
}

// 클립보드 복사 유틸
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast(`클립보드 복사 완료: ${text}`);
  } catch (err) {
    showToast(`복사 실패 (직접 복사해주세요): ${text}`);
  }
}

// 현재 탭에 따른 데이터 소스 가져오기
function getCurrentDataset() {
  switch (state.currentTab) {
    case "scenes": return SCENES_DATA;
    case "mobs": return MOBS_DATA;
    case "events": return EVENTS_DATA;
    case "characters":
    default: return CHARACTERS_DATA;
  }
}

// 19+ NSFW 모드 UI 동기화
function syncNsfwToggle() {
  if (!el.nsfwToggle) return;
  el.nsfwToggle.classList.toggle("active", state.isNsfwMode);
  const badge = el.nsfwToggle.querySelector(".nsfw-badge");
  if (badge) {
    badge.textContent = state.isNsfwMode ? "19+ ON" : "SAFE";
  }
}

// 스탯 카운터 갱신
function updateStats() {
  if (el.statCharacters) {
    el.statCharacters.textContent = CHARACTERS_DATA.length;
  }
  if (el.statAssets) {
    let total = 0;
    [CHARACTERS_DATA, SCENES_DATA, MOBS_DATA, EVENTS_DATA].forEach(list => {
      list.forEach(item => {
        total += (item.variants && item.variants.length) || 1;
      });
    });
    el.statAssets.textContent = `${total}+`;
  }
}

// 필터 버튼 렌더링
function renderFilterButtons() {
  if (!el.filterContainer) return;
  const dataset = getCurrentDataset();
  const groups = new Set();
  dataset.forEach(item => {
    if (item.group) groups.add(item.group);
  });

  el.filterContainer.innerHTML = `<button class="filter-pill ${state.currentFilter === 'all' ? 'active' : ''}" type="button" data-filter="all">전체</button>`;
  
  groups.forEach(group => {
    const btn = document.createElement("button");
    btn.className = `filter-pill ${state.currentFilter === group ? 'active' : ''}`;
    btn.type = "button";
    btn.dataset.filter = group;
    btn.textContent = group === "student" ? "학생" : group === "faculty" ? "교수진" : group;
    el.filterContainer.append(btn);
  });

  el.filterContainer.querySelectorAll(".filter-pill").forEach(button => {
    button.addEventListener("click", () => {
      state.currentFilter = button.dataset.filter;
      el.filterContainer.querySelectorAll(".filter-pill").forEach(b => b.classList.toggle("active", b === button));
      renderCards();
    });
  });
}

// 고품격 다크 판타지 SVG 플레이스홀더 생성기 (이미지가 없을 때 자동 표출)
function getPlaceholderSvg(name, id) {
  const initial = (name || id || "?").charAt(0);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="832" height="1216" viewBox="0 0 832 1216">
    <defs>
      <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#1e1633"/>
        <stop offset="50%" stop-color="#120c1f"/>
        <stop offset="100%" stop-color="#08050e"/>
      </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#bg)"/>
    <circle cx="416" cy="480" r="160" fill="rgba(141,92,225,0.12)" stroke="rgba(213,191,255,0.2)" stroke-width="2"/>
    <text x="416" y="535" font-family="'Iowan Old Style', serif" font-size="140" font-weight="bold" fill="#d5bfff" text-anchor="middle">${initial}</text>
    <text x="416" y="710" font-family="sans-serif" font-size="32" font-weight="700" fill="#e2d9f0" text-anchor="middle" letter-spacing="2">${name}</text>
    <text x="416" y="760" font-family="monospace" font-size="22" fill="#8d5ce1" text-anchor="middle">${id}</text>
  </svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

// 카드 렌더링
function renderCards() {
  if (!el.grid) return;
  el.grid.innerHTML = "";

  const dataset = getCurrentDataset();
  const query = state.searchQuery.trim().toLowerCase();

  let items = dataset.filter(item => {
    // 1. 그룹 필터
    if (state.currentFilter !== "all" && item.group !== state.currentFilter) {
      return false;
    }
    // 2. 19+ 필터 (SAFE 모드일 때 19+ 전용 이벤트 숨김)
    if (!state.isNsfwMode && item.isNsfw) {
      return false;
    }
    // 3. 검색어 필터
    if (query) {
      const matchName = item.name && item.name.toLowerCase().includes(query);
      const matchRole = item.role && item.role.toLowerCase().includes(query);
      const matchType = item.type && item.type.toLowerCase().includes(query);
      const matchQuote = item.quote && item.quote.toLowerCase().includes(query);
      const matchId = item.id && item.id.toLowerCase().includes(query);
      if (!matchName && !matchRole && !matchType && !matchQuote && !matchId) {
        return false;
      }
    }
    return true;
  });

  // 정렬
  items.sort((a, b) => {
    if (state.sortBy === "id-asc") return String(a.id).localeCompare(String(b.id), undefined, { numeric: true });
    if (state.sortBy === "id-desc") return String(b.id).localeCompare(String(a.id), undefined, { numeric: true });
    if (state.sortBy === "name-asc") return String(a.name).localeCompare(String(b.name));
    return 0;
  });

  if (items.length === 0) {
    if (el.emptyState) el.emptyState.classList.remove("hidden");
    return;
  }
  if (el.emptyState) el.emptyState.classList.add("hidden");

  items.forEach(item => {
    const card = document.createElement("article");
    card.className = "character-card";
    card.dataset.id = item.id;
    card.dataset.group = item.group || "all";

    // 기본 썸네일 이미지 경로 구성
    let defaultImg;
    if (item.img) {
      defaultImg = item.img.startsWith("/") ? `.${item.img}` : item.img;
    } else if (state.currentTab === "characters") {
      defaultImg = `./${item.id}/a01.webp`;
    } else {
      defaultImg = `./${item.id}.webp`;
    }

    const revision = item.revision ? `?v=${item.revision}` : "";
    const placeholder = getPlaceholderSvg(item.name, item.id);

    card.innerHTML = `
      <img src="${defaultImg}${revision}" alt="${item.name}" loading="lazy" width="832" height="1216" onerror="this.onerror=null; this.src='${placeholder}';">
      <div class="character-overlay">
        <span class="character-number">${item.id}</span>
        <span class="character-type">${item.type || "에셋"}</span>
        <h3>${item.name}</h3>
        <p class="character-role">${item.role || ""}</p>
        ${item.quote ? `<p class="character-quote">“${item.quote}”</p>` : ""}
      </div>`;

    card.addEventListener("click", () => openModal(item));
    el.grid.append(card);
  });
}

// 모달 인스펙터 열기
function openModal(item) {
  state.activeItem = item;
  const variants = item.variants || ["a01"];
  state.activeVariant = variants[0] || "a01";

  if (el.modalId) el.modalId.textContent = item.id;
  if (el.modalName) el.modalName.textContent = item.name;
  if (el.modalType) el.modalType.textContent = item.type || "주요 에셋";
  if (el.modalRole) el.modalRole.textContent = item.role || "";
  
  if (el.modalQuote) {
    if (item.quote) {
      el.modalQuote.textContent = `“${item.quote}”`;
      el.modalQuote.style.display = "block";
    } else {
      el.modalQuote.style.display = "none";
    }
  }

  // 바리에이션 목록 렌더링
  renderModalVariants(item);
  updateModalPreview();

  if (el.modal) el.modal.showModal();
}

// 모달 내 바리에이션 썸네일 그리드 렌더링
function renderModalVariants(item) {
  if (!el.modalVariants) return;
  el.modalVariants.innerHTML = "";

  const variants = item.variants || ["a01"];
  // SAFE 모드일 때 s 접두사 숨김 여부 처리
  const visibleVariants = variants.filter(v => state.isNsfwMode || !v.startsWith("s"));

  if (el.variantCount) {
    el.variantCount.textContent = `${visibleVariants.length}개`;
  }

  visibleVariants.forEach(v => {
    const isNsfw = v.startsWith("s");
    let imgPath;
    if (state.currentTab === "characters") {
      imgPath = `./${item.id}/${v}.webp`;
    } else {
      imgPath = `./${item.id}.webp`;
    }

    const placeholder = getPlaceholderSvg(item.name, v);
    const itemEl = document.createElement("div");
    itemEl.className = `variant-item ${state.activeVariant === v ? 'active' : ''}`;
    itemEl.innerHTML = `
      <img src="${imgPath}" alt="${v}" loading="lazy" onerror="this.onerror=null; this.src='${placeholder}';">
      <span class="variant-badge ${isNsfw ? 'nsfw' : ''}">${v.toUpperCase()}</span>
    `;

    itemEl.addEventListener("click", () => {
      state.activeVariant = v;
      el.modalVariants.querySelectorAll(".variant-item").forEach(el => el.classList.toggle("active", el === itemEl));
      updateModalPreview();
    });

    el.modalVariants.append(itemEl);
  });
}

// 모달 프리뷰 및 마크다운 태그 갱신
function updateModalPreview() {
  if (!state.activeItem) return;
  const item = state.activeItem;
  const v = state.activeVariant;

  let imgPath;
  let markdownTag;
  if (state.currentTab === "characters") {
    imgPath = `./${item.id}/${v}.webp`;
    markdownTag = `![]({IMG}/${item.id}/${v}.webp)`;
  } else {
    imgPath = `./${item.id}.webp`;
    markdownTag = `![]({IMG}/${item.id}.webp)`;
  }

  const placeholder = getPlaceholderSvg(item.name, `${item.id}/${v}`);
  if (el.modalImage) {
    el.modalImage.onerror = () => {
      el.modalImage.onerror = null;
      el.modalImage.src = placeholder;
    };
    el.modalImage.src = imgPath;
    el.modalImage.alt = `${item.name} (${v})`;
  }
  if (el.modalTagInput) {
    el.modalTagInput.value = imgPath;
  }
}

// 모달 닫기
function closeModal() {
  if (el.modal) el.modal.close();
  state.activeItem = null;
}

// 이벤트 리스너 초기화
function initEvents() {
  // 19+ NSFW 모드 토글
  if (el.nsfwToggle) {
    el.nsfwToggle.addEventListener("click", () => {
      state.isNsfwMode = !state.isNsfwMode;
      localStorage.setItem("crack_nsfw_mode", state.isNsfwMode);
      syncNsfwToggle();
      renderCards();
      if (state.activeItem) {
        renderModalVariants(state.activeItem);
      }
      showToast(state.isNsfwMode ? "🔞 19+ 성인 씬 모드가 활성화되었습니다." : "🛡️ SAFE 모드로 전환되었습니다.");
    });
  }

  // 카테고리 탭 전환
  el.categoryTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      state.currentTab = tab.dataset.tab;
      state.currentFilter = "all";
      el.categoryTabs.forEach(t => {
        t.classList.toggle("active", t === tab);
        t.setAttribute("aria-selected", t === tab);
      });
      renderFilterButtons();
      renderCards();
    });
  });

  // 실시간 검색
  if (el.searchInput) {
    el.searchInput.addEventListener("input", (e) => {
      state.searchQuery = e.target.value;
      renderCards();
    });
  }

  // 정렬 변경
  if (el.sortSelect) {
    el.sortSelect.addEventListener("change", (e) => {
      state.sortBy = e.target.value;
      renderCards();
    });
  }

  // 모달 닫기 버튼 & 배경 클릭
  if (el.modalClose) el.modalClose.addEventListener("click", closeModal);
  if (el.modalBackdrop) el.modalBackdrop.addEventListener("click", closeModal);
  if (el.modal) {
    el.modal.addEventListener("cancel", closeModal);
  }

  // 마크다운 태그 복사 버튼들
  if (el.btnCopyInput) {
    el.btnCopyInput.addEventListener("click", () => {
      if (el.modalTagInput) copyToClipboard(el.modalTagInput.value);
    });
  }
  if (el.modalCopyTag) {
    el.modalCopyTag.addEventListener("click", () => {
      if (el.modalTagInput) copyToClipboard(el.modalTagInput.value);
    });
  }

  // 플로팅 맨 위로 버튼 스크롤 옵저버
  window.addEventListener("scroll", () => {
    if (el.backToTop) {
      el.backToTop.classList.toggle("visible", window.scrollY > 400);
    }
  });
  if (el.backToTop) {
    el.backToTop.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
}

// 초기 실행
document.addEventListener("DOMContentLoaded", () => {
  syncNsfwToggle();
  updateStats();
  renderFilterButtons();
  renderCards();
  initEvents();
});
